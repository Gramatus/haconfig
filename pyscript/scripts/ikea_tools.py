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
import math
import database_services
import inspect
# import traceback

room_prefix = "pyscript.transrooms_"

@service
def turn_on_ikea_lights_when_room_turned_on(trigger=None, entity_id=None, area_id=None, disabled=False):
    """yaml
name: Turn on IKEA lights the lights in a room are turned on
fields:
    trigger:
        description: Trigger data from an automation
        required: true
"""
    if disabled:
        return
    if area_id != None:
        log.debug("Turning on all lights in AREA \"" + area_id + "\"")
        light.turn_on(area_id=area_id)
    else:
        log.info("TODO - or not something I will not handle?")
    # log.info("entity_id: " + str(entity_id))
    # log.info(light.kontor.last_changed)
    # log.info("area_id: " + area_id)
    # if trigger != None:
    #     trigger_data = handle_trigger_data(trigger)
    #     log.info(trigger_data)
    # log.info("TODO")

@service
def turn_off_ikea_lights_when_room_turned_off(trigger=None, entity_id=None, area_id=None, disabled=False):
    """yaml
name: Turn off IKEA lights the lights in a room are turned off
fields:
    trigger:
        description: Trigger data from an automation
        required: true
"""
    if disabled:
        return
    if area_id != None:
        log.debug("Turning off all lights in AREA \"" + area_id + "\"")
        light.turn_off(area_id=area_id)
    else:
        log.info("TODO - or not something I will not handle?")
    # log.info("entity_id: " + str(entity_id))
    # log.info(light.kontor.last_changed)
    # log.info("area_id: " + area_id)
    # if trigger != None:
    #     trigger_data = handle_trigger_data(trigger)
    #     log.info(trigger_data)
    # log.info("TODO")

def handle_trigger_data(trigger):
    trigger = str(trigger)
    trigger = re.compile("(<state [^;]*)(;)([^>]*>)").sub('\\g<1>,\\g<3>',trigger)
    comma_replacement = ";;;"
    for item in re.findall("\\[[^]]*\\]", trigger):
        trigger = trigger.replace(item,item.replace(",", comma_replacement))
    for item in re.findall("\\s[^)]*\\)", trigger):
        trigger = trigger.replace(item,item.replace(",", comma_replacement))
    trigger = re.compile("(\\s*)([^=\\s]*?)(=)([^,>]*)").sub('\\g<1>\"\\g<2>\":\"\\g<4>\"',trigger)
    trigger = trigger.replace(comma_replacement, ",")
    trigger = re.compile("( <state)([^>]*)(>)").sub('{\\g<2>}',trigger)
    trigger = trigger.replace("\":\"[","\": [")
    trigger = trigger.replace("]\",","],")
    trigger = trigger.replace("'","\"")
    trigger = trigger.replace(" None"," null")
    # Load the JSON object and then get the event data
    trigger_data = json.loads(trigger)
    return trigger_data

