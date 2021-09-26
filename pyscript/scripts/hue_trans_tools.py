# Testing my own hue api component
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
    # current_trans = state.get("input_select.lysfade_aktiv_gruppe")
    current_trans = get_current_trans(transition_group)
    if current_trans == None:
        _LOGGER.info("No transition currently active")
        return
    seconds_to_target, seconds_to_target_from_midnight = get_seconds_to_target(transition_group)

    time_factor = 1
    if "starttime_entity" in current_trans and "endtime_entity" in current_trans:
        seconds_to_complete_trans = 0
        for scn in current_trans["Scenes"]:
            seconds_to_complete_trans = seconds_to_complete_trans + scn["timeinseconds"]
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
        # Max allowed time from Hue is 65535 * 100ms, i.e. 1:49:13, so we limit to that (anything getting above that will change the "ratios", but that is acceptable)
        if scene_time > 65535/10:
            _LOGGER.info("Wanted run time makes this scene run longer that 1:49:13 (max from Hue), so run time is truncated. Wanted run time for \"" + scn["name"] + "\": " + str(datetime.timedelta(seconds=scene_time)))
            scene_time = 65535/10
        seconds_for_remaining_scenes += scene_time
        scene_that_should_be_active["normaltimeinseconds"] = scene_time
        scene_that_should_be_active["timetotarget"] = seconds_to_target
        scene_that_should_be_active["normaltimetotarget"] = seconds_for_remaining_scenes
        scene_that_should_be_active["timeinseconds"] = scene_time - (seconds_for_remaining_scenes - seconds_to_target)
        if(seconds_for_remaining_scenes > seconds_to_target):
            target_found = True
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
                seconds_to_complete_trans = seconds_to_complete_trans + scn["timeinseconds"]
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

