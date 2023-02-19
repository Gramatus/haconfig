from __future__ import annotations

import collections
import logging
import random
import time
from asyncio import run_coroutine_threadsafe
from requests import TooManyRedirects
from collections import OrderedDict
from datetime import datetime
import homeassistant.core as ha_core

import pychromecast
import spotipy
from homeassistant.components.cast.helpers import ChromeCastZeroconf
from homeassistant.exceptions import HomeAssistantError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class SpotifyToken:
    """Represents a spotify token for an account."""

    hass = None
    session = None

    def __init__(self, hass: ha_core.HomeAssistant) -> None:
        self.hass = hass
        _LOGGER.info("Reading session from hass data")
        self.session = hass.data[DOMAIN]["session"]

    def ensure_token_valid(self) -> bool:
        if not self.session.valid_token:
            run_coroutine_threadsafe(
                self.session.async_ensure_token_valid(), self.hass.loop
            ).result()

    @property
    def access_token(self) -> str:
        self.ensure_token_valid()
        _LOGGER.info("expires: %s time: %s", self.session.token["expires_at"], time.time())
        return self.session.token["access_token"]

    @property
    def expires(self) -> str:
        return self.session.token["expires_at"] - int(time.time())


class GramatusAuthController:

    spotifyTokenInstance = None
    hass = None

    def __init__(self, hass: ha_core.HomeAssistant) -> None:
        self.hass = hass

    def get_token_instance(self) -> any:
        """Get token instance"""
        _LOGGER.debug("setting up token instance")
        if self.spotifyTokenInstance is None:
            self.spotifyTokenInstance = SpotifyToken(self.hass)
        return self.spotifyTokenInstance

    def get_spotify_client(self) -> spotipy.Spotify:
        return spotipy.Spotify(auth=self.get_token_instance().access_token)
