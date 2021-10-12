import aiohue
import logging
import async_timeout
from homeassistant.helpers import aiohttp_client,entity_registry
import attr
import aiohttp
import datetime
import json
import sys
import time
import datetime
import operator
import copy
import asyncio
import re

_LOGGER = logging.getLogger(__name__)

entity_prefix = "huetrans"
state_prefix = "pyscript." + entity_prefix
room_prefix = "pyscript.transrooms_"

def get_current_trans(transition_group):
    current_trans = None
    for val in state.names(domain="pyscript"):
        if entity_prefix+"_"+transition_group in val and state.get(val) == "on":
            current_trans = state.getattr(val)
    return current_trans

def get_scene_to_activate_with_time_and_previous(transition_group):
    current_trans = get_current_trans(transition_group)
    if current_trans == None:
        _LOGGER.info("No transition currently active")
        return
    seconds_to_target, seconds_to_target_from_midnight = get_seconds_to_target(transition_group)

    time_factor = 1
    if "starttime_entity" in current_trans and "endtime_entity" in current_trans:
        seconds_to_complete_trans = 0
        for scn in current_trans["Scenes"]:
            delay = 0
            if "delay" in scn:
                delay = scn["delay"]
            seconds_to_complete_trans = seconds_to_complete_trans + scn["timeinseconds"] + delay
        start = state.getattr("input_datetime." + current_trans["starttime_entity"])["timestamp"]
        end = state.getattr("input_datetime." + current_trans["endtime_entity"])["timestamp"]
        seconds_start_to_end = end - start
        time_factor = seconds_start_to_end / seconds_to_complete_trans
        _LOGGER.info("time_factor: " + str(time_factor) + ", Original running time: " + str(datetime.timedelta(seconds=seconds_to_complete_trans)) + ", Actual running time: " + str(datetime.timedelta(seconds=seconds_start_to_end)))

    seconds_for_remaining_scenes = 0
    scene_that_should_be_active = None
    previous_scene = None
    target_found = False
    for scn in sorted(current_trans["Scenes"], key=lambda i:i["index"], reverse=True):
        previous_scene = copy.copy(scn)
        if target_found == True:
            break
        scene_that_should_be_active = copy.copy(scn)
        scene_time = scn["timeinseconds"] * time_factor
        delay = 0
        if "delay" in scn:
            delay = scn["delay"]
        # Max allowed time from Hue is 65535 * 100ms, i.e. 1:49:13, so we limit to that (anything getting above that will change the "ratios", but that is acceptable)
        if scene_time > 65535/10:
            _LOGGER.info("Wanted run time makes this scene run longer that 1:49:13 (max from Hue), so run time is truncated. Wanted run time for \"" + scn["name"] + "\": " + str(datetime.timedelta(seconds=scene_time)))
            scene_time = 65535/10
        seconds_for_remaining_scenes += scene_time + delay
        scene_that_should_be_active["normaltimeinseconds"] = scene_time
        scene_that_should_be_active["timetotarget"] = seconds_to_target
        scene_that_should_be_active["normaltimetotarget"] = seconds_for_remaining_scenes
        elapsed_time_for_current_scene = seconds_for_remaining_scenes - seconds_to_target
        corrected_delay = delay - elapsed_time_for_current_scene
        if corrected_delay < 0:
            # Scene has already used up all available delay time (which normally is zero, so normally it is used up from the start)
            scene_that_should_be_active["timeinseconds"] = scene_time + corrected_delay
            corrected_delay = 0
        else:
            # There is still delay time "available", and thus the transition time should be the complete time expected for the scene
            scene_that_should_be_active["timeinseconds"] = scene_time
        scene_that_should_be_active["delay"] = corrected_delay
        if(seconds_for_remaining_scenes > seconds_to_target):
            target_found = True
    if seconds_to_target < 0:
        previous_scene = scene_that_should_be_active
        seconds_for_remaining_scenes = 0
    start_time = str(datetime.timedelta(seconds=seconds_to_target_from_midnight-seconds_for_remaining_scenes))
    final_endtime = str(datetime.timedelta(seconds=seconds_to_target_from_midnight))
    if target_found == False:
        _LOGGER.info("Run time for \"" + current_trans["friendly_name"] + "\": " + start_time + " to " + final_endtime + ". Not ready to run this transition yet.")
        return {
            "current": None,
            "previous": None
        }
    else:
        _LOGGER.info("Remaining run time for \"" + current_trans["friendly_name"] + "\": " + start_time + " to " + final_endtime + ".")
        return {
            "current": scene_that_should_be_active,
            "previous": previous_scene
        }