@service
def trigger_for_room_if_active_ikea(dataset, room:str, elapsed_time:int=0, current_step:int=1, override_time:int=None, force_run:bool=False, index:int=1):
    # Important info on IKEA lights:
    # https://github.com/dresden-elektronik/deconz-rest-plugin/issues/894
    # Quick summary:
    # - when a transition is ongoing, the light seems to "freeze"
    # - some actions "unfreezes" the light, e.g. sending "bri_inc" = 0 (according to poster, this might be translated to a "stop" command)
    log.debug("  > " + room + ": Started [trigger_for_room_if_active_ikea], step #" + str(current_step))
    max_trans_time_ikea = 5*60
    min_fade_steps = 6
    room_key = room.replace(".","_")
    fadeend_entity = room_prefix + room_key + "_fadeend"
    # endtime = datetime.datetime.strptime(endtimevalue, "%Y-%m-%dT%H:%M:%S.%f%z")
    # fadeend = datetime.datetime.strptime(state.getattr(fadeend_entity)["end_time"], "%Y-%m-%dT%H:%M:%S.%f")
    fading = state.get(fadeend_entity) == "active"
    # This expects this to always run AFTER other code that ensures this has a value. Normally that is how it works.
    roomsettings = state.getattr("pyscript.transtools_settings")[room_key]
    lights_on = state.get(room) == "on"
    trans_active = roomsettings["trans_active"]
    if force_run:
        lights_on = True
        trans_active = True
    if not lights_on:
        log.debug("  > " + room + ": Lights are not on, will not do anything.")
        return
    elif not trans_active:
        log.debug("  > " + room + ": Transitions are disabled, will not do anything.")
        return
    elif not fading:
        # We expect some other code to set the correct state for the rooms fadeend entity before this code runs
        log.debug("  > " + room + ": Fade is not running, will not do anything")
        return
    for data in dataset:
        if data["room"] != room:
            continue
        # log.info(data)
        scn = data["Scenes"][0]
        for scene in data["Scenes"]:
            if scene["index"] == index:
                scn = scene
        final_bri = scn["brightness"]
        final_kelvin = None
        if "kelvin" in scn:
            final_kelvin = scn["kelvin"]
        final_hue = None
        if "hue" in scn:
            final_hue = scn["hue"]
        final_sat = None
        if "sat" in scn:
            final_sat = scn["sat"]
        full_fade_time = scn["timeinseconds"]
        if override_time != None:
            full_fade_time = override_time
        if full_fade_time < 60:
            min_fade_steps = 4
        if full_fade_time < 10:
            min_fade_steps = 2
        fade_time = full_fade_time - elapsed_time
        # log.info("  > " + room + ": fade_time: "+ str(fade_time) + ", elapsed_time: " + str(elapsed_time) + ", full time: " + str(full_fade_time))
        if fade_time > max_trans_time_ikea:
            fade_time = max_trans_time_ikea
        fade_steps = full_fade_time / max_trans_time_ikea
        if fade_steps < min_fade_steps:
            log.debug("Reducing fade time to make sure we have at least " + str(min_fade_steps) + " steps for the fade")
            fade_steps = min_fade_steps
            fade_time = full_fade_time / fade_steps
        completed_level_after = ((fade_time * 2) + elapsed_time) / full_fade_time
        if completed_level_after > 1:
            completed_level_after = 1
        # log.info("completed_level_after: "+ str(completed_level_after))
        # log.info("fade_time: "+ str(fade_time))
        for light_entity in data["lights"]:
            light_on = state.get(light_entity) == "on"
            if not light_on:
                if not force_run:
                    log.debug("    # " + light_entity + ": Light is not on, will not do anything.")
                    continue
                else:
                    log.debug("    # " + light_entity + ": Light is not on. Will turn on and wait a bit to ensure attributes are set correctly.")
                    light.turn_on(entity_id=light_entity, brightness_step=0) # See info above, used to be sure the light is "freed up" to receive new commands.
                    turnon_wait_time=1000
                    await asyncio.sleep(turnon_wait_time)
            light_attr = state.getattr(light_entity)
            current_bri = 0
            if "brightness" in light_attr:
                current_bri = light_attr["brightness"]
            current_kelvin = None
            if "color_temp" in light_attr:
                current_kelvin = color_temperature_mired_to_kelvin(light_attr["color_temp"])
            elif "rgb_color" in light_attr and light_attr["rgb_color"] != None:
                log.info("RGB_COLOR: " + str(light_attr["rgb_color"]))
                match = rgb_to_kelvin_via_lookup(light_attr["rgb_color"][0], light_attr["rgb_color"][1], light_attr["rgb_color"][2], for_entity=light_entity)
                if match != None:
                    current_kelvin = color_temperature_mired_to_kelvin(match["color_temp"])
                    # log.info("    # " + light_entity + ": current_kelvin: "+ str(current_kelvin))
            current_hue = None
            current_sat = None
            if "hs_color" in light_attr:
                hs_color = light_attr["hs_color"]
                current_hue, current_sat = huesat_to_huehs(hs_color)
            new_bri = 10
            if current_bri != None:
                new_bri = int(current_bri + ((final_bri - current_bri) * completed_level_after))
            new_kelvin = 2500
            if current_kelvin != None and final_kelvin != None:
                new_kelvin = int(current_kelvin + ((final_kelvin - current_kelvin) * completed_level_after))
            new_hs = None
            has_color = "hs" in light_attr["supported_color_modes"]
            has_ct = "color_temp" in light_attr["supported_color_modes"]
            if has_color and current_hue != None and current_sat != None and final_hue != None and final_sat != None:
                new_hue = int(current_hue + ((final_hue - current_hue) * completed_level_after))
                new_sat = int(current_sat + ((final_sat - current_sat) * completed_level_after))
                new_hs = hue_hs_to_huesat(new_hue, new_sat)
            light.turn_on(entity_id=light_entity, brightness_step=0) # See info above, used to be sure the light is "freed up" to receive new commands
            # Another note-to-self: It seems that changing brightness AND color at the same time does not go down well at all. So I probably need to do a part A, part B exchange back and forth
            change_color = current_step % 2 == 0 # We change the color on even steps
            if change_color and new_hs != None:
                log.debug("    # " + light_entity + ": fading to new color " + str(new_hs))
                light.turn_on(entity_id=light_entity, hs_color=new_hs, transition=fade_time)
            elif change_color and new_kelvin != None:
                log.debug("    # " + light_entity + ": fading to new color temperature " + str(new_kelvin) + "K")
                light.turn_on(entity_id=light_entity, kelvin=new_kelvin, transition=fade_time)
            else:
                log.debug("    # " + light_entity + ": fading to brightness " + str(new_bri))
                if(new_bri == None):
                    log.warning("Missing new_bri")
                else:
                    light.turn_on(entity_id=light_entity, brightness=new_bri, transition=fade_time)
        if elapsed_time + fade_time < full_fade_time:
            wait_time = fade_time + 1 # Let there be a slight delay before the next run
            log.debug("  > " + room + ": Waiting " + str(wait_time) + " seconds before starting next step: #" + str(current_step + 1))
            task.sleep(wait_time)
            pyscript.trigger_for_room_if_active_ikea(dataset=dataset, room=room, elapsed_time=elapsed_time + wait_time, current_step=current_step + 1, override_time=override_time, index=index)
        else:
            log.info("  > " + room + ": Fade completed at step #" + str(current_step))

