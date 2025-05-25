"""API for interacting with Ringo Lock."""
from __future__ import annotations

import aiohttp
import logging
import asyncio
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

_LOGGER = logging.getLogger(__name__)

# Timeout settings
TIMEOUT = aiohttp.ClientTimeout(total=10)  # 10 seconds total timeout

class RingoLock:
    """Class to represent a Ringo Lock."""
    BASE_URL = "https://dev.ringodoor.com/api"

    def __init__(self, api: "RingoAPI", lock_id: str, relay_id: str):
        """Initialize the lock."""
        self._api = api
        self._lock_id = lock_id
        self._relay_id = relay_id
        self._name = None

    async def get_name(self) -> Optional[str]:
        """Get the name of the lock."""
        if not self._name:
            locks = await self._api.get_locks()
            for lock in locks:
                if lock["lock_id"] == self._lock_id and lock["relay_id"] == self._relay_id:
                    self._name = lock.get("name")
                    break
        return self._name

    async def open_door(self, digital_key: str) -> Dict[str, Any]:
        """Open the lock."""
        return await self._api.open_door(self._lock_id, self._relay_id, digital_key)

    async def open_door_by_pin(self, pin: str, open: bool = True) -> Dict[str, Any]:
        """Open the lock using a PIN."""
        return await self._api.open_door_by_pin(self._lock_id, self._relay_id, pin, open)