def get_seconds_to_target(transition_group):
    current_trans = get_current_trans(transition_group)
    if current_trans == None:
        _LOGGER.info("No transition currently active")
        return
    now = datetime.datetime.now()
    endtime_entity = current_trans["endtime_entity"]
    if endtime_entity == None:
        _LOGGER.info(current_trans["friendly_name"] + " has no endtime entity defined")
        return

    endtimevalue = state.get("input_datetime." + endtime_entity)
    endtime = time.strptime(endtimevalue,"%H:%M:%S")
    target_time = now.replace(hour=endtime.tm_hour, minute=endtime.tm_min, second=endtime.tm_sec, microsecond=0)
    seconds_to_target = (target_time - now).total_seconds()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_to_target_from_midnight = (target_time - midnight).total_seconds()
    return seconds_to_target, seconds_to_target_from_midnight

@service
def ensure_worklight_startup():
    """yaml
name: Ensure worklights startup time (also ensures startup times for "basic lights")
description: Ensure that there is enough time from wakeup lights until work lights
"""
    ensure_fade_diff("input_datetime.huetrans_vekking_endtime", "input_datetime.huetrans_arbeidslys_endtime", 60*60, "Wakeup", "work lights")
    ensure_fade_diff("input_datetime.huetrans_vekking_endtime", "input_datetime.huetrans_basislys_morgen_endtime", -30*60, "Wakeup", "basic lights morning")
    ensure_fade_diff("input_datetime.huetrans_basislys_morgen_endtime", "input_datetime.huetrans_basislys_dag_endtime", 1*60*60+15*60, "Basic lights morning", "basic lights day")

def ensure_fade_diff(entity_id_before, entity_id_after, min_diff, logname_before, logname_after):
    before_endtime = state.getattr(entity_id_before)["timestamp"]
    after_endtime = state.getattr(entity_id_after)["timestamp"]
    diff = after_endtime - before_endtime
    if diff < min_diff:
        _LOGGER.info("Changing fade end time - " + logname_before + " time collides with " + logname_after + ", delaying " + logname_after + ". " + logname_before + " value: " + str(datetime.timedelta(seconds=before_endtime))+ ", " + logname_after + " value: " + str(datetime.timedelta(seconds=after_endtime)) + ", wanted diff: " + str(min_diff) + ", actual diff: " + str(diff))
        input_datetime.set_datetime(entity_id=entity_id_after,time=str(datetime.timedelta(seconds=before_endtime+min_diff)))
    else:
        _LOGGER.info("Not changing fade end time - " + logname_before + " time does not collide with " + logname_after + ". " + logname_before + " value: " + str(datetime.timedelta(seconds=before_endtime))+ ", " + logname_after + " value: " + str(datetime.timedelta(seconds=after_endtime)) + ", wanted diff: " + str(min_diff) + ", actual diff: " + str(diff))

@service
def reset_trans():
    """yaml
name: Reset transition triggers
description: Sets current transition and transition start time for all transition groups
"""
    set_current_trans_auto("Hoved")
    set_trans_start_time("Hoved")
    set_current_trans_auto("Faste lys")
    set_trans_start_time("Faste lys")
    trigger_transition_scene("Hoved")
    trigger_transition_scene("Faste lys")

@service
def set_current_trans_auto(transition_group):
    """yaml
name: Set current transition (automatic)
description: Set which transition is currently active, based on end times
fields:
    transition_group:
        description: Which transition group to trigger actions for
        required: true
        example: hoved
        selector:
            select:
                options:
                    - "Hoved"
                    - "Faste lys"
"""
    transition_group = transition_group.lower().replace(" ","")
    _LOGGER.info("Reading state: sensor.template_next_transition_" + transition_group)
    next_trans_group = state.get("sensor.template_next_transition_" + transition_group)
    set_current_trans(next_trans_group)

