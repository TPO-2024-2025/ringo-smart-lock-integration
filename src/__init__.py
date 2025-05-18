"""The Ringo integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .api import RingoAPI
from .const import DOMAIN
from .services import async_setup_services

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.LOCK]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the Ringo component."""
    _LOGGER.debug("Setting up Ringo integration services")
    # Set up services
    await async_setup_services(hass)
    _LOGGER.debug("Ringo integration services setup complete")
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ringo from a config entry."""
    _LOGGER.debug("Setting up Ringo config entry")
    hass.data.setdefault(DOMAIN, {})
    
    api = None
    try:
        # Initialize the API
        _LOGGER.debug("Creating RingoAPI instance")
        api = RingoAPI(
            entry.data["client"],
            entry.data["secret"]
        )
        _LOGGER.debug("RingoAPI instance created")
        
        # Authenticate
        _LOGGER.debug("Authenticating with Ringo API")
        if not await api.authenticate():
            _LOGGER.error("Failed to authenticate with Ringo API")
            raise ConfigEntryAuthFailed("Failed to authenticate with Ringo API")
        _LOGGER.debug("Authentication successful")
            
        # Test API functionality
        _LOGGER.debug("Testing API functionality - getting locks")
        locks = await api.get_locks()
        _LOGGER.info("Found %d locks", len(locks))
            
    except ConfigEntryAuthFailed:
        raise
    except Exception as e:
        _LOGGER.error("Failed to initialize Ringo API: %s", e, exc_info=True)
        if api:
            await api.close()
        raise ConfigEntryNotReady(f"Failed to initialize Ringo API: {e}")
    
    # Store the API instance
    _LOGGER.debug("Storing API instance in hass.data")
    hass.data[DOMAIN][entry.entry_id] = api
    
    # Set up platforms
    _LOGGER.debug("Setting up platforms")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("Platform setup complete")
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Ringo config entry")
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        api = hass.data[DOMAIN].pop(entry.entry_id)
        await api.close()
    
    return unload_ok
