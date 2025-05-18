"""Services for the Ringo integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import DOMAIN

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
    
    async def create_key(call: ServiceCall) -> None:
        """Create a new digital key."""
        # Get the first API instance (assuming single config entry)
        api = next(iter(hass.data[DOMAIN].values()))
        try:
            result = await api.create_key(
                name=call.data["name"],
                times=call.data["times"],
                locks=call.data["locks"],
                use_pin=1 if call.data["use_pin"] else 0,
                pins=call.data.get("pins")
            )
            _LOGGER.info("Created new digital key: %s", result)
        except Exception as e:
            _LOGGER.error("Failed to create digital key: %s", e)

    async def update_key(call: ServiceCall) -> None:
        """Update an existing digital key."""
        # Get the first API instance (assuming single config entry)
        api = next(iter(hass.data[DOMAIN].values()))
        try:
            result = await api.update_key(
                digital_key=call.data["digital_key"],
                name=call.data["name"],
                times=call.data["times"],
                locks=call.data["locks"],
                use_pin=1 if call.data["use_pin"] else 0,
                pins=call.data.get("pins")
            )
            _LOGGER.info("Updated digital key: %s", result)
        except Exception as e:
            _LOGGER.error("Failed to update digital key: %s", e)

    async def delete_key(call: ServiceCall) -> None:
        """Delete a digital key."""
        # Get the first API instance (assuming single config entry)
        api = next(iter(hass.data[DOMAIN].values()))
        try:
            result = await api.delete_key(call.data["digital_key"])
            _LOGGER.info("Deleted digital key: %s", result)
        except Exception as e:
            _LOGGER.error("Failed to delete digital key: %s", e)

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
            # Get the first API instance (assuming single config entry)
            api = next(iter(hass.data[DOMAIN].values()))
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

    async def get_locks(call: ServiceCall) -> None:
        """Get list of all locks."""
        # Get the first API instance (assuming single config entry)
        api = next(iter(hass.data[DOMAIN].values()))
        try:
            locks = await api.get_locks()
            # Store the result in a sensor or notify the user
            hass.states.async_set("sensor.ringo_locks", len(locks), {
                "locks": locks,
                "friendly_name": "Ringo Locks"
            })
            _LOGGER.info("Retrieved %d locks", len(locks))
        except Exception as e:
            _LOGGER.error("Failed to get locks: %s", e)

    async def get_keys(call: ServiceCall) -> None:
        """Get list of all keys."""
        # Get the first API instance (assuming single config entry)
        api = next(iter(hass.data[DOMAIN].values()))
        try:
            keys = await api.get_keys()
            # Store the result in a sensor or notify the user
            hass.states.async_set("sensor.ringo_keys", len(keys), {
                "keys": keys,
                "friendly_name": "Ringo Keys"
            })
            _LOGGER.info("Retrieved %d keys", len(keys))
        except Exception as e:
            _LOGGER.error("Failed to get keys: %s", e)

    async def get_users(call: ServiceCall) -> None:
        """Get list of all users."""
        # Get the first API instance (assuming single config entry)
        api = next(iter(hass.data[DOMAIN].values()))
        try:
            users = await api.get_users()
            # Store the result in a sensor or notify the user
            hass.states.async_set("sensor.ringo_users", len(users), {
                "users": users,
                "friendly_name": "Ringo Users"
            })
            _LOGGER.info("Retrieved %d users", len(users))
        except Exception as e:
            _LOGGER.error("Failed to get users: %s", e)

    async def get_key_status(call: ServiceCall) -> None:
        """Get status of a digital key."""
        # Get the first API instance (assuming single config entry)
        api = next(iter(hass.data[DOMAIN].values()))
        try:
            key_status = await api.get_key_status(call.data["digital_key"])
            # Store the result in a sensor or notify the user
            hass.states.async_set("sensor.ringo_key_status", "valid" if key_status.get("valid") else "invalid", {
                "key_status": key_status,
                "friendly_name": "Ringo Key Status"
            })
            _LOGGER.info("Retrieved key status: %s", key_status)
        except Exception as e:
            _LOGGER.error("Failed to get key status: %s", e)

    # Register services
    hass.services.async_register(
        "ringo",
        "create_key",
        create_key,
        schema=CREATE_KEY_SCHEMA
    )

    hass.services.async_register(
        "ringo",
        "update_key",
        update_key,
        schema=UPDATE_KEY_SCHEMA
    )

    hass.services.async_register(
        "ringo",
        "delete_key",
        delete_key,
        schema=DELETE_KEY_SCHEMA,
    )

    hass.services.async_register(
        "ringo",
        "set_digital_key",
        set_digital_key,
        schema=SET_DIGITAL_KEY_SCHEMA
    )

    hass.services.async_register(
        "ringo",
        "get_locks",
        get_locks
    )

    hass.services.async_register(
        "ringo",
        "get_keys",
        get_keys
    )

    hass.services.async_register(
        "ringo",
        "get_users",
        get_users
    )

    hass.services.async_register(
        "ringo",
        "get_key_status",
        get_key_status,
        schema=GET_KEY_STATUS_SCHEMA
    ) 