@service
def set_trans_start_time(transition_group):
    """yaml
name: Set transition start time trigger
description: Set an input_datetime that triggers the next transition
fields:
    transition_group:
        description: Which transition group to trigger actions for
        required: true
        example: hoved
        selector:
            select:
                options:
                    - "Hoved"
                    - "Faste lys"
"""
    transition_group = transition_group.lower().replace(" ","")
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seconds_since_midnight = (now - midnight).total_seconds()
    next_trans = None
    next_trans_timestamp = 0
    for val in state.names(domain="pyscript"):
        if entity_prefix+"_"+transition_group in val:
            data = state.getattr(val)
            if "endtime_entity" not in data:
                continue
            seconds_to_complete_trans = 0
            for scn in data["Scenes"]:
                delay = 0
                if "delay" in scn:
                    delay = scn["delay"]
                seconds_to_complete_trans = seconds_to_complete_trans + scn["timeinseconds"] + delay
            endtime = state.getattr("input_datetime." + data["endtime_entity"])["timestamp"]
            starttime = endtime-seconds_to_complete_trans
            if "starttime_entity" in data:
                starttime = state.getattr("input_datetime." + data["starttime_entity"])["timestamp"]
            data["start_time"] = str(datetime.timedelta(seconds=starttime))
            state.setattr(val+".start_time",data["start_time"])
            if seconds_since_midnight < starttime and (next_trans_timestamp == 0 or next_trans_timestamp > starttime):
                next_trans = data
                next_trans_timestamp = starttime
    if next_trans != None:
        _LOGGER.info("Neste fade med " + transition_group + " starter kl. " + next_trans["start_time"])
        _LOGGER.debug(next_trans)
        input_datetime.set_datetime(entity_id="input_datetime.lysfade_start_neste_" + transition_group + "fade",time=next_trans["start_time"])
    else:
        _LOGGER.info("No more transitions scheduled for today for \"" + transition_group + "\"...")

@service
def set_current_trans(trans):
    """yaml
name: Set current transition
description: Set which transition is currently active (for the group it belongs to)
fields:
    trans:
        description: Which transition to set as active
        required: true
        example: 
        selector:
            entity:
                domain: pyscript
                device_class: Fadeoppsett
"""
    transition_group = trans.replace(state_prefix+"_","").split("_")[0]
    for val in state.names(domain="pyscript"):
        if entity_prefix+"_"+transition_group in val:
            state.set(val,"off")
    _LOGGER.info("Set state to off for all transitions in group: " + transition_group)
    state.set(trans,"on")
    _LOGGER.info("Set state to on for: " + trans)

