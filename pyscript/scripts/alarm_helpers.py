import logging
import asyncio

_LOGGER = logging.getLogger(__name__)

@service
async def volume_increase():
    """yaml
name: Increase volume
description: Increase volume gradually
"""
    volume_level = 0.0
    _LOGGER.info("Setting volume to: "+str(volume_level))
    media_player.volume_set(entity_id="media_player.spotify_gramatus",volume_level=volume_level)
    fadein_seconds = 60
    fadein_steps = 20
    wait_seconds = fadein_seconds/fadein_steps
    _LOGGER.info("Step time: "+str(wait_seconds))
    for x in range(fadein_steps):
        volume_level=round(volume_level+0.05, 2)
        if(volume_level>1): volume_level=1
        await asyncio.sleep(wait_seconds)
        _LOGGER.info("Setting volume to: "+str(volume_level))
        media_player.volume_set(entity_id="media_player.spotify_gramatus",volume_level=volume_level)
    _LOGGER.info("Done, final volume is: "+str(volume_level))