class RingoAPI:
    """Class to handle the Ringo API."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize the API."""
        _LOGGER.debug("Initializing RingoAPI")
        self._client = username  # This is actually the API client ID
        self._secret = password  # This is actually the API secret
        self._session = None
        self._token = None
        self._token_expiry = None
        self._lock = asyncio.Lock()  # Add lock for token refresh

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create a session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=TIMEOUT)
        return self._session

    async def authenticate(self) -> bool:
        """Authenticate with the API."""
        _LOGGER.debug("Authenticating with Ringo API")
        try:
            session = await self._get_session()
            headers = {
                "Ringo-Api-Client": self._client,
                "Ringo-Api-Secret": self._secret
            }
            _LOGGER.debug("Making authentication request with client: %s", self._client)
            async with session.get(
                "https://dev.ringodoor.com/api/token",
                headers=headers,
                timeout=TIMEOUT
            ) as response:
                response_text = await response.text()
                _LOGGER.debug("Authentication response status: %s, body: %s", response.status, response_text)
                
                if response.status == 200:
                    try:
                        data = await response.json()
                        _LOGGER.debug("Authentication response data: %s", data)
                        
                        # Extract token from the nested response structure
                        token = data.get("data")
                        if not token:
                            _LOGGER.error("No token received in response. Response data: %s", data)
                            return False
                            
                        self._token = token
                        self._token_expiry = datetime.now() + timedelta(hours=1)
                        _LOGGER.debug("Authentication successful, token received")
                        return True
                    except ValueError as e:
                        _LOGGER.error("Failed to parse authentication response as JSON: %s", e)
                        return False
                elif response.status == 401:
                    _LOGGER.error("Authentication failed: Invalid credentials")
                    return False
                else:
                    _LOGGER.error("Authentication failed with status %s: %s", response.status, response_text)
                    return False
        except asyncio.TimeoutError:
            _LOGGER.error("Authentication timeout")
            return False
        except Exception as e:
            _LOGGER.error("Authentication failed: %s", str(e), exc_info=True)
            return False

    async def _ensure_token(self) -> None:
        """Ensure we have a valid token."""
        async with self._lock:  # Use lock to prevent multiple simultaneous token refreshes
            if not self._token or not self._token_expiry or datetime.now() >= self._token_expiry:
                _LOGGER.debug("Token expired or missing, reauthenticating")
                if not await self.authenticate():
                    raise Exception("Failed to authenticate")
                _LOGGER.debug("Token refreshed successfully")

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        """Make a request to the API."""
        #_LOGGER.debug("Making %s request to %s", method, endpoint)
        retry_count = 0
        max_retries = 2
        
        while retry_count <= max_retries:
            try:
                await self._ensure_token()
                
                session = await self._get_session()
                headers = {
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json"
                }
                #_LOGGER.debug("Making request with token: %s...", self._token[:10] if self._token else "None")
                
                async with session.request(
                    method,
                    f"https://dev.ringodoor.com/api/{endpoint}",
                    headers=headers,
                    timeout=TIMEOUT,
                    **kwargs
                ) as response:
                    if response.status == 401 and retry_count < max_retries:
                        _LOGGER.debug("Token expired, attempting to reauthenticate (attempt %d)", retry_count + 1)
                        self._token = None  # Force token refresh
                        retry_count += 1
                        continue
                    response.raise_for_status()
                    return await response.json()
            except asyncio.TimeoutError:
                _LOGGER.error("Request timeout for %s %s", method, endpoint)
                raise
            except Exception as e:
                if retry_count < max_retries:
                    _LOGGER.debug("Request failed, retrying (attempt %d): %s", retry_count + 1, e)
                    retry_count += 1
                    continue
                _LOGGER.error("Request failed for %s %s after %d retries: %s", 
                            method, endpoint, max_retries, e)
                raise
        
        raise Exception(f"Failed to complete request after {max_retries} retries")

    async def get_locks(self) -> List[Dict[str, Any]]:
        """Get all locks."""
        response = await self._request("GET", "locks")
       # _LOGGER.debug("Raw locks response: %s", response)
        
        # Extract locks from the nested response structure
        locks = response.get("data", [])
        if not locks:
            _LOGGER.error("No locks found in response: %s", response)
            return []
            
       # _LOGGER.debug("Found %d locks: %s", len(locks), locks)
        return locks

    async def get_keys(self) -> List[Dict[str, Any]]:
        """Get all keys."""
        return await self._request("GET", "key-list")

    async def get_users(self) -> List[Dict[str, Any]]:
        """Get all users."""
        response = await self._request("GET", "users")
        # Extract users from the nested response structure
        users = response.get("data", [])
        if not users:
            _LOGGER.error("No users found in response: %s", response)
            return []
        return users

    async def get_key_status(self, digital_key: str) -> Dict[str, Any]:
        """Get full info about a single Digital key."""
        return await self._request("GET", "key", params={"digital_key": digital_key})

    async def open_door(self, lock_id: int, relay_id: int, digital_key: str) -> Dict[str, Any]:
        """Open a door."""
        return await self._request(
            "POST",
            "open-door",
            json={
                "lock_id": lock_id,
                "relay_id": relay_id,
                "digital_key": digital_key
            }
        )

    async def open_door_by_pin(self, lock_id: int, relay_id: int, pin: str, open: bool = True) -> Dict[str, Any]:
        """Open a door using a PIN."""
        return await self._request(
            "POST",
            "open-door-by-pin",
            json={
                "lock_id": lock_id,
                "relay_id": relay_id,
                "pin": pin,
                "open": open
            }
        )

    async def create_key(
        self,
        name: str,
        times: List[Dict[str, Any]],
        locks: List[Dict[str, int]],
        use_pin: int,
        pins: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Create a new key."""
        return await self._request(
            "POST",
            "key",
            json={
                "name": name,
                "times": times,
                "locks": locks,
                "use_pin": use_pin,
                "pins": pins or []
            }
        )

    async def update_key(
        self,
        digital_key: str,
        name: str,
        times: List[Dict[str, Any]],
        locks: List[Dict[str, int]],
        use_pin: int,
        pins: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Update a key."""
        return await self._request(
            "PUT",
            "key",
            json={
                "digital_key": digital_key,
                "name": name,
                "times": times,
                "locks": locks,
                "use_pin": use_pin,
                "pins": pins or []
            }
        )

    async def delete_key(self, digital_key: str) -> Dict[str, Any]:
        """Delete a key."""
        return await self._request(
            "DELETE",
            "key",
            json={"digital_key": digital_key}
        )

    async def close(self) -> None:
        """Close the session."""
        if self._session and not self._session.closed:
            try:
                await self._session.close()
            except Exception as e:
                _LOGGER.error("Error closing session: %s", e)
            finally:
                self._session = None 