@service
def trigger_transition_scene(transition_group, only_for_room=None):
    """yaml
name: Trigger next transition scene
description: >
    Will trigger the next transition scene based on
        a) The current value of "input_select.lysfade_aktiv_gruppe", and
        b) What scene is currently active within that group (read from a JSON state object). The scenelist and roomlist are hardcoded as dictionaries in hue_trans_tools.py.
    Scenes will only be triggered for rooms where fading is activated and the lights are on.
fields:
    transition_group:
        description: Which transition group to trigger actions for
        required: true
        example: hoved
        selector:
            select:
                options:
                    - "Hoved"
                    - "Faste lys"
    only_for_room:
        description: If this should only run for the selected rooms
        required: false
        example: hoved
        selector:
            entity:
                domain: pyscript
                device_class: trans_room
"""
    transition_group = transition_group.lower().replace(" ","")
    current_trans = get_current_trans(transition_group)
    if only_for_room != None:
        only_for_room_attr = state.getattr(only_for_room)
        if "entity_id" in only_for_room_attr:
            only_for_room = only_for_room_attr["entity_id"]
        # If we are currently running a transition, don't run the "single room" action (it is probably triggered by the transition actually turning on the lights)
        if state.get("timer.lysfade_aktiv_trans_trigger_" + transition_group) == "active":
            _LOGGER.info("Skipping only_for_room run for: " + only_for_room)
            return
        _LOGGER.info("Will ONLY run for the following rooms on this run: " + only_for_room)
    else:
        timer.start(entity_id="timer.lysfade_aktiv_trans_trigger_" + transition_group)

    if current_trans == None:
        _LOGGER.info("No transition currently active")
        return

    scenes = get_scene_to_activate_with_time_and_previous(transition_group)
    _LOGGER.info(scenes)

    alarmActive = state.get("input_boolean.alarm_aktiv") == "on"
    alarmLightActive = state.get("input_boolean.alarm_med_lys") == "on"
    wakeup_trans_name = "Fadeoppsett: Vekking"
    skip_inactive_wakeup_trans = current_trans["friendly_name"] == wakeup_trans_name and scenes["current"] != None and (not alarmActive or not alarmLightActive) and only_for_room == None

    force_run = False
    alarmRunning = state.get("input_boolean.vekking_pagar") == "on"
    if "force_run" in current_trans and alarmRunning:
        force_run = current_trans["force_run"]

    prefade_duration = int(float(state.get("input_number.lysfade_prefade_varighet")))

    needs_prefade = False
    has_finished = False
    if(scenes["current"] == None):
        return
    ignore_currentscene = False
    if scenes["current"]["timetotarget"] < 0:
        # This should only happen when a light is turned on after end time (e.g. when coming home after the normal end of transition)
        has_finished = True
        # Do a quick transition to the right state. At this point, previous and current are the same. We update data for "previous" because that is what is used in the next bit and that saves us some logic later.
        scenes["previous"]["loginfo"]  = "Past target time, quickly restoring correct light, scene no. " + str(scenes["previous"]["index"]) + " of " + str(len(current_trans["Scenes"])) + ","
        scenes["previous"]["timeinseconds"] = prefade_duration
    elif scenes["current"]["index"] != scenes["previous"]["index"] and (scenes["current"]["normaltimetotarget"]-scenes["current"]["timetotarget"]) > 300:
        # We are currently not at the first scene in the transition. If any room is not currently already on it's way to the correct scene, switch to that one first. However, only do this if we are more than five minutes after the original start time.
        needs_prefade = True
        scenes["previous"]["loginfo"] = "Quickly starting previous scene, no. " + str(scenes["previous"]["index"]) + " of " + str(len(current_trans["Scenes"])) + ","
        scenes["previous"]["timeinseconds"] = prefade_duration

    # Let there be a 2 second wait between each call, to avoid the bridge being overloaded
    delay_between_triggers = 2
    delay = 0
    anything_activated = False
    if (needs_prefade or has_finished) and not skip_inactive_wakeup_trans:
        for room in current_trans["Rooms"]:
            if only_for_room != None:
                ignore_currentscene = True
                if only_for_room != room:
                    continue
            delay = delay + delay_between_triggers
            scene_activated = trigger_for_room_if_active(room, scenes["previous"], scenes["current"]["id"], delay, ignore_currentscene=ignore_currentscene)
            if scene_activated:
                anything_activated = True
            await asyncio.sleep(delay_between_triggers)

    if has_finished:
        _LOGGER.info("This transition has finished, but is still the current transition. Setting time for next transition group to start.")
        set_trans_start_time(transition_group)
        return

    if skip_inactive_wakeup_trans:
        timetotarget = scenes["current"]["timetotarget"]
        if timetotarget < 0:
            timetotarget = 0
        wait_time = timetotarget + 5*60
        if not alarmActive:
            _LOGGER.info("Alarm is not active, thus the wakeup fade should not run. Starting timer, without any scenes activating, to trigger a new evaluation in: " + str(datetime.timedelta(seconds=wait_time)))
        elif not alarmLightActive:
            _LOGGER.info("Alarm is active, but without lights, thus the wakeup fade should not run. Starting timer, without any scenes activating, to trigger a new evaluation in: " + str(datetime.timedelta(seconds=wait_time)))
        timer.start(entity_id="timer.lysfade_neste_trigger_" + transition_group, duration=wait_time)
        return

    if anything_activated:
        _LOGGER.info("Waiting " + str(prefade_duration) + " seconds for the previous scene to load")
        await asyncio.sleep(prefade_duration)
        _LOGGER.info("Now loading the actual scene")
    lysfade_settings = state.getattr("pyscript.transtools_settings")
    _LOGGER.info("Next scene: \"" + scenes["current"]["name"] + "\", no. " + str(scenes["current"]["index"]) + " of " + str(len(current_trans["Scenes"])))
    delay = 0
    for room in current_trans["Rooms"]:
        if only_for_room != None and only_for_room != room:
            continue
        trigger_for_room_if_active(room, scenes["current"], scenes["current"]["id"], delay, force_run)
        delay = delay + delay_between_triggers
        await asyncio.sleep(delay_between_triggers)

    # This is just "FYI", not used for anything, but it could be useful in debugging...
    state.setattr("pyscript.transtools_settings.currentScene_" + transition_group, {
        "name": scenes["current"]["name"],
        "id": scenes["current"]["id"],
        "parentTrans": current_trans
    })
    duration = round(scenes["current"]["timeinseconds"] + scenes["current"]["delay"], 0)
    _LOGGER.info("Starting timer to trigger next scene in: " + str(datetime.timedelta(seconds=duration)))
    timer.start(entity_id="timer.lysfade_neste_trigger_" + transition_group, duration=duration-delay)

