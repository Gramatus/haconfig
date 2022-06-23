import logging
import asyncio
import datetime
import spotify_services

playlist_mapping = {
    "Våkneliste": "3FVKcokzHla6424Cj74LzL",
    "Lovsang": "0dUdJSf4v753IJwv8xDThH",
    "Alle gromlåter": "2pjB7wGkkoG9VYY8enMR5b",
    "90's Country": "37i9dQZF1DWVpjAJGB70vU",
    "Classic Acoustic": "37i9dQZF1DX504r1DvyvxG",
    "Classical Sunday Morning": "5Gmlxl0elXRNLL0heTF8Wz",
    "Kristne gromlåter": "4dgE3OmDZxl5OOj5SSriWX"
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
            log.info("No initial volume supplied, will use current volume: " + str(initial_volume))
        else:
            initial_volume = 0.0
            log.warning("No initial volume supplied, no current volume found, will use 0.0. Attributes found:")
            log.info(attributes)
    volume_level = initial_volume
    volume_increase = final_volume - initial_volume
    fadein_steps = abs(int(100 * volume_increase))
    wait_seconds = 0
    if fadein_steps == 0:
        log.info("Volume change from " + str(initial_volume) + " to " + str(final_volume) + " will happen in 0 steps, i.e. no change will occur")
    else:
        wait_seconds = fadein_seconds / fadein_steps
    increase = final_volume > initial_volume
    increase_step = 0
    if not fadein_steps == 0:
        log.info("Will change volume from " + str(initial_volume) + " to " + str(final_volume) + " in "+str(fadein_seconds)+" seconds. Time for each step: " + str(round(wait_seconds, 2)))
        increase_step = volume_increase / fadein_steps
    media_player.volume_set(entity_id=device, volume_level=volume_level)
    for x in range(fadein_steps):
        volume_level=round(volume_level+increase_step, 2)
        if increase and volume_level > final_volume:
            volume_level=final_volume
            log.info("Reached max volume")
        elif not increase and volume_level < final_volume:
            volume_level=final_volume
            log.info("Reached min volume")
        media_player.volume_set(entity_id=device, volume_level=volume_level)
        await asyncio.sleep(wait_seconds)
    log.info("Done, final volume is: " + str(volume_level))

@service
async def good_night():
    """yaml
name: Good night routine
description: Set HVAC night settings, lower blinds and turn off lights after one minute
"""
    log.info("Turning on Fully screen and bringing Fully to the foreground")
    wakeup_fully()
    log.info("Turning down covers")
    cover.close_cover(entity_id="cover.tradfri_blind")
    log.info("Wait 16 seconds for cover to close")
    await asyncio.sleep(16)
    log.info("Turning on lights temporarily, with a 10 second transition")
    light.turn_on(entity_id="light.soverom",transition=10,kelvin=2000,brightness=30)
    log.info("Setting HVAC settings")
    melcloud.set_vane_vertical(entity_id="climate.soverom",position="auto")
    climate.set_temperature(entity_id="climate.soverom",temperature=17.5)
    turnoff_time = str(datetime.timedelta(seconds=int((datetime.datetime.now() - datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())+5*60))
    turnon_time = str(datetime.timedelta(seconds=state.getattr("input_datetime.vekking")["timestamp"]-5*60))
    log.info("Telling Fully to turn off WiFi between " + turnoff_time + " and " + turnon_time)
    pyscript.fully_set_wifi_off_between(timeoff=turnoff_time, timeon=turnon_time, device="fully.nettbrett1")
    log.info("Wait 120 seconds before turning starting to turn the lights off")
    await asyncio.sleep(120)
    log.info("Turning off lights with a 60 second transition")
    light.turn_off(entity_id="light.soverom",transition=60)
    log.info("Turning off Fully screen")
    pyscript.fully_turn_off_screen(device="fully.nettbrett1")
    log.info("Done")

@service
def test_wifi_off():
    turnoff_time = str(datetime.timedelta(seconds=int((datetime.datetime.now() - datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds())+5*60))
    turnon_time = str(datetime.timedelta(seconds=state.getattr("input_datetime.vekking")["timestamp"]-5*60))
    pyscript.fully_set_wifi_off_between(timeoff=turnoff_time, timeon=turnon_time, device="fully.nettbrett1")
    log.info(turnoff_time)
    log.info(turnon_time)

@service
async def start_morning():
    """yaml
name: Start morning routine
description: Finish things in bedroom and prepare downstairs
"""
    log.info("Dismissing backup alarm")
    pyscript.fully_dismiss_alarm(device="fully.nettbrett1")
    log.info("Turning back on HVAC with daytime settings")
    climate.turn_on(entity_id="climate.soverom")
    melcloud.set_vane_vertical(entity_id="climate.soverom",position="swing")
    climate.set_temperature(entity_id="climate.soverom",temperature=16)
    log.info("Turning off lights with a 120 second transition")
    light.turn_off(entity_id="light.soverom", transition=120)
    log.info("Changing wakeup active to off")
    input_boolean.turn_off(entity_id="input_boolean.vekking_pagar")
    log.info("Wait 30 seconds before turning off the sound")
    await asyncio.sleep(30)
    log.info("Turning off the sound")
    remote.turn_off(entity_id="remote.harmony_hub_soverom")
    log.info("Setting volume to 90 %")
    volume_increase(30, "media_player.godehol", final_volume = 0.9)
    log.info("Turning off fully screen")
    pyscript.fully_to_foreground(device="fully.nettbrett1")
    await asyncio.sleep(5)
    pyscript.fully_turn_off_screen(device="fully.nettbrett1")
    log.info("Done")

@service
async def wakeup_fully():
    """yaml
name: Wakeup fully, used for wakeup alarm
description: Sounding the alarm
"""
    pyscript.fully_turn_on_screen(device="fully.nettbrett1")
    pyscript.fully_to_foreground(device="fully.nettbrett1")

@service
async def wakeup_alarm(device="media_player.godehol"):
    """yaml
name: Run wakeup alarm routine
description: Sounding the alarm
"""
    log.info("Start: Wakeup routine")
    playlistID = state.get("input_text.vekking_spilleliste_id")
    pyscript.play_playlist_random(playlistid=playlistID, device=device, shuffle_type="No shuffle", fadein_seconds=60, final_volume=0.9, delay_seconds_start_spotcast=10)
    log.info("  > Waiting 5 seconds before turning on sound system")
    await asyncio.sleep(10)
    log.info("Turning on sound system")
    remote.turn_on(entity_id="remote.harmony_hub_soverom",activity="Listen to Music")
    log.info("Done: Wakeup routine")

@service
def ensure_alarm_active():
    """yaml
name: Ensure that the alarm actually started as expected
"""
    check_interval = 120
    need_to_check_alarm = True
    log.info("Started script to ensure that wakeup plays music as expected")
    while need_to_check_alarm:
        wakeup_active = state.get("input_boolean.vekking_pagar") == "on"
        if not wakeup_active:
            log.info("Wakeup is not active, will not do anything")
            need_to_check_alarm = False
            break
        asyncio.sleep(check_interval)
        target_device = "media_player.godehol"
        alarm_start = state.getattr("input_datetime.vekking")["timestamp"]
        midnight = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone()
        time_since_wakeup = datetime.datetime.now().timestamp() - (alarm_start + midnight.timestamp())
        if time_since_wakeup > 5*60:
            target_device = "media_player.soverom"
        cast_playback_active = state.get(target_device) == "playing"
        spotify_playback_active = state.get("media_player.spotify_gramatus") == "playing"
        if cast_playback_active and spotify_playback_active:
            log.info("Confirmed alarm is at expected state")
            need_to_check_alarm = False
            break
        minutes_since_wakeup = round(time_since_wakeup/60, 1)
        ha_uptime_seconds = datetime.datetime.now().timestamp() - datetime.datetime.strptime(state.get("sensor.oppetid_ha"), "%Y-%m-%dT%H:%M:%S.%f%z").timestamp()
        chromecast_power_plug = "device_not_yet_configured"
        # cc_time_since_turnon = (state.get(chromecast_power_plug + ".last_changed") - midnight).total_seconds()
        cc_time_since_turnon = 5*60 # Until I actually have a plug to use...
        # If not ok after 15 minutes, and HA has been up for more than 60 minutes, try restaring HA
        if time_since_wakeup > 15*60 and ha_uptime_seconds > 60*60:
            log.warning("Alarm still not running as expected after " + str(minutes_since_wakeup) + " minutes, restarting home assistant to see if that helps (HA uptime: " + str(datetime.timedelta(seconds=ha_uptime_seconds)) + ")")
            homeassistant.restart()
        # If not ok after 10 minutes, and the smart plug powering the chromecastdevice has been on for more than 60 minutes, try turning that off and then on again
        elif time_since_wakeup > 10*60 and cc_time_since_turnon > 60*60:
            log.warning("Alarm still not running as expected after " + str(minutes_since_wakeup) + " minutes, trying to restart chromecast device (by turning power off/on)")
            #light.turn_off(chromecast_power_plug)
            # await asyncio.sleep(15)
            #light.turn_on(chromecast_power_plug)
            log.info("Turning CC off/on not yet implemented - smart plug currently not acquired")
        else:
            # Change target media player to bedroom if Godehol does not work after 5 minutes
            if time_since_wakeup > 5*60:
                log.warning("Alarm still not running as expected after " + str(minutes_since_wakeup) + " minutes, trying to connect to " + target_device + ", in case the trouble is in the cast group and the rerunning wakeup routine")
            else:
                log.warning("Alarm still not running as expected after " + str(minutes_since_wakeup) + " minutes, trying to rerun wakeup routine")
            pyscript.wakeup_alarm(device=target_device)
    log.info("Finished ensure alarm script")

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
                    - "Classic Acoustic"
                    - "Classical Sunday Morning"
"""
    playlistid = playlist_mapping[playlist]
    input_text.set_value(entity_id="input_text.shuffle_status", value="Shuffling: " + playlist)
    shuffleplaylistid = spotify_services.ensure_shuffled_playlist(playlistid)
    input_text.set_value(entity_id="input_text.shuffle_status", value="idle")
    input_text.set_value(entity_id="input_text.vekking_spilleliste_id", value=shuffleplaylistid)
    input_select.select_option(entity_id="input_select.vekking_valgt_spilleliste", option=playlist)
    log.info("Updated shuffle shadow playlist. Now setting selected playlist for wakeup to: \"" + playlist + "\" (original id: \"" + playlistid + "\", shuffle playlist id: \"" + shuffleplaylistid + "\")")

@service
def set_wakeup_trans():
    """yaml
name: Set wakeup transition endtime
description: Set the endtime for the wakeup transition if the alarm time changes
"""
    # If we change the alarm between 1AM and wakeup time, the "trigger times" for fades have already been set and we need to reset them
    midnight = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone()
    seconds_since_midnight = (datetime.datetime.now().astimezone() - midnight).total_seconds()
    if seconds_since_midnight > (60*60)-30 and seconds_since_midnight < (60*60)+30:
        log.info("Currently at the exact moment when fade trigger times are set, waiting 60 seconds until that has finished")
        task.sleep(60)
        seconds_since_midnight = (datetime.datetime.now().astimezone() - midnight).total_seconds()
    wakeup_time = state.getattr("input_datetime.vekking")["timestamp"]
    if seconds_since_midnight > (60*60) and seconds_since_midnight < wakeup_time:
        log.info("We are now between 1AM and wakeup time, should reset fade trigger times")
        pyscript.set_trans_start_time(transition_group="Hoved")
        pyscript.set_trans_start_time(transition_group="Faste lys")
    else:
        log.info("All good")
    return
    # Code below not needed anymore
    wakeup_time = state.getattr("input_datetime.vekking")["timestamp"]
    data = state.getattr("pyscript.huetrans_hoved_vekking")
    endtime_entity = data["endtime_entity"]
    if not "." in endtime_entity:
        endtime_entity = "input_datetime." + endtime_entity
    # The wakeup transition runs for 60*60 seconds, but half is before wakeup and half after
    wakeup_endtime = wakeup_time + 30*60
    wakeup_endtime_str = str(datetime.timedelta(seconds=wakeup_endtime))
    input_datetime.set_datetime(entity_id=endtime_entity, time=wakeup_endtime_str)
