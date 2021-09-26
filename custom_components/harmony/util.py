"""The Logitech Harmony Hub integration utils."""
import logging
import aioharmony.exceptions as harmony_exceptions
from aioharmony.harmonyapi import HarmonyAPI

from homeassistant.const import CONF_NAME

_LOGGER = logging.getLogger(__name__)

def find_unique_id_for_remote(harmony: HarmonyAPI):
    _LOGGER.info("Torgeir: util.py")
    # _LOGGER.info(harmony)
    _LOGGER.info("HUB ID: \"" + str(harmony.hub_id) + "\"")
    """Find the unique id for both websocket and xmpp clients."""
    if harmony.hub_id is not None:
        return str(harmony.hub_id)

    _LOGGER.info("Fallback HUB ID: \"" + harmony.config["global"]["timeStampHash"].split(";")[-1] + "\"")
    # fallback timeStampHash if Hub ID is not available
    return harmony.config["global"]["timeStampHash"].split(";")[-1]


def find_best_name_for_remote(data: dict, harmony: HarmonyAPI):
    """Find the best name from config or fallback to the remote."""
    # As a last resort we get the name from the harmony client
    # in the event a name was not provided.  harmony.name is
    # usually the ip address but it can be an empty string.
    if CONF_NAME not in data or data[CONF_NAME] is None or data[CONF_NAME] == "":
        return harmony.name

    return data[CONF_NAME]


async def get_harmony_client_if_available(ip_address: str):
    """Connect to a harmony hub and fetch info."""
    harmony = HarmonyAPI(ip_address=ip_address)

    try:
        if not await harmony.connect():
            await harmony.close()
            return None
    except harmony_exceptions.TimeOut:
        return None

    await harmony.close()

    return harmony
