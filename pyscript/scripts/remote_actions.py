import logging
import json
import re
import media_services

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
    shuffle_type = state.get("input_select.quick_play_shuffle_type")
    if action == None:
        _LOGGER.debug("Receieved a keypress that has no action connected to it")
        return
    if action == "Spill Alle Gromlåter":
        pyscript.play_playlist_random(playlistid="2pjB7wGkkoG9VYY8enMR5b", shuffle_type=shuffle_type)
    elif action == "Spill Kristne gromlåter":
        pyscript.play_playlist_random(playlistid="4dgE3OmDZxl5OOj5SSriWX", shuffle_type=shuffle_type)
    elif action == "Spill Classical essentials":
        pyscript.play_playlist_random(playlistid="37i9dQZF1DWWEJlAGA9gs0", shuffle_type=shuffle_type)
    elif action == "Spill Bluesfavoritter":
        pyscript.play_playlist_random(playlistid="0C2U8SFwZ3Y9bBjVa2KSMx", shuffle_type=shuffle_type)
    elif action == "Spill Night blues":
        pyscript.play_playlist_random(playlistid="2VJTrnLKqMyKZnnPXh3Ttt", shuffle_type=shuffle_type)
    elif action == "Spill Jazz Guitar":
        pyscript.play_playlist_random(playlistid="5xddIVAtLrZKtt4YGLM1SQ", shuffle_type=shuffle_type)
    elif action == "Spill 90's Country":
        pyscript.play_playlist_random(playlistid="37i9dQZF1DWVpjAJGB70vU", shuffle_type=shuffle_type)
    elif action == "Spill Visefavoritter":
        pyscript.play_playlist_random(playlistid="58TtpzdDAFoFkdTHXbx2ak", shuffle_type=shuffle_type)
    elif action == "NRK P1":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Tving HA med bryter":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Start HA med bryter":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Forrige på Spotify":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    elif action == "Play media":
        playingEntity, playState = media_services.getPlayingEntity()
        if playingEntity is not None:
            if playState == "playing":
                _LOGGER.info("Pausing " + playingEntity)
                media_player.media_pause(entity_id=playingEntity)
            elif playState == "paused":
                _LOGGER.info("Resuming " + playingEntity)
                media_player.media_play(entity_id=playingEntity)
    elif action == "Pause media":
        playingEntity, playState = media_services.getPlayingEntity()
        if playingEntity is not None:
            if playState == "playing":
                _LOGGER.info("Pausing " + playingEntity)
                media_player.media_pause(entity_id=playingEntity)
    elif action == "Stop media":
        playingEntity, playState = media_services.getPlayingEntity()
        if playingEntity is not None:
            _LOGGER.info("Stopping " + playingEntity)
            media_player.media_stop(entity_id=playingEntity)
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

@service
def getPlayingEntity():
    playingEntity, playState = media_services.getPlayingEntity()
    _LOGGER.info(playingEntity)