@service
def ikea_test():
    current_trans = state.getattr("pyscript.huetrans_fastelys_dag")
    if "IKEA" in current_trans:
        # light.turn_on(entity_id="light.kjokken_hylle", kelvin=2900, brightness=255)
        # pyscript.trigger_for_room_if_active_ikea(dataset=current_trans["IKEA"], room="light.gang_nede_vindu")
        # hs_to_kelvin()
        data = state.getattr("light.gang_nede_vindu")
        state_rgb = data["rgb_color"]
        # match = rgb_to_kelvin_via_lookup(state_rgb[0], state_rgb[1], state_rgb[2])
        match = rgb_to_kelvin_via_lookup(255, 59, 2, for_entity="light.gang_nede_vindu")
        current_kelvin = None
        if match != None:
            current_kelvin = color_temperature_mired_to_kelvin(match["color_temp"])
        log.info("current_kelvin: " + str(current_kelvin))

def rgb_to_kelvin_via_lookup(red, green, blue, for_entity):
    # Running this function and then doing another recursion of itself reached about 1250 in recursion depth, for some reason...
    sys.setrecursionlimit(1500)
    log.debug("recursionlimit temporarily increased to: " + str(sys.getrecursionlimit()))
    match = rgb_to_kelvin_via_lookup_inner(red, green, blue, for_entity=for_entity)
    sys.setrecursionlimit(1000)
    log.debug("recursionlimit changed back to: " + str(sys.getrecursionlimit()))
    return match

