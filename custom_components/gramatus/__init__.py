"""Gramatus custom code."""
import logging
_LOGGER = logging.getLogger(__name__)

GRAMATUS_DOMAIN = "gramatus"

def setup(hass, config):
    """Set up is called when Home Assistant is loading our component."""
    # See https://dev-docs.home-assistant.io/en/master/api/core.html#homeassistant.core.StateMachine

    # Hue Scene entities
    hass.states.set("huescenes.vanliglys", "off", {"friendly_name": "Vanlig lys", "scene_name": "1. Vanlig lys", "icon": "hass:lightbulb"})
    hass.states.set("huescenes.dagslys", "off", {"friendly_name": "Dagslys", "scene_name": "2. Dagslys", "icon": "hass:lightbulb"})
    hass.states.set("huescenes.koselys", "off", {"friendly_name": "Kveldslys", "scene_name": "3. Koselys", "icon": "hass:lightbulb"})
    hass.states.set("huescenes.snartkveld", "off", {"friendly_name": "Snart kveld", "scene_name": "4. Snart kveld", "icon": "hass:lightbulb"})
    hass.states.set("huescenes.arktisknordlys", "off", {"friendly_name": "Arktisk nordlys", "scene_name": "Arktisk nordlys", "icon": "hass:lightbulb"})
    # Roomtoggle entities
    hass.states.set("roomtoggles.badet", "off", {"friendly_name": "Bad", 'rooms': ['light.bad'], "icon": "mdi:home-lightbulb", "is_on": False})
    hass.states.set("roomtoggles.stua", "off", {"friendly_name": "Stue", 'rooms': ['light.stue'], "icon": "mdi:home-lightbulb"})
    hass.states.set("roomtoggles.kjokken", "off", {"friendly_name": "Kjøkken", 'rooms': ['light.kjokken'], "icon": "mdi:home-lightbulb"})
    hass.states.set("roomtoggles.kontor_gang", "off", {"friendly_name": "Gang og kontor", 'rooms': ['light.kontor', 'light.gang_nede'], "icon": "mdi:home-lightbulb"})
    # Fully instance entities
    hass.states.set("fully.nettbrett1", "on", {"friendly_name": "Fully på nettbrett 1", "icon": "mdi:tablet-dashboard", "ip": "192.168.50.60"})
    hass.states.set("fully.nettbrett2", "on", {"friendly_name": "Fully på nettbrett 2", "icon": "mdi:tablet-dashboard", "ip": "192.168.50.108"})
    hass.states.set("fully.lgg3", "on", {"friendly_name": "Fully på LG G3", "icon": "mdi:tablet-dashboard", "ip": "192.168.50.149"})

    # Transition entities
    _LOGGER.info(hass.states.get("hue_transitions.Kveldslys"))
    if hass.states.get("hue_transitions.Kveldslys") == None:
        hass.states.set("hue_transitions.Kveldslys","on",{
            "Scenes": [
                {
                    "index": 1,
                    "name": "FadeKveldslys !start",
                    "id": "KMVf61DE0jXA9b4",
                    "timeinseconds": (60*60)+(0)
                },
                {
                    "index": 2,
                    "name": "FadeKveldslys 1t0min",
                    "id": "fVqEsKelwr0BLv3",
                    "timeinseconds": (60*60)+(0)
                },
                {
                    "index": 4,
                    "name": "FadeKveldslys 2t30min",
                    "id": "uofrddCzHp-x0vF",
                    "timeinseconds": (30*60)+(0)
                },
                {
                    "index": 3,
                    "name": "FadeKveldslys 2t0min",
                    "id": "rtH7xu7qvsv3PPv",
                    "timeinseconds": (30*60)+(0)
                },
                {
                    "index": 5,
                    "name": "FadeKveldslys 3t0min",
                    "id": "iVcGM9UbJtc34TF",
                    "timeinseconds": (30*60)+(0)
                }
            ],
            "Rooms": [
                "light.bad",
                "light.kontor"
            ]
        })

    def handle_test():
        """Handle the test."""
        _LOGGER.debug("Gramatus testing")

    #hass.services.register(GRAMATUS_DOMAIN, "gramatus_test", handle_test)

    # Return boolean to indicate that initialization was successful
    return True
