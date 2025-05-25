"""Services for the Ringo integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN
from .api import RingoAPI

_LOGGER = logging.getLogger(__name__)

# Service schemas
CREATE_KEY_SCHEMA = vol.Schema({
    vol.Required("name"): cv.string,
    vol.Required("times"): [
        vol.Schema({
            vol.Required("type"): vol.In(["date", "schedule"]),
            vol.Optional("start"): cv.positive_int,
            vol.Optional("end"): cv.positive_int,
            vol.Optional("start_time"): cv.string,
            vol.Optional("end_time"): cv.string,
            vol.Optional("monday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("tuesday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("wednesday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("thursday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("friday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("saturday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("sunday"): vol.Any(cv.boolean, vol.In([0, 1])),
        })
    ],
    vol.Required("locks"): [
        vol.Schema({
            vol.Required("lock_id"): cv.positive_int,
            vol.Required("relay_id"): cv.positive_int,
        })
    ],
    vol.Required("use_pin"): vol.Any(cv.boolean, vol.In([0, 1])),
    vol.Optional("pins"): [
        vol.Schema({
            vol.Required("email"): cv.string,
            vol.Optional("phone"): cv.string,
            vol.Required("firstname"): cv.string,
            vol.Required("lastname"): cv.string,
            vol.Required("pin"): cv.string,
        })
    ],
})

UPDATE_KEY_SCHEMA = CREATE_KEY_SCHEMA.extend({
    vol.Required("digital_key"): cv.string,
    vol.Required("name"): cv.string,
    vol.Required("times"): [
        vol.Schema({
            vol.Required("type"): vol.In(["date", "schedule"]),
            vol.Optional("start"): cv.positive_int,
            vol.Optional("end"): cv.positive_int,
            vol.Optional("start_time"): cv.string,
            vol.Optional("end_time"): cv.string,
            vol.Optional("monday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("tuesday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("wednesday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("thursday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("friday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("saturday"): vol.Any(cv.boolean, vol.In([0, 1])),
            vol.Optional("sunday"): vol.Any(cv.boolean, vol.In([0, 1])),
        })
    ],
    vol.Required("locks"): [
        vol.Schema({
            vol.Required("lock_id"): cv.positive_int,
            vol.Required("relay_id"): cv.positive_int,
        })
    ],
    vol.Required("use_pin"): vol.Any(cv.boolean, vol.In([0, 1])),
    vol.Optional("pins"): [
        vol.Schema({
            vol.Required("email"): cv.string,
            vol.Optional("phone"): cv.string,
            vol.Required("firstname"): cv.string,
            vol.Required("lastname"): cv.string,
            vol.Required("pin"): cv.string,
        })
    ],
})

DELETE_KEY_SCHEMA = vol.Schema({
    vol.Required("digital_key"): cv.string,
})

SET_DIGITAL_KEY_SCHEMA = vol.Schema({
    vol.Required("entity_id"): cv.entity_id,
    vol.Required("digital_key"): cv.string,
})

GET_KEY_STATUS_SCHEMA = vol.Schema({
    vol.Required("digital_key"): cv.string,
})

async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the services for Ringo integration."""
    _LOGGER.debug("Starting service setup")
    
    async def get_api() -> RingoAPI:
        """Get the API instance."""
        _LOGGER.debug("Getting API instance")
        if not hass.data.get(DOMAIN):
            _LOGGER.error("DOMAIN not found in hass.data")
            raise Exception("Ringo integration not initialized")
        
        _LOGGER.debug("DOMAIN found in hass.data: %s", hass.data[DOMAIN])
        
        # Get the first entry_id and its API instance
        entry_ids = list(hass.data[DOMAIN].keys())
        _LOGGER.debug("Found entry_ids: %s", entry_ids)
        
        if not entry_ids:
            _LOGGER.error("No entry_ids found in hass.data[DOMAIN]")
            raise Exception("No Ringo API instance available")
        
        api = hass.data[DOMAIN][entry_ids[0]]
        _LOGGER.debug("Retrieved API instance: %s", api)
        
        if not api:
            _LOGGER.error("API instance is None")
            raise Exception("No Ringo API instance available")
        return api
    
    async def create_key(call: ServiceCall) -> dict:
        """Create a new digital key."""
        try:
            api = await get_api()
            result = await api.create_key(
                name=call.data["name"],
                times=call.data["times"],
                locks=call.data["locks"],
                use_pin=1 if call.data["use_pin"] else 0,
                pins=call.data.get("pins")
            )
            _LOGGER.info("Created new digital key: %s", result)
            # Return a proper response dictionary
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            _LOGGER.error("Failed to create digital key: %s", e)
            return {
                "success": False,
                "error": str(e)
            }

    async def update_key(call: ServiceCall) -> dict:
        """Update an existing digital key."""
        try:
            api = await get_api()
            result = await api.update_key(
                digital_key=call.data["digital_key"],
                name=call.data["name"],
                times=call.data["times"],
                locks=call.data["locks"],
                use_pin=1 if call.data["use_pin"] else 0,
                pins=call.data.get("pins")
            )
            _LOGGER.info("Updated digital key: %s", result)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            _LOGGER.error("Failed to update digital key: %s", e)
            return {
                "success": False,
                "error": str(e)
            }

    async def delete_key(call: ServiceCall) -> dict:
        """Delete a digital key."""
        try:
            api = await get_api()
            result = await api.delete_key(call.data["digital_key"])
            _LOGGER.info("Deleted digital key: %s", result)
            return {
                "success": True,
                "result": result
            }
        except Exception as e:
            _LOGGER.error("Failed to delete digital key: %s", e)
            return {
                "success": False,
                "error": str(e)
            }

    async def set_digital_key(call: ServiceCall) -> None:
        """Set a digital key for a lock."""
        entity_id = call.data["entity_id"]
        digital_key = call.data["digital_key"]
        
        if (lock := hass.states.get(entity_id)) is None:
            _LOGGER.error("Lock entity not found: %s", entity_id)
            return

        if not lock.attributes.get("lock_id") or not lock.attributes.get("relay_id"):
            _LOGGER.error("Invalid lock entity: %s", entity_id)
            return

        try:
            api = await get_api()
            # Verify the key is valid
            key_status = await api.get_key_status(digital_key)
            if not key_status.get("valid"):
                _LOGGER.error("Invalid digital key")
                return

            # Set the key on the lock
            await hass.services.async_call(
                "lock",
                "set_digital_key",
                {"entity_id": entity_id, "digital_key": digital_key},
                blocking=True
            )
        except Exception as e:
            _LOGGER.error("Failed to set digital key: %s", e)
            raise

    async def get_locks(call: ServiceCall) -> dict:
        """Get list of all locks."""
        try:
            api = await get_api()
            locks = await api.get_locks()
            # Store the result in a sensor or notify the user
            hass.states.async_set("sensor.ringo_locks", len(locks), {
                "locks": locks,
                "friendly_name": "Ringo Locks"
            })
            _LOGGER.info("Retrieved %d locks", len(locks))
            return {
                "success": True,
                "locks": locks
            }
        except Exception as e:
            _LOGGER.error("Failed to get locks: %s", e)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_keys(call: ServiceCall) -> dict:
        """Get list of all keys."""
        try:
            api = await get_api()
            keys = await api.get_keys()
            # Store the result in a sensor or notify the user
            hass.states.async_set("sensor.ringo_keys", len(keys), {
                "keys": keys,
                "friendly_name": "Ringo Keys"
            })
            _LOGGER.info("Retrieved %d keys", len(keys))
            return {
                "success": True,
                "keys": keys
            }
        except Exception as e:
            _LOGGER.error("Failed to get keys: %s", e)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_users(call: ServiceCall) -> dict:
        """Get list of all users."""
        try:
            api = await get_api()
            users = await api.get_users()
            # Store the result in a sensor or notify the user
            hass.states.async_set("sensor.ringo_users", len(users), {
                "users": users,
                "friendly_name": "Ringo Users"
            })
            _LOGGER.info("Retrieved %d users", len(users))
            return {
                "success": True,
                "users": users
            }
        except Exception as e:
            _LOGGER.error("Failed to get users: %s", e)
            return {
                "success": False,
                "error": str(e)
            }

    async def get_key_status(call: ServiceCall) -> dict:
        """Get status of a digital key."""
        try:
            api = await get_api()
            key_status = await api.get_key_status(call.data["digital_key"])
            # Store the result in a sensor or notify the user
            hass.states.async_set("sensor.ringo_key_status", "valid" if key_status.get("valid") else "invalid", {
                "key_status": key_status,
                "friendly_name": "Ringo Key Status"
            })
            _LOGGER.info("Retrieved key status: %s", key_status)
            return {
                "success": True,
                "key_status": key_status
            }
        except Exception as e:
            _LOGGER.error("Failed to get key status: %s", e)
            return {
                "success": False,
                "error": str(e)
            }

    # Register services with explicit schemas
    try:
        _LOGGER.debug("Registering services")
        
        # Create key service
        hass.services.async_register(
            DOMAIN,
            "create_key",
            create_key,
            schema=CREATE_KEY_SCHEMA,
            supports_response=vol.All(vol.Coerce(bool), True)
        )
        _LOGGER.debug("Registered create_key service")

        # Update key service
        hass.services.async_register(
            DOMAIN,
            "update_key",
            update_key,
            schema=UPDATE_KEY_SCHEMA,
            supports_response=vol.All(vol.Coerce(bool), True)
        )
        _LOGGER.debug("Registered update_key service")

        # Delete key service
        hass.services.async_register(
            DOMAIN,
            "delete_key",
            delete_key,
            schema=DELETE_KEY_SCHEMA,
            supports_response=vol.All(vol.Coerce(bool), True)
        )
        _LOGGER.debug("Registered delete_key service")

        # Set digital key service
        hass.services.async_register(
            DOMAIN,
            "set_digital_key",
            set_digital_key,
            schema=SET_DIGITAL_KEY_SCHEMA,
            supports_response=vol.All(vol.Coerce(bool), True)
        )
        _LOGGER.debug("Registered set_digital_key service")

        # Get locks service
        hass.services.async_register(
            DOMAIN,
            "get_locks",
            get_locks,
            supports_response=vol.All(vol.Coerce(bool), True)
        )
        _LOGGER.debug("Registered get_locks service")

        # Get keys service
        hass.services.async_register(
            DOMAIN,
            "get_keys",
            get_keys,
            supports_response=vol.All(vol.Coerce(bool), True)
        )
        _LOGGER.debug("Registered get_keys service")

        # Get users service
        hass.services.async_register(
            DOMAIN,
            "get_users",
            get_users,
            supports_response=vol.All(vol.Coerce(bool), True)
        )
        _LOGGER.debug("Registered get_users service")

        # Get key status service
        hass.services.async_register(
            DOMAIN,
            "get_key_status",
            get_key_status,
            schema=GET_KEY_STATUS_SCHEMA,
            supports_response=vol.All(vol.Coerce(bool), True)
        )
        _LOGGER.debug("Registered get_key_status service")
        
        _LOGGER.debug("All services registered successfully")
    except Exception as e:
        _LOGGER.error("Failed to register services: %s", e, exc_info=True)
        raise 