def rgb_to_kelvin_via_lookup_inner(red, green, blue, red_offset=0, green_offset=0, blue_offset=0, red_moving_up=True, green_moving_up=True, blue_moving_up=True, source_values=None, for_entity="unknown"):
    # if len(inspect.stack(0)) > 1000:
    #     log.info("Current recursion depth: "+ str(len(inspect.stack(0))))
    max_offset = 10
    if source_values == None:
        source_values = "red: " + str(red) + ", green: " + str(green) + ", blue: " + str(blue)
    query = "WHERE [red]=" + str(red) + " AND [green]=" + str(green) + " AND [blue]=" + str(blue)
    # log.info(query)
    matches = database_services.run_select_query("*", "[mired_lookup]", query)
    # log.info("Match count: "+ str(len(matches)))
    should_quit = False
    if red_offset > max_offset or green_offset > max_offset or blue_offset > max_offset:
        log.debug("    # " + for_entity + ": Reached top. red_offset: " + str(red_offset) + ", green_offset: " + str(green_offset) + ", blue_offset: " + str(blue_offset))
        # Reset RGB-values
        red = red - red_offset
        blue = blue - blue_offset
        green = green - green_offset
        # Reset offsets
        red_offset = 0
        green_offset = 0
        blue_offset = 0
        # Turn around the search
        red_moving_up = False
        green_moving_up = False
        blue_moving_up = False
    elif red_offset < (-1 * max_offset) or green_offset < (-1 * max_offset) or blue_offset < (-1 * max_offset):
        log.debug("    # " + for_entity + ": Reached bottom. red_offset: " + str(red_offset) + ", green_offset: " + str(green_offset) + ", blue_offset: " + str(blue_offset))
        min_blue, min_green, max_blue, max_green = database_services.run_select_query("MIN([blue]) AS [min_blue], MIN([green]) AS [min_green], MAX([blue]) AS [max_blue], MAX([green]) AS [max_green]", "[mired_lookup]")[0].values()
        # Reset RGB-values
        red = red - red_offset
        blue = blue - blue_offset
        green = green - green_offset
        # log.info("Green: " + str(green))
        # log.info("Blue: " + str(blue))
        green_above = green > max_green
        green_below = green < min_green
        blue_above = blue > max_blue
        blue_below = blue < min_blue
        if green_above:
            green = max_green
        if green_below:
            green = min_green
        if blue_above:
            blue = max_blue
        if blue_below:
            blue = min_blue
        # Restart search with values we expect to hit something
        if green_above or blue_above or green_below or blue_below:
            log.debug("    # " + for_entity + ": Could not find an exact match. Restarting search with values we expect to hit something. " + "red: " + str(red) + ", green: " + str(green) + ", blue: " + str(blue) + " - original values was " + source_values)
            return rgb_to_kelvin_via_lookup_inner(red, green, blue, source_values=source_values, for_entity=for_entity)
        if green_above and blue_above:
            log.debug("    # " + for_entity + ": Both was above expected range")
        if green_below and blue_below:
            log.debug("    # " + for_entity + ": Both was below expected range")
        if not green_above and not green_below:
            log.debug("    # " + for_entity + ": Green was within range")
        else:
            log.debug("    # " + for_entity + ": Green was outside range")
        if not blue_above and not blue_below:
            log.debug("    # " + for_entity + ": Blue was within range")
        else:
            log.debug("    # " + for_entity + ": Blue was outside range")
        should_quit = True
        log.info("    # " + for_entity + ": Gone through entire search spectrum and now giving up. Value we were searching for was " + source_values)
        matches = database_services.run_select_query("*", "[mired_lookup]")
    moving_up = green_moving_up # Until we finish this bit...
    if len(matches) > 0:
        return matches[0]
    elif should_quit:
        return None
    else:
        new_offset = 1
        if not moving_up:
            new_offset = -1
        value_offset = new_offset
        if (moving_up and green_offset > blue_offset) or (not moving_up and green_offset < blue_offset):
            if blue > 254 or blue < 1:
                value_offset = 0
            return rgb_to_kelvin_via_lookup_inner(red, green, blue + value_offset, red_offset, green_offset, blue_offset + new_offset, red_moving_up, green_moving_up, blue_moving_up, source_values, for_entity=for_entity)
        else:
            if green > 254 or green < 1:
                value_offset = 0
            return rgb_to_kelvin_via_lookup_inner(red, green + value_offset, blue, red_offset, green_offset + new_offset, blue_offset, red_moving_up, green_moving_up, blue_moving_up, source_values, for_entity=for_entity)

