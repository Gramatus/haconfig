import aiohue
import logging
import async_timeout
from homeassistant.helpers import aiohttp_client,entity_registry
import attr
import aiohttp
import datetime
import re
import json

_LOGGER = logging.getLogger(__name__)

entity_prefix_thermo = "thermostat_"

state.persist("pyscript." + entity_prefix_thermo + "kontor", "off", {
    "icon": "mdi:thermostat-box",
    "device_class": "thermostat",
    "friendly_name": "Innstillinger for termostat på kontoret",
    "sensor_entity": "sensor.kontoret_temperature",
    "target_entity": "input_number.termostat_kontoret",
    "switches": [
        "light.termostat_kontoret"
    ]
})

@service
def hue_event_trigger(trigger): # , event, hue_event, entity_id, switch_event_type, switch_id, switch_event_button_id
    """yaml
name: Trigger remote actions
fields:
    trigger:
        description: Trigger data from an automation
        required: true
"""
    #log.info(trigger)
    # Convert the text version of the trigger data back to something we can load as a JSON object
    trigger = re.compile("(\".*)(')([^\"]*)(')(\")").sub('\g<1>\\\"\g<3>\\\"\g<5>',trigger)
    trigger = re.compile("(\s*)([^=\s]*?)(=)([^,>]*)").sub('\g<1>\"\g<2>\":\"\g<4>\"',trigger)
    trigger = re.compile("(<Event hue_event\[L\]:)([^>]*)(>)").sub('{\g<2>}',trigger)
    trigger = trigger.replace("'","\"")
    #log.info(trigger)
    # Load the JSON object and then get the event data
    trigger_data = json.loads(trigger)
    #log.info(trigger_data)
    event = trigger_data["event"]
    switch_id = event["id"].replace("_button", "")
    switch_event_button_id = int(event["subtype"])
    buttons = { 1: "On", 2: "DimUp", 3: "DimDown", 4: "Off" }
    # switch_button = buttons.get(switch_event // 1000)
    switch_button = buttons.get(switch_event_button_id)
    # initial_press: DON'T use this normally. It will trigger on ALL presses, whether short or long. Use short_release instead.
    # repeat: Triggers after the button has been held for about a second. Then (I believe) it will re-trigger (every second or half-second or something?), thus it can be used e.g. for dimming up while holding.
    # short_release: Triggers only if the button is released quickly
    # long_release: Triggers after a hold is done. Probably most useful for "finishing" tasks or something.
    switch_event_type = event["type"]
    # log.info("Hue Event triggered. switch_id: \"" + str(switch_id) + "\", switch_event_button_id: " + str(switch_event_button_id) + ", switch_button: " + str(switch_button) + ", switch_event_type: " + str(switch_event_type)) # + ", event_time: " + str(event_time)
    area_ids = []
    if switch_id == "bryterkontor":
        area_ids = ["kontor"]
    elif switch_id == "brytergang":
        area_ids = ["gang_nede", "kontor"]
    elif switch_id == "bryterkjokken":
        area_ids = ["kjokken"]
    elif switch_id == "brytersoverom":
        timer_id = "timer.natt_nedtelling"
        if switch_button == "DimUp" and switch_event_type == "short_release":
            pyscript.run_night_light(duration_mins=15)
        if switch_button == "DimDown" and switch_event_type == "short_release":
            pyscript.run_night_light(duration_mins=30)
        if switch_button == "Off" and switch_event_type == "short_release":
            if state.get(timer_id) == "active":
                timer.cancel(entity_id=timer_id)
    elif switch_id == "bryterkjeller":
        if switch_button == "On" and switch_event_type == "short_release":
            light.turn_on(entity_id="light.kjeller")
        if switch_button == "Off" and switch_event_type == "short_release":
            light.turn_off(entity_id="light.kjeller")
    if switch_button == "On" and switch_event_type == "short_release":
        for area_id in area_ids:
            pyscript.turn_on_ikea_lights_when_room_turned_on(area_id=area_id)
    elif switch_button == "Off" and switch_event_type == "short_release":
        for area_id in area_ids:
            pyscript.turn_off_ikea_lights_when_room_turned_off(area_id=area_id)
    # log.info("Done with event handling")

@service
def toggle_thermostat(thermostat):
    """yaml
name: Toggle
description: Turn on a Hue scene based on the scene ID (will use group 0 if no group is specified)
fields:
    thermostat:
        description: Entity with settings for this thermostat
        required: true
        example: pyscript.thermostat_kontor
        selector:
            entity:
                domain: pyscript
                device_class: thermostat
"""
    data = state.getattr(thermostat)
    current_temp = state.get(data["sensor_entity"])
    target_temp = state.get(data["target_entity"])
    target_state = "off" if current_temp > target_temp else "on"
    log.debug("Temperature: " + str(current_temp) + ", Target: " + str(target_temp) + ", Turning " + target_state + ": " + ",".join(data["switches"]))
    for switch in data["switches"]:
        if target_state == "off":
            light.turn_off(entity_id=switch)
        else:
            light.turn_on(entity_id=switch)
    state.set(thermostat, target_state)

