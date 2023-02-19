"""Gramatus custom code."""
import logging
_LOGGER = logging.getLogger(__name__)

DOMAIN = "gramatus_fully"

def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""
    # See https://dev-docs.home-assistant.io/en/master/api/core.html#homeassistant.core.StateMachine

    # Fully instance entities
    hass.states.set("fully.nettbrett1", "on", {"friendly_name": "Fully på nettbrett 1", "icon": "mdi:tablet-dashboard", "ip": "192.168.50.60"})
    hass.states.set("fully.nettbrett2", "on", {"friendly_name": "Fully på nettbrett 2", "icon": "mdi:tablet-dashboard", "ip": "192.168.50.108"})
    hass.states.set("fully.lgg3", "on", {"friendly_name": "Fully på LG G3", "icon": "mdi:tablet-dashboard", "ip": "192.168.50.149"})

    # Return boolean to indicate that initialization was successful
    return True