def trigger_for_room_if_active(room_entity, scn, targetid, delay, force_run=False, ignore_currentscene=False):
    room_key = room_entity.replace(".","_")
    lysfade_settings = state.getattr("pyscript.transtools_settings")
    if room_key in lysfade_settings:
        roomsettings = lysfade_settings[room_key]
    else:
        roomsettings = {
            "trans_active": True,
            "currentScene": ""
        }
    if "trans_active" not in roomsettings:
        roomsettings["trans_active"] = True
    if "currentScene" not in roomsettings:
        roomsettings["currentScene"] = ""

    lights_on = state.get(room_entity) == "on"
    trans_active = roomsettings["trans_active"]
    already_at_scene = roomsettings["currentScene"] == targetid and not ignore_currentscene
    transition_time = round(scn["timeinseconds"] - delay, 0)
    if force_run:
        lights_on = True
        trans_active = True

    scene_activated = False
    if already_at_scene:
        _LOGGER.info("  > " + room_entity + ": Room is already at, or activating, the correct scene. Current: \"" + roomsettings["currentScene"] + "\", Target: \"" + targetid + "\", To activate: \"" + scn["id"] + "\" (\"" + scn["name"] + "\")")
    elif lights_on and trans_active:
        debug_info = ""
        if state.get("pyscript.transtools_debugmode") != "on":
            pyscript.turn_on_scene_by_id(scene_id=scn["id"], group_id=room_entity, transitionsecs=transition_time, transitionms=0, no_logging=True)
        else:
            debug_info = "DEBUG MODE, skipping: "
        if "loginfo" not in scn:
            scn["loginfo"] = "Triggering scene"
        _LOGGER.info("  > " + room_entity + ":" + debug_info + " " +scn["loginfo"] + " \"" + scn["name"] + "\" (id: \"" + scn["id"] + "\") with a transitiontime of " + str(transition_time) + " seconds")
        roomsettings["currentScene"] = scn["id"]
        roomsettings["currentSceneName"] = scn["name"]
        scene_activated = True
    else:
        if not lights_on:
            _LOGGER.info("  > " + room_entity + ": Lights are not on, will not do anything. Current: \"" + roomsettings["currentScene"] + "\", Target: \"" + targetid + "\", To activate: \"" + scn["id"] + "\" (\"" + scn["name"] + "\")")
        elif not trans_active:
            _LOGGER.info("  > " + room_entity + ": Transitions are disabled, will not do anything. Current: \"" + roomsettings["currentScene"] + "\", Target: \"" + targetid + "\", To activate: \"" + scn["id"] + "\" (\"" + scn["name"] + "\")")
        else:
            _LOGGER.info("  > " + room_entity + ": Skipping start for an unknown reason. Current: \"" + roomsettings["currentScene"] + "\", Target: \"" + targetid + "\", To activate: \"" + scn["id"] + "\" (\"" + scn["name"] + "\")")

    room_name = state.getattr(room_entity)["friendly_name"]
    fadeend_entity = room_prefix + room_key + "_fadeend"
    transactive_entity = room_prefix + room_key + "_trans_active"
    if scene_activated:
        state.setattr(fadeend_entity+".duration",str(datetime.timedelta(seconds=transition_time)))
        state.setattr(fadeend_entity+".start_time",datetime.datetime.now().isoformat())
        state.setattr(fadeend_entity+".end_time",(datetime.datetime.now() + datetime.timedelta(0,transition_time)).isoformat())
        state.set(fadeend_entity,"active")
        state.setattr(fadeend_entity+".friendly_name", room_name + ": til \"" + scn["name"] + "\"")

    state.setattr("pyscript.transtools_settings." + room_key, roomsettings)
    state.setattr("pyscript.active_trans_scenes." + room_key, roomsettings["currentSceneName"])
    state.setattr(transactive_entity+".friendly_name", room_name + ": lys skal fade")
    return scene_activated