@service
def start_wakeup_light():
    """yaml
name: Start wakeup light
description: Start the wakeup light routine
"""
    log.warning("This method is no longer used, returning")
    return
    url = 'http://'+pyscript.config["hue_ip"]+'/api/'+pyscript.config["hue_user"]+'/sensors/143/state'
    body = '{"status": 1}'
    async with aiohttp.ClientSession() as session:
        async with session.put(url,data=body) as response:
            log.debug("Response from Hue: Status "+str(response.status)+", reply: "+response.text())

@service
async def turn_on_scene_by_id(scene_id, group_id=None, transitionhours=0, transitionmins=0, transitionsecs=0, transitionms=400, no_logging=False):
    """yaml
name: Turn on scene by ID
description: Turn on a Hue scene based on the scene ID (will use group 0 if no group is specified)
fields:
    scene_id:
        description: ID of the scene to trigger
        required: true
        example: bzJVKN6HRpYcaaw
        selector:
            text:
    group_id:
        description: ID of group (if omitted, the "all lights group" will be used)
        required: false
        example: light.kontor
        selector:
            entity:
                domain: light
    transitionhours:
        description: Optional (default is 0). Number of hours for the transition to last. If the total time of the transition is above 1:49:13, it will be set to that.
        required: false
        example: 0
        selector:
            number:
                min: 0
                max: 2
                mode: box
                step: 1
    transitionmins:
        description: Optional (default is 0). Number of minutes for the transition to last. If the total time of the transition is above 1:49:13, it will be set to that.
        required: false
        example: 0
        selector:
            number:
                min: 0
                max: 60
                mode: box
                step: 1
    transitionsecs:
        description: Optional (default is 0). Number of seconds for the transition to last. If the total time of the transition is above 1:49:13, it will be set to that.
        required: false
        example: 0
        selector:
            number:
                min: 0
                max: 60
                mode: box
                step: 1
    transitionms:
        description: Optional (default is 400). Number of milliseconds for the transition to last.
        required: false
        example: 400
        selector:
            number:
                min: 0
                max: 1000
                mode: box
                step: 100
"""
    friendly_name=None
    if(group_id != None):
        friendly_name=state.getattr(group_id)["friendly_name"]
    async with get_bridge() as bridge:
        group = None
        match_count = 0
        if(group_id != None):
            for grp in bridge.groups.values():
                if grp.name == friendly_name:
                    match_count = match_count + 1
                    group = grp
        if group is None:
            group = bridge.groups.get_all_lights_group()
        if match_count > 1:
            _LOGGER.warning("Found multiple matches with name: " + friendly_name + ", check bridge for e.g. zones with duplicate names")
        scene = None
        for scn in bridge.scenes.values():
            if scn.id == scene_id:
                scene = scn
        if(scene == None):
            _LOGGER.warning("No scene found with ID: %s",scene_id);
            return;
        transition = int(round(((transitionhours*60*60)+(transitionmins*60)+(transitionsecs)+(transitionms/1000))*10,0))
        if not no_logging:
            _LOGGER.debug("Triggering scene. Group: " + group.name + ", Scene: " + scene.name + ", Transition time: " + str(datetime.timedelta(seconds=round(transition/10,1))) + " (submitted as: " + str(transition) + ")")
        group.set_action(scene=scene.id,transitiontime=transition)

@service
def toggle_room(room_entity):
    """yaml
name: Toggle room selector state
description: Toggle a room selector state between on/off
fields:
    room_entity:
        description: Name of the room toogle
        required: true
        example: huescenes.vanliglys
        selector:
            entity:
                domain: roomtoggles
"""
    current_state = state.get(room_entity)
    if(current_state == "on"):
        state.set(room_entity, value = "off")
        state.setattr(room_entity+".is_on", False)
    else:
        state.set(room_entity, value = "on")
        state.setattr(room_entity+".is_on", True)

@service
def turn_on_scene_for_active_rooms(scene_entity):
    """yaml
name: Turn on scene for active rooms
description: Turn on a Hue scene based on the scene name for active rooms (as defined in my input_booleans)
fields:
    scene_entity:
        description: Name of the scene to trigger
        required: true
        example: huescenes.vanliglys
        selector:
            entity:
                domain: huescenes
"""
    for entity_id in state.names(domain="roomtoggles"):
        room_state = state.get(entity_id)
        if(room_state == "on"):
            for group in state.getattr(entity_id)["rooms"]:
                group_name = state.getattr(group)["friendly_name"]
                scene_name = state.getattr(scene_entity)["scene_name"]
                hue.hue_activate_scene(group_name=group_name,scene_name=scene_name)
                for entity in state.names(domain="huescenes"):
                    state.set(entity, value = "off")
                state.set(scene_entity,value = "on")

async def get_bridge():
    bridge = aiohue.HueBridgeV1(
        pyscript.config["hue_ip"],
        app_key=pyscript.config["hue_user"],
    )
    """Create a bridge object and verify authentication."""
    # Initialize bridge (and validate our username)
    try:
        with async_timeout.timeout(10):
            await bridge.initialize()
    except (aiohue.LinkButtonNotPressed, aiohue.Unauthorized) as err:
        raise AuthenticationRequired from err
    except (
        asyncio.TimeoutError,
        client_exceptions.ClientOSError,
        client_exceptions.ServerDisconnectedError,
        client_exceptions.ContentTypeError,
    ) as err:
        raise CannotConnect from err
    except aiohue.AiohueException as err:
        LOGGER.exception("Unknown Hue linking error occurred")
        raise AuthenticationRequired from err
    return bridge
