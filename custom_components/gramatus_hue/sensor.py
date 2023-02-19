"""Support for saving certain  Philips Hue scenes as entities (NOT USED!)."""
from homeassistant.helpers.entity import Entity

import logging
_LOGGER = logging.getLogger(__name__)

def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the sensor platform."""
    _LOGGER.debug("Setting up gramatus platform")
    #add_entities([HueScene("bf8cb54b-ee8f-4296-aecb-5e079c3419ca","1. Vanlig lys")])

class HueScene(Entity):
    """Representation of a Hue scene."""

    def __init__(self, scene_id, scene_name):
        """Initialize the sensor."""
        _LOGGER.debug("Creating entity with id: %s", scene_id)
        self._state = None
        self._id = scene_id
        self._name = scene_name

    @property
    def unique_id(self):
        """Return the ID of this Hue sensor."""
        return self._id
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state