# Suggested use case:
# 1. Run an automation every x minutes before a given time
# 2. This automation triggers this, which runs the next light
# Alternative:
# - Set time to next light as a value somewhere
# - Trigger this based on a timer that this thing starts
@service
def trigger_transition_scene(transition_group):
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
"""
    transition_group = transition_group.lower().replace(" ","")
    current_trans = get_current_trans(transition_group)

    if current_trans == None:
        _LOGGER.info("No transition currently active")
        return

    scenes = get_scene_to_activate_with_time_and_previous(transition_group)
    _LOGGER.debug(scenes)

    if current_trans["friendly_name"] == "Fadeoppsett: Vekking":
    # if current_trans["friendly_name"] == "Fadeoppsett: Arbeidslys":
        alarmActive = state.get("input_boolean.alarm_aktiv") == "on"
        alarmLightActive = state.get("input_boolean.alarm_med_lys") == "on"
        timetotarget = scenes["current"]["timetotarget"]
        if timetotarget < 0:
            timetotarget = 0
        wait_time = timetotarget + 5*60
        if not alarmActive or not alarmLightActive:
            if not alarmActive:
                _LOGGER.info("Alarm is not active, thus the wakeup fade should not run. Starting timer, without any scenes activating, to trigger a new evaluation in: " + str(datetime.timedelta(seconds=wait_time)))
            elif not alarmLightActive:
                _LOGGER.info("Alarm is active, but without lights, thus the wakeup fade should not run. Starting timer, without any scenes activating, to trigger a new evaluation in: " + str(datetime.timedelta(seconds=wait_time)))
            timer.start(entity_id="timer.lysfade_neste_trigger_" + transition_group, duration=wait_time)
            return

    force_run = False
    if "force_run" in current_trans:
        force_run = current_trans["force_run"]

    needs_prefade = False
    has_finished = False
    if(scenes["current"] == None):
        return
    if scenes["current"]["timetotarget"] < 0:
        # This should only happen when a light is turned on after end time (e.g. when coming home after the normal end of transition)
        has_finished = True
        # Do a quick transition to the right state. At this point, previous and current are the same. We update data for "previous" because that is what is used in the next bit and that saves us some logic later.
        scenes["previous"]["loginfo"]  = "Past target time, quickly restoring correct light: " + scenes["previous"]["name"] + ", no. " + str(scenes["previous"]["index"]) + " of " + str(len(current_trans["Scenes"]))
        scenes["previous"]["timeinseconds"] = 60
    elif scenes["current"]["index"] != scenes["previous"]["index"] and (scenes["current"]["normaltimetotarget"]-scenes["current"]["timetotarget"]) > 300:
        # We are currently not at the first scene in the transition. If any room is not currently already on it's way to the correct scene, switch to that one first. However, only do this if we are more than five minutes after the original start time.
        needs_prefade = True
        #_LOGGER.info("Quickly starting previous scene: " + scenes["previous"]["name"] + ", no. " + str(scenes["previous"]["index"]) + " of " + str(len(current_trans["Scenes"])))
        scenes["previous"]["loginfo"] = "Quickly starting previous scene: " + scenes["previous"]["name"] + ", no. " + str(scenes["previous"]["index"]) + " of " + str(len(current_trans["Scenes"]))
        scenes["previous"]["timeinseconds"] = 60

    # Let there be a 2 second wait between each call, to avoid the bridge being overloaded
    delay_between_triggers = 2
    delay = 0
    anything_activated = False
    if needs_prefade or has_finished:
        for room in current_trans["Rooms"]:
            delay = delay + delay_between_triggers
            scene_activated = trigger_for_room_if_active(room, scenes["previous"], scenes["current"]["id"], delay)
            if scene_activated:
                anything_activated = True
            await asyncio.sleep(delay_between_triggers)

    if has_finished:
        _LOGGER.info("This transition has finished, but is still the current transition. Setting time for next transition group to start.")
        set_trans_start_time(transition_group)
        return

    if anything_activated:
        # TODO: Consider if we should skip waiting when no scenes are active, or if that is not needed? Note: if this happens, nothing will happen later on as well, so it is really not so important (except if some rooms are correct and some not?)
        _LOGGER.info("Waiting 60 seconds for the previous scene to load")
        await asyncio.sleep(60)
        _LOGGER.info("Now loading the actual scene")
    lysfade_settings = state.getattr("pyscript.transtools_settings")
    _LOGGER.info("Next scene: \"" + scenes["current"]["name"] + "\", no. " + str(scenes["current"]["index"]) + " of " + str(len(current_trans["Scenes"])))
    delay = 0
    for room in current_trans["Rooms"]:
        trigger_for_room_if_active(room, scenes["current"], scenes["current"]["id"], delay, force_run)
        delay = delay + delay_between_triggers
        await asyncio.sleep(delay_between_triggers)

    state.setattr("pyscript.transtools_settings.currentScene", {
        "name": scenes["current"]["name"],
        "id": scenes["current"]["id"],
        "parentTrans": current_trans
    })
    duration = round(scenes["current"]["timeinseconds"],0)
    _LOGGER.info("Starting timer to trigger next scene in: " + str(datetime.timedelta(seconds=duration)))
    timer.start(entity_id="timer.lysfade_neste_trigger_" + transition_group, duration=duration-delay)

def trigger_for_room_if_active(room_entity, scn, targetid, delay, force_run=False):
    # _LOGGER.info("Next room: " + room_entity)
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
    # _LOGGER.info("Checking if scene with id: " + scn["id"] + " should be triggered for group: " + room_entity)

    lights_on = state.get(room_entity) == "on"
    trans_active = roomsettings["trans_active"]
    already_at_scene = roomsettings["currentScene"] == targetid
    duration = round(scn["timeinseconds"] - delay, 0)
    if force_run:
        lights_on = True
        trans_active = True

    scene_activated = False
    if already_at_scene:
        _LOGGER.info("  > " + room_entity + ": Room is already at, or activating, the correct scene. Current: \"" + roomsettings["currentScene"] + "\", Target: \"" + targetid + "\", To activate: \"" + scn["id"] + "\" (\"" + scn["name"] + "\")")
    elif lights_on and trans_active:
        debug_info = ""
        if state.get("pyscript.transtools_debugmode") != "on":
            pyscript.turn_on_scene_by_id(scene_id=scn["id"],group_id=room_entity,transitionsecs=duration)
        else:
            debug_info = "DEBUG MODE, skipping: "
        if "loginfo" in scn:
            _LOGGER.info(debug_info + scn["loginfo"])
        else:
            _LOGGER.info("  > " + room_entity + ":" + debug_info + " Triggering scene \"" + scn["name"] + "\" (id: \"" + scn["id"] + "\") with a transitiontime of " + str(duration) + " seconds")
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
        state.setattr(fadeend_entity+".duration",str(datetime.timedelta(seconds=duration)))
        state.setattr(fadeend_entity+".start_time",datetime.datetime.now().isoformat())
        state.setattr(fadeend_entity+".end_time",(datetime.datetime.now() + datetime.timedelta(0,duration)).isoformat())
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
