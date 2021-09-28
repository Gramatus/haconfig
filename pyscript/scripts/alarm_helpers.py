import logging
import asyncio
import datetime
import spotify_services

_LOGGER = logging.getLogger(__name__)

playlist_mapping = {
    "Våkneliste": "3FVKcokzHla6424Cj74LzL",
    "Lovsang": "0dUdJSf4v753IJwv8xDThH",
    "Alle gromlåter": "2pjB7wGkkoG9VYY8enMR5b",
    "90's Country": "37i9dQZF1DWVpjAJGB70vU"
}

@service
async def volume_increase(fadein_seconds, device="media_player.spotify_gramatus", initial_volume = None, final_volume = 1.0):
    """yaml
name: Increase volume
description: Increase volume gradually
fields:
    fadein_seconds:
        description: Number of seconds for the fadein
        required: true
        example: 60
        selector:
            number:
                min: 30
                max: 120
                mode: box
    device:
        description: Media player to run fadein against
        required: false
        example: media_player.spotify_gramatus
        selector:
            entity:
                domain: media_player
    initial_volume:
        description: Volume to start at
        required: false
        example: 0.0
        selector:
            number:
                min: 0
                max: 1
                step: 0.01
                mode: box
    final_volume:
        description: Volume to end at
        required: false
        example: 1.0
        selector:
            number:
                min: 0
                max: 1
                step: 0.01
                mode: box
"""
    if initial_volume == None:
        attributes = state.getattr(device)
        if "volume_level" in attributes:
            initial_volume = round(attributes["volume_level"], 2)
            _LOGGER.info("No initial volume supplied, will use current volume: " + str(initial_volume))
        else:
            initial_volume = 0.0
            _LOGGER.warning("No initial volume supplied, no current volume found, will use 0.0. Attributes found:")
            _LOGGER.info(attributes)
    volume_level = initial_volume
    volume_increase = final_volume - initial_volume
    fadein_steps = abs(int(100 * volume_increase))
    wait_seconds = fadein_seconds / fadein_steps
    _LOGGER.info("Will change volume from " + str(initial_volume) + " to " + str(final_volume) + " in "+str(fadein_seconds)+" seconds. Time for each step: " + str(round(wait_seconds, 2)))
    increase = final_volume > initial_volume
    increase_step = volume_increase / fadein_steps
    media_player.volume_set(entity_id=device, volume_level=volume_level)
    for x in range(fadein_steps):
        volume_level=round(volume_level+increase_step, 2)
        if increase and volume_level > final_volume:
            volume_level=final_volume
            _LOGGER.info("Reached max volume")
        elif not increase and volume_level < final_volume:
            volume_level=final_volume
            _LOGGER.info("Reached min volume")
        media_player.volume_set(entity_id=device, volume_level=volume_level)
        await asyncio.sleep(wait_seconds)
    _LOGGER.info("Done, final volume is: " + str(volume_level))

# Alternate script:
# service: remote.send_command
# target:
#   entity_id: remote.harmony_hub_soverom
# data:
#   command: PowerToggle
#   device: 75674802

