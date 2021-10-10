# Testing my own hue api component
import aiohue
import logging
import async_timeout
from homeassistant.helpers import aiohttp_client,entity_registry
import attr
import aiohttp
import datetime

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
    _LOGGER.info("Temperature: " + str(current_temp) + ", Target: " + str(target_temp) + ", Turning " + target_state + ": " + ",".join(data["switches"]))
    for switch in data["switches"]:
        # _LOGGER.info("  > turning " + target_state + " " + switch)
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
    _LOGGER.info("This method is no longer used, returning")
    return
    url = 'http://'+pyscript.config["hue_ip"]+'/api/'+pyscript.config["hue_user"]+'/sensors/143/state'
    body = '{"status": 1}'
    async with aiohttp.ClientSession() as session:
        async with session.put(url,data=body) as response:
            _LOGGER.debug("Response from Hue: Status "+str(response.status)+", reply: "+response.text())

# bzJVKN6HRpYcaaw
@service
def turn_on_scene_by_id(scene_id, group_id=None, transitionhours=0, transitionmins=0, transitionsecs=0, transitionms=400, no_logging=False):
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
        example: 2
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
    bridge = get_bridge()

    group = None
    match_count = 0
    if(group_id != None):
        for grp in bridge.groups.values():
            if grp.name == friendly_name:
                match_count = match_count + 1
                group = grp
                # _LOGGER.info("Found match: " + grp.name + ", details:")
                # _LOGGER.info(grp)
    if group is None:
        group = bridge.groups.get_all_lights_group()
    if match_count > 1:
        _LOGGER.warning("Found multiple matches with name: " + friendly_name + ", check bridge for e.g. zones with duplicate names")
    scene = None
    for scn in bridge.scenes.values():
        # _LOGGER.info(scn)
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
    # _LOGGER.debug("Running script")
    for entity_id in state.names(domain="roomtoggles"):
        room_state = state.get(entity_id)
        # _LOGGER.debug(entity_id + " state: " + room_state)
        if(room_state == "on"):
            # _LOGGER.debug(entity_id + " is selected")
            for group in state.getattr(entity_id)["rooms"]:
                group_name = state.getattr(group)["friendly_name"]
                # _LOGGER.debug("Related group: " + str(group_name))
                scene_name = state.getattr(scene_entity)["scene_name"]
                # _LOGGER.debug("Scene name: " + str(scene_name))
                hue.hue_activate_scene(group_name=group_name,scene_name=scene_name)
                #_LOGGER.debug("Toggles: " + str(scene_toggles))
                #_LOGGER.debug("Selected toggle: " + str(scene_toggles[scene_name]))
                for entity in state.names(domain="huescenes"):
                    #input_boolean.turn_off(entity_id="input_boolean."+scene_toggles[name])
                    state.set(entity,value = "off")
                state.set(scene_entity,value = "on")
                #input_boolean.turn_on(entity_id="input_boolean."+scene_entity.friendly_name)

def get_bridge():
    bridge = aiohue.Bridge(
        pyscript.config["hue_ip"],
        username=pyscript.config["hue_user"],
        websession=aiohttp_client.async_get_clientsession(hass),
    )
    """Create a bridge object and verify authentication."""
    # Initialize bridge (and validate our username)
    try:
        with async_timeout.timeout(10):
            if not bridge.username:
                _LOGGER.error("Username not set in bridge")
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