def old_code():
    log.info("Just for folding")
    # @service
    # def ikea_test_get_kelvin_table():
    #     # database_services.create_mired_lookup()
    #     wait_time = 0.2
    #     start_mired = 256
    #     end_mired = 454
    #     # end_mired = 255
    #     lookup_table = {}
    #     for mired in range(start_mired, end_mired + 1):
    #         light.turn_on(entity_id="light.gang_nede_vindu", color_temp=mired)
    #         attr = state.getattr("light.gang_nede_vindu")
    #         lookup_table[mired] = {
    #             "hs_color": attr["hs_color"],
    #             "rgb_color": attr["rgb_color"],
    #             "xy_color": attr["xy_color"]
    #         }
    #         database_services.add_mired_lookup(mired, attr["hs_color"][0], attr["hs_color"][1], attr["rgb_color"][0], attr["rgb_color"][1], attr["rgb_color"][2], attr["xy_color"][0], attr["xy_color"][1])
    #         task.sleep(wait_time)
    #     log.info(lookup_table)

    # def hs_to_kelvin():
    #     # rgb = [255, 150, 50] # ca. 2300
    #     data = state.getattr("light.gang_nede_vindu")
    #     state_rgb = data["rgb_color"]
    #     state_xy = data["xy_color"]
    #     state_mired = data["color_temp"]
    #     kelvin = RGB_To_Kelvin(state_rgb[0], state_rgb[1], state_rgb[2])
    #     cct = xy_to_kelvin(state_xy[0], state_xy[1])
    #     mired = calculate_PhillipsHueCT_withCCT(cct)
    #     log.info("state_rgb: " + str(state_rgb))
    #     log.info("kelvin: " + str(kelvin))
    #     log.info("cct: " + str(cct))
    #     log.info("mired: " + str(mired) + " (state says: " + str(state_mired) + ")")
    #     # color_temperature_to_rgb(color_temperature_kelvin)

    # def xy_to_kelvin2(x, y):
    #     u = 4*x / (-2*x+12*y+3)
    #     v = 6*y / (-2*x+12*y+3)
    #     return None


    # def xy_to_kelvin(x, y):
    #     #x = 0.312708; y = 0.329113
    #     n = (x-0.3320)/(0.1858-y)
    #     cct = 437.0*n*n*n + 3601.0*n*n + 6861.0*n + 5517.0
    #     return cct

    # def calculate_PhillipsHueCT_withCCT(cct):
    #     if cct>6500.0:
    #         return 2000.0/13.0
    #     if cct<2000.0:
    #         return 500.0;
    #     # return (float) (1 / cct * 1000000); // same as..
    #     return 1000000 / cct

    # def RGB_To_Kelvin(red, green, blue):
    #     red, green, blue = [color / 255 for color in [red, green, blue]]
    #     # Wide RGB D65 https://gist.github.com/popcorn245/30afa0f98eea1c2fd34d
    #     X = red * 0.649926 + green * 0.103455 + blue * 0.197109
    #     Y = red * 0.234327 + green * 0.743075 + blue * 0.022598
    #     Z = red * 0.000000 + green * 0.053077 + blue * 1.035763

    #     # CIEXYZ D65 https://www.image-engineering.de/library/technotes/958-how-to-convert-between-srgb-and-ciexyz
    #     # X = red * 0.4124564 + green * 0.3575761 + blue * 0.1804375
    #     # Y = red * 0.2126729 + green * 0.7151522 + blue * 0.0721750
    #     # Z = red * 0.0193339 + green * 0.1191920 + blue * 0.9503041

    #     x = X / (X + Y + Z)
    #     y = Y / (X + Y + Z)
    #     n = (x - 0.3366) / (y - 0.1735)
    #     CCT = (-949.86315 + 6253.80338 * math.e**(-n / 0.92159) +
    #            28.70599 * math.e**(-n / 0.20039) +
    #            0.00004 * math.e**(-n / 0.07125))
    #     n = (x - 0.3356) / (y - 0.1691) if CCT > 50000 else n
    #     CCT = 36284.48953 + 0.00228 * math.e**(-n / 0.07861) + (
    #         5.4535 * 10**-36) * math.e**(-n / 0.01543) if CCT > 50000 else CCT
    #     return CCT

def color_temperature_kelvin_to_mired(kelvin_temperature: float) -> int:
    """Convert degrees kelvin to mired shift."""
    return math.floor(1000000 / kelvin_temperature)

def color_temperature_mired_to_kelvin(mired_temperature: int) -> float:
    """Convert mired shift to degrees kelvin."""
    if mired_temperature == None:
        log.warning("Missing mired_temperature")
        # traceback.print_stack()
        return 2500
    return math.floor(1000000 / mired_temperature)

def hue_hs_to_huesat(HueColor: int, HueSaturation: Int) -> "list[int]":
    hue = (HueColor / 65535) * 360
    if hue > 360:
        hue = 360
    sat = (HueSaturation / 255) * 100
    if sat > 100:
        sat = 100
    return [hue, sat]

def huesat_to_huehs(huesat: "list[int]") -> "tuple[int, int]":
    if huesat == None:
        log.warning("No huesat, setting to test values")
        huesat = [1,1]
    HueColor = int((huesat[0] / 360) * 65535)
    HueSaturation = int((huesat[1] / 100) * 255)
    return HueColor, HueSaturation
