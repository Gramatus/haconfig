import logging
import json
import re
import media_services
import spotify_services
import asyncio
import datetime

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
    _LOGGER.info(trigger)
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
        _LOGGER.info("Starting NRK P1")
        extradata = {
            "metadata": {
                "metadataType": 0,
                "title": "NRK P1",
                "images": [{ "url": "https://play-lh.googleusercontent.com/U5LxZ1tqqcOoQk6igbKN6Xu6iFxP7jbsUq5pryhxqfeMNs1NIkF6UsFJS-FbdPOlEg=s180-rw" }]
            }
        }
        media_player.play_media(entity_id="media_player.godehol", media_content_id="https://lyd.nrk.no/nrk_radio_p1_sorlandet_mp3_h", media_content_type="audio/mp3", extra=extradata)
    elif action == "Tving HA med bryter":
        _LOGGER.info("Turning off KjøkkenNest, then waiting 5 seconds")
        media_player.turn_off(entity_id="media_player.kjokkennest")
        await asyncio.sleep(5)
        _LOGGER.info("Casting Home Assistant to KjøkkenNest")
        cast.show_lovelace_view(entity_id="media_player.kjokkennest", dashboard_path="kjokken-ga", view_path="default_view")
    elif action == "Start HA med bryter":
        _LOGGER.info("Casting Home Assistant to KjøkkenNest")
        cast.show_lovelace_view(entity_id="media_player.kjokkennest", dashboard_path="kjokken-ga", view_path="default_view")
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
    elif action == "Forrige på Spotify":
        playingEntity, playState = media_services.getPlayingEntity()
        if playingEntity is not None:
            _LOGGER.info("Going back to previus track on " + playingEntity)
            media_player.media_previous_track(entity_id=playingEntity)
    elif action == "Neste på Spotify":
        spotify_playing = spotify_services.skip_track()
        if not spotify_playing:
            playingEntity, playState = media_services.getPlayingEntity()
            if playingEntity is not None:
                _LOGGER.info("Skipping to next track on " + playingEntity)
                media_player.media_next_track(entity_id=playingEntity)
    elif action == "Anlegg kjøkken av/på":
        _LOGGER.info("Turning on/off Anlegg kjøkken")
        remote.send_command(entity_id="remote.harmony_hub_gangen", device="JVC Mini System", command="PowerToggle")
    elif action == "Anlegg bad av/på":
        device_on = state.get("input_boolean.status_anlegg_bad") == "on"
        if device_on:
            _LOGGER.info("Turning off Anlegg bad")
            remote.send_command(entity_id="remote.harmony_hub_gangen", device="Yamaha AV Receiver", command="PowerOff")
            input_boolean.turn_off(entity_id="input_boolean.status_anlegg_bad")
        else:
            _LOGGER.info("Turning on Anlegg bad")
            remote.send_command(entity_id="remote.harmony_hub_gangen", device="Yamaha AV Receiver", command="PowerOn")
            input_boolean.turn_on(entity_id="input_boolean.status_anlegg_bad")
    elif action == "Anlegg stue av/på":
        if (datetime.datetime.now().astimezone() - state.get("light.hue_smart_plug_1.last_changed")).total_seconds() < 5:
            _LOGGER.info("Anlegg stue changed state in the last 5 seconds, will not do anything")
            return
        device_on = state.get("light.hue_smart_plug_1") == "on"
        if device_on:
            _LOGGER.info("Turning off Anlegg stue")
            remote.send_command(entity_id="remote.harmony_hub_stua", device="Yamaha AV Receiver", command="PowerOff")
            light.turn_off(entity_id="light.hue_smart_plug_1")
            pyscript.turn_off_hdmi_switch()
        else:
            _LOGGER.info("Turning on Anlegg stue")
            remote.send_command(entity_id="remote.harmony_hub_stua", device="Yamaha AV Receiver", command="PowerON")
            light.turn_on(entity_id="light.hue_smart_plug_1")
            pyscript.set_hdmi_output(output="Dantax TV")
    elif action == "Anlegg soverom av/på":
        _LOGGER.info("TODO: Trigger action \"" + action + "\"...")
    else:
        _LOGGER-warning("Received action \"" + action + "\", but no way to handle the action has been defined")

@service
def getPlayingEntity():
    playingEntity, playState = media_services.getPlayingEntity()
    _LOGGER.info(playingEntity)

@service
def set_hdmi_output(output):
    """yaml
name: Set HDMI Output
description: Set correct output on the HDMI box
fields:
    output:
        description: Output to activate
        required: true
        example: Projector
        selector:
            select:
                options:
                    - "Projector"
                    - "Dantax TV"
"""
    turn_off_hdmi_switch()
    wait_time = 0.2
    await asyncio.sleep(wait_time)
    # Turn on correct device
    cmd = "InputOut1=In2"
    if output == "Projector":
        cmd = "InputOut1=In2"
    if output == "Dantax TV":
        cmd = "InputOut2=In2"
    remote.send_command(entity_id="remote.harmony_hub_stua", device="HDMI Switch", command=cmd)

@service
def turn_off_hdmi_switch():
    """yaml
name: Turn off HDMI Switch
"""
    wait_time = 0.2
    # Power Toggle always turns ON if Out1 is off, but turns *everything* OFF is Out1 is on...
    # This command is only used to force power ON for out1
    remote.send_command(entity_id="remote.harmony_hub_stua", device="HDMI Switch", command="InputOut1=In1")
    await asyncio.sleep(wait_time)
    # Make sure everything is off
    remote.send_command(entity_id="remote.harmony_hub_stua", device="HDMI Switch", command="Power Toggle")
