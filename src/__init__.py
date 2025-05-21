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
    _LOGGER.debug("Setting up Ringo component")
    hass.data.setdefault(DOMAIN, {})
    _LOGGER.debug("Initialized DOMAIN in hass.data: %s", hass.data[DOMAIN])
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ringo from a config entry."""
    _LOGGER.debug("Setting up Ringo config entry")
    
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
            if api:
                await api.close()
            raise ConfigEntryAuthFailed("Failed to authenticate with Ringo API")
        _LOGGER.debug("Authentication successful")
            
        # Test API functionality
        _LOGGER.debug("Testing API functionality - getting locks")
        locks = await api.get_locks()
        _LOGGER.info("Found %d locks", len(locks))
            
    except ConfigEntryAuthFailed:
        if api:
            await api.close()
        raise
    except Exception as e:
        _LOGGER.error("Failed to initialize Ringo API: %s", e, exc_info=True)
        if api:
            await api.close()
        raise ConfigEntryNotReady(f"Failed to initialize Ringo API: {e}")
    
    # Store the API instance
    _LOGGER.debug("Storing API instance in hass.data")
    hass.data[DOMAIN][entry.entry_id] = api
    _LOGGER.debug("API instance stored with entry_id: %s", entry.entry_id)
    
    # Set up platforms first
    _LOGGER.debug("Setting up platforms")
    try:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        _LOGGER.debug("Platform setup complete")
    except Exception as e:
        _LOGGER.error("Failed to set up platforms: %s", e, exc_info=True)
        raise ConfigEntryNotReady(f"Failed to set up platforms: {e}")
    
    # Set up services after platforms are initialized
    try:
        _LOGGER.debug("Setting up services")
        await async_setup_services(hass)
        _LOGGER.debug("Services setup complete")
    except Exception as e:
        _LOGGER.error("Failed to set up services: %s", e, exc_info=True)
        # Don't fail the setup if services fail
        # Just log the error and continue
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Ringo config entry")
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        api = hass.data[DOMAIN].pop(entry.entry_id)
        await api.close()
    
    return unload_ok