@service
async def good_night():
    """yaml
name: Good night routine
description: Set HVAC night settings, lower blinds and turn off lights after one minute
"""
    _LOGGER.info("Turning on Fully screen and bringing Fully to the foreground")
    wakeup_fully()
    _LOGGER.info("Turning down covers")
    cover.close_cover(entity_id="cover.tradfri_blind")
    _LOGGER.info("Wait 16 seconds for cover to close")
    await asyncio.sleep(16)
    _LOGGER.info("Turning on lights temporarily, with a 10 second transition")
    light.turn_on(entity_id="light.soverom",transition=10,kelvin=2000,brightness=30)
    _LOGGER.info("Setting HVAC settings")
    melcloud.set_vane_vertical(entity_id="climate.soverom",position="auto")
    climate.set_temperature(entity_id="climate.soverom",temperature=17.5)
    turnoff_time = str(datetime.timedelta(seconds=int((datetime.datetime.now() - datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())+5*60))
    turnon_time = str(datetime.timedelta(seconds=state.getattr("input_datetime.vekking")["timestamp"]-5*60))
    _LOGGER.info("Telling Fully to turn off WiFi between " + turnoff_time + " and " + turnon_time)
    pyscript.fully_set_wifi_off_between(timeoff=turnoff_time, timeon=turnon_time, device="fully.nettbrett1")
    _LOGGER.info("Wait 120 seconds before turning starting to turn the lights off")
    await asyncio.sleep(120)
    _LOGGER.info("Turning off lights with a 60 second transition")
    light.turn_off(entity_id="light.soverom",transition=60)
    _LOGGER.info("Turning off Fully screen")
    pyscript.fully_turn_off_screen(device="fully.nettbrett1")
    _LOGGER.info("Done")

@service
def test_wifi_off():
    #now = datetime.datetime.now()
    #midnight = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    turnoff_time = str(datetime.timedelta(seconds=int((datetime.datetime.now() - datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())+5*60))
    turnon_time = str(datetime.timedelta(seconds=state.getattr("input_datetime.vekking")["timestamp"]-5*60))
    pyscript.fully_set_wifi_off_between(timeoff=turnoff_time, timeon=turnon_time, device="fully.nettbrett1")
    _LOGGER.info(turnoff_time)
    _LOGGER.info(turnon_time)

@service
async def start_morning():
    """yaml
name: Start morning routine
description: Finish things in bedroom and prepare downstairs
"""
    _LOGGER.info("Dismissing backup alarm")
    pyscript.fully_dismiss_alarm(device="fully.nettbrett1")
    _LOGGER.info("Turning back on HVAC with daytime settings")
    climate.turn_on(entity_id="climate.soverom")
    melcloud.set_vane_vertical(entity_id="climate.soverom",position="swing")
    climate.set_temperature(entity_id="climate.soverom",temperature=16)
    _LOGGER.info("Turning off lights with a 120 second transition")
    light.turn_off(entity_id="light.soverom",transition=120)
    _LOGGER.info("Changing wakeup active to off")
    input_boolean.turn_off(entity_id="input_boolean.vekking_pagar")
    _LOGGER.info("Wait 30 seconds before turning off the sound")
    await asyncio.sleep(30)
    _LOGGER.info("Turning off the sound")
    remote.turn_off(entity_id="remote.harmony_hub_soverom")
    _LOGGER.info("Setting volume to 90 %")
    volume_increase(30, "media_player.godehol", final_volume = 0.9)
    _LOGGER.info("Turning off fully screen")
    pyscript.fully_to_foreground(device="fully.nettbrett1")
    await asyncio.sleep(5)
    pyscript.fully_turn_off_screen(device="fully.nettbrett1")
    _LOGGER.info("Done")

@service
async def wakeup_fully():
    """yaml
name: Wakeup fully, used for wakeup alarm
description: Sounding the alarm
"""
    pyscript.fully_turn_on_screen(device="fully.nettbrett1")
    pyscript.fully_to_foreground(device="fully.nettbrett1")

@service
async def wakeup_alarm():
    """yaml
name: Run wakeup alarm routine
description: Sounding the alarm
"""
    _LOGGER.info("Start: Wakeup routine")
    playlistID = state.get("input_text.vekking_spilleliste_id")
    _LOGGER.info("  > Setting volume to 0 for Godehol")
    media_player.volume_set(entity_id="media_player.godehol",volume_level=0)
    _LOGGER.info("  > Connecting to Godehol on spotcast")
    spotcast.start(entity_id="media_player.godehol")
    _LOGGER.info("  > Waiting 10 seconds for connection to be ready")
    await asyncio.sleep(10)
    _LOGGER.info("  > Playing playlist on spotify: " + playlistID)
    media_player.play_media(entity_id="media_player.spotify_gramatus", media_content_id="spotify:playlist:" + playlistID, media_content_type="playlist")
    _LOGGER.info("  > Waiting 5 more seconds")
    await asyncio.sleep(5)
    increase_time = 60
    _LOGGER.info("Shuffling playlist, turning on sound system and starting volumne increase over " + str(increase_time) + " seconds")
    media_player.shuffle_set(entity_id="media_player.spotify_gramatus", shuffle=False)
    remote.turn_on(entity_id="remote.harmony_hub_soverom",activity="Listen to Music")
    volume_increase(increase_time, "media_player.godehol", initial_volume = 0.0, final_volume = 0.5)
    _LOGGER.info("Done: Wakeup routine")

@service
async def set_wakeup_playlist(playlist):
    """yaml
name: Set wakeup playlist
description: Set the selected wakeup playlist
fields:
    playlist:
        description: Playlist to play
        required: true
        example: Våkneliste
        selector:
            select:
                options:
                    - "Våkneliste"
                    - "Lovsang"
                    - "Alle gromlåter"
                    - "90's Country"
"""
    playlistid = playlist_mapping[playlist]
    shuffleplaylistid = spotify_services.ensure_shuffled_playlist(playlistid)
    input_text.set_value(entity_id="input_text.vekking_spilleliste_id", value=shuffleplaylistid)
    input_select.select_option(entity_id="input_select.vekking_valgt_spilleliste", option=playlist)
    _LOGGER.info("Updated shuffle shadow playlist. Now setting selected playlist for wakeup to: \"" + playlist + "\" (original id: \"" + playlistid + "\", shuffle playlist id: \"" + shuffleplaylistid + "\")")

@service
def set_wakeup_trans():
    """yaml
name: Set wakeup transition endtime
description: Set the endtime for the wakeup transition if the alarm time changes
"""
    wakeup_time = state.getattr("input_datetime.vekking")["timestamp"]
    data = state.getattr("pyscript.huetrans_hoved_vekking")
    endtime_entity = "input_datetime." + data["endtime_entity"]
    # The wakeup transition runs for 60*60 seconds, but half is before wakeup and half after
    wakeup_endtime = wakeup_time + 30*60
    wakeup_endtime_str = str(datetime.timedelta(seconds=wakeup_endtime))
    input_datetime.set_datetime(entity_id=endtime_entity,time=wakeup_endtime_str)