@service
def toggle_trans_active(room):
    """yaml
name: Toggle transistion active
description: TODO
fields:
    room:
        description: Which room to toggle for
        required: true
        example: 
        selector:
            entity:
                domain: pyscript
                device_class: trans_active
"""
    if state.get(room) == "on":
        _LOGGER.info("Set state to off for: " + room)
        state.set(room,"off")
    else:
        _LOGGER.info("Set state to on for: " + room)
        state.set(room,"on")

@service
def run_trans_for_turned_on_room(trigger):
    """yaml
name: Activate "current" transition for a room where the lights just turned on
fields:
    trigger:
        description: Trigger data from an automation
        required: true
"""
    trigger = str(trigger)
    trigger = re.compile("(<state [^;]*)(;)([^>]*>)").sub('\g<1>,\g<3>',trigger)
    comma_replacement = ";;;"
    for item in re.findall("\[[^]]*\]", trigger):
        trigger = trigger.replace(item,item.replace(",", comma_replacement))
    for item in re.findall("\([^)]*\)", trigger):
        trigger = trigger.replace(item,item.replace(",", comma_replacement))
    trigger = re.compile("(\s*)([^=\s]*?)(=)([^,>]*)").sub('\g<1>\"\g<2>\":\"\g<4>\"',trigger)
    trigger = trigger.replace(comma_replacement, ",")
    trigger = re.compile("( <state)([^>]*)(>)").sub('{\g<2>}',trigger)
    trigger = trigger.replace("\":\"[","\": [")
    trigger = trigger.replace("]\",","],")
    trigger = trigger.replace("'","\"")
    trigger = trigger.replace(" None"," null")
    # Load the JSON object and then get the event data
    trigger_data = json.loads(trigger)
    _LOGGER.debug("Entity that triggered the automation: " + trigger_data["entity_id"])
    trigger_transition_scene(transition_group="Hoved", only_for_room=trigger_data["entity_id"])

@service
def run_night_light(duration_mins):
    """yaml
name: Run night light
description: Start night light and let it run for the specified duration
fields:
    duration_mins:
        description: Number of minutes for the light to stay on
        required: true
        example: 15
        selector:
            number:
                min: 5
                max: 60
                step: 5
                mode: box
"""
    timer.start(entity_id="timer.natt_nedtelling", duration=duration_mins*60)
    # TODO: Consider if I will be saving this anywhere?
    # input_select.select_option(entity_id="input_select.nattlys_varighet", option="15 min")
    pyscript.turn_on_scene_by_id(scene_id="Y2qG5PtH6AC7b1j")
    await asyncio.sleep(10)
    pyscript.turn_on_scene_by_id(scene_id="xyJCA3wUDhukb-w")
    await asyncio.sleep(9*60 + 50)
    next_delay = 5*60
    light.turn_on(entity_id="light.c_hue_go_soverom_1", transition=next_delay, brightness=1)
    light.turn_on(entity_id="light.c_hue_go_soverom_2", transition=next_delay, brightness=1)
    await asyncio.sleep(next_delay)
    light.turn_off(entity_id="light.c_hue_go_soverom_1")
    light.turn_off(entity_id="light.c_hue_go_soverom_2")

@service
def stop_night_light():
    """yaml
name: Stop night light
description: Finish night light run
"""
    timer.finish(entity_id="timer.natt_nedtelling")
    light.turn_off(entity_id="light.c_hue_go_soverom_1")
    light.turn_off(entity_id="light.c_hue_go_soverom_2")
