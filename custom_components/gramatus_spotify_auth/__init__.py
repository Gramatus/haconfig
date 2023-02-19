from __future__ import annotations

import collections
import logging
import aiohttp
import homeassistant
# from spotipy import Spotify

import homeassistant.core as ha_core
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady

from .const import DOMAIN, SPOTIFY_SCOPES
from .helpers import get_spotify_install_status
# from .auth_controller import GramatusAuthController

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gramatus Spotify Auth from a config entry."""
    _LOGGER.debug("Config entry data from Gramatus Spotify Auth")
    _LOGGER.debug(entry.data)
    implementation = await async_get_config_entry_implementation(hass, entry)
    session = OAuth2Session(hass, entry, implementation)

    try:
        await session.async_ensure_token_valid()
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    # spotify = Spotify(auth=session.token["access_token"])
    _LOGGER.debug("New Spotify token:" + session.token["access_token"])
    _LOGGER.debug("Scopes for token: " + session.token["scope"])

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["session"] = session
    # hass.data[DOMAIN]["client"] = spotify
    _LOGGER.info("Added session to hass data for " + DOMAIN)

    if not set(session.token["scope"].split(" ")).issuperset(SPOTIFY_SCOPES):
        raise ConfigEntryAuthFailed

    return True

def setup(hass: ha_core.HomeAssistant, config: collections.OrderedDict) -> bool:

    # get spotify core integration status
    # if return false, could indicate a bad spotify integration. Race
    # condition doesn't permit us to abort setup, see #258
    if not get_spotify_install_status(hass):
        _LOGGER.debug("Spotify integration was not found, please verify integration is functional. Could result in python error...")

    """Setup the Gramatus Spotify Auth service."""

    # auth_controller = GramatusAuthController(hass)

    # if DOMAIN not in hass.data:
    #     hass.data[DOMAIN] = {}
    # hass.data[DOMAIN]["controller"] = auth_controller

    async def reset_token(call: ha_core.ServiceCall):
        """service called."""
        _LOGGER.info("Reloading token if needed")
        if not hass.data[DOMAIN]["session"].valid_token:
            _LOGGER.info("Reloading token")
            await hass.data[DOMAIN]["session"].async_ensure_token_valid()
        else:
            _LOGGER.info("Token is still valid")
        _LOGGER.info("New expiry for token: " + str(hass.data[DOMAIN]["session"].token["expires_at"]) + ", token: " + hass.data[DOMAIN]["session"].token["access_token"])

    # async def get_token(call: ha_core.ServiceCall):
    #     """service called."""
    #     _LOGGER.info("Getting token")
    #     token_instance = auth_controller.get_token_instance()
    #     return token_instance["access_token"]

    hass.services.register(DOMAIN, "reset_token", reset_token)

    return True
