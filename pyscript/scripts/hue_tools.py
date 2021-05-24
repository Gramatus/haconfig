# Testing my own hue api component
import aiohue
import logging
import async_timeout
from homeassistant.helpers import aiohttp_client,entity_registry
import attr

_LOGGER = logging.getLogger(__name__)

# bzJVKN6HRpYcaaw
@service
def turn_on_scene_by_id(scene_id,group_id=None):
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
"""
    friendly_name=None
    if(group_id != None):
        friendly_name=state.getattr(group_id)["friendly_name"]
    bridge = get_bridge()

    group = None
    if(group_id != None):
        for grp in bridge.groups.values():
            if grp.name == friendly_name:
                group = grp
    if group is None:
        group = bridge.groups.get_all_lights_group()
    _LOGGER.debug("Group name: %s",group.name)
    scene = None
    for scn in bridge.scenes.values():
        if scn.id == scene_id:
            scene = scn
    if(scene == None):
        _LOGGER.warning("No scene found with ID: %s",scene_id);
        return;
    _LOGGER.debug("Scene name: %s",scene.name)
    group.set_action(scene=scene.id)


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
