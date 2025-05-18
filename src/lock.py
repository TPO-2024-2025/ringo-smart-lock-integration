"""Platform for lock integration."""
from __future__ import annotations

import logging
from typing import Any
import asyncio

from homeassistant.components.lock import LockEntity, LockEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import RingoAPI, RingoLock
from .const import DOMAIN, DEFAULT_AUTO_LOCK_TIME

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Ringo Lock from a config entry."""
    api: RingoAPI = hass.data[DOMAIN][entry.entry_id]
    
    # Get locks from API
    locks = await api.get_locks()
    #_LOGGER.debug("Found %d locks: %s", len(locks), locks)
    
    entities = []
    for lock_data in locks:
        lock = RingoLock(api, lock_data["lock_id"], lock_data["relay_id"])
        entities.append(RingoLockEntity(lock, entry))
    
    async_add_entities(entities)

class RingoLockEntity(LockEntity):
    """Representation of a Ringo Lock."""

    _attr_has_entity_name = True
    _attr_supported_features = LockEntityFeature(0)

    def __init__(self, lock: RingoLock, entry: ConfigEntry) -> None:
        """Initialize the lock."""
        self._lock = lock
        self._attr_unique_id = f"{lock._lock_id}_{lock._relay_id}"
        self._attr_name = None
        self._attr_is_locked = True
        self._auto_lock_timer = None
        self._auto_lock_time = DEFAULT_AUTO_LOCK_TIME

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        return {
            "auto_lock_time": self._auto_lock_time,
        }

    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        self._attr_name = await self._lock.get_name()
        self.async_write_ha_state()

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the lock."""
        #_LOGGER.debug("Starting unlock process for %s", self.name)
        
        # Get a digital key first
        keys_response = await self._lock._api.get_keys()
        keys = keys_response.get("data", [])
        
        if not keys:
            _LOGGER.error("No digital keys available")
            return
            
        # Find a valid key for this specific lock and relay
        valid_key = None
        for key in keys:
            if key.get("is_valid") == 1 and key.get("is_ended") == 0:
                for lock in key.get("locks", []):
                    if (lock.get("lock_id") == self._lock._lock_id and 
                        lock.get("relay_id") == self._lock._relay_id):
                        valid_key = key
                        break
                if valid_key:
                    break
                    
        if not valid_key:
            _LOGGER.error("No valid key found for lock_id=%s, relay_id=%s", 
                         self._lock._lock_id, self._lock._relay_id)
            return
            
        # Use the valid key
        digital_key = valid_key["digital_key"]
        
        # Make the API call using the lock's open_door method
        result = await self._lock.open_door(digital_key)
        
        # Check if the unlock was successful
        if result and isinstance(result, dict) and result.get("status") == 200:
            #_LOGGER.debug("Unlock successful")
            self._attr_is_locked = False
            self.async_write_ha_state()
            
            # Start auto-lock timer
            if self._auto_lock_timer:
                self._auto_lock_timer.cancel()
            
            self._auto_lock_timer = self.hass.loop.call_later(
                self._auto_lock_time,
                self._handle_auto_lock
            )
        else:
            _LOGGER.error("Unlock failed: %s", result)

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the lock."""
        #_LOGGER.debug("Locking %s", self.name)
        self._attr_is_locked = True
        self.async_write_ha_state()
        
        if self._auto_lock_timer:
            self._auto_lock_timer.cancel()
            self._auto_lock_timer = None

    @callback
    def _handle_auto_lock(self) -> None:
        """Handle the auto-lock timer callback."""
        #_LOGGER.debug("Auto-lock triggered for %s", self.name)
        self._attr_is_locked = True
        self.async_write_ha_state()
        self._auto_lock_timer = None
