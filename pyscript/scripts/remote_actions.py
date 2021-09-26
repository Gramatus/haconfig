import logging
import json
import re

_LOGGER = logging.getLogger(__name__)

@service
def remote_action_trigger(trigger):
    """yaml
name: Trigger remote actions
fields:
    trigger:
        description: Trigger data from an automation
        required: true
"""
    # Convert the text version of the trigger data back to something we can load as a JSON object
    trigger = re.compile("(\".*)(')([^\"]*)(')(\")").sub('\g<1>\\\"\g<3>\\\"\g<5>',trigger)
    trigger = re.compile("(\s*)([^=\s]*?)(=)([^,>]*)").sub('\g<1>\"\g<2>\":\"\g<4>\"',trigger)
    trigger = re.compile("(<Event roku_command\[L\]:)([^>]*)(>)").sub('{\g<2>}',trigger)
    trigger = trigger.replace("'","\"")
    # Load the JSON object and then get the event data
    trigger_data = json.loads(trigger)
    event = trigger_data["event"]
    # If the event is not a keypress, we don't care
    if event["type"] != "keypress":
        return
    # See harmony_setup.md and remote_actions_state.py for the crazy mappings we are using
    remote_mapping = state.getattr("pyscript.remote_mapping")
    matches = [remote_mapping[key] for key in remote_mapping if remote_mapping[key]["roku_instance"] == event["source_name"] and remote_mapping[key]["roku_command"] == event["key"]]
    if len(matches) == 0:
        return
    action = matches[0]["action"]
    if action == None:
        _LOGGER.debug("Receieved a keypress that has no action connected to it")
        return
    if action == "Spill Alle Gromlåter":
        _LOGGER.info("TODO: Trigger playing music...")
    elif action == "NRK P1":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Tving HA med bryter":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Start HA med bryter":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Forrige på Spotify":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Play/pause Spotify":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Neste på Spotify":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Anlegg kjøkken av/på":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Anlegg bad av/på":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Anlegg stue av/på":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Anlegg soverom av/på":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    else:
        _LOGGER-warning("Received action \"" + action + "\", but no way to handle the action has been defined")
