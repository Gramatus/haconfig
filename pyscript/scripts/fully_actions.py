import aiohttp
import asyncio
import logging
import urllib

_LOGGER = logging.getLogger(__name__)

@service
def fully_set_alarm(time,playlistID,device):
    """yaml
name: Turn screen on for Fully Device
fields:
    time:
        description: Time to start alarm
        required: true
        example: 23:59:59
        selector:
            time:
    playlistID:
        description: ID of playlist to start
        required: true
        example: 37i9dQZF1DWVpjAJGB70vU
        selector:
            text:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
"""
    ip = state.getattr(device)["ip"]
    _LOGGER.debug(ip)
    timeParts = time.split(":")
    _LOGGER.debug(timeParts[0])
    _LOGGER.debug(timeParts[1])

    queryParams = urllib.parse.quote_plus("intent:playlistid:"+playlistID+";hour:"+timeParts[0]+";minute:"+timeParts[1]+"#Intent;launchFlags=0x10000000;component=com.gramatus.setalarm/.MainActivity;end")
    _LOGGER.debug(queryParams)
    fully_action(ip,"loadUrl","&url="+queryParams)


@service
async def fully_open_app(pkg,device):
    """yaml
name: Open app on Fully device
description: Open NRK app
fields:
    pkg:
        description: Package to open
        required: true
        example: com.spotify.music
        selector:
            select:
                options:
                    - "Spotify: com.spotify.music"
                    - "NRK Radio: no.nrk.mobil.radio"
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
"""
    #ip = device.split(" ")[1].strip("())")
    ip = state.getattr(device)["ip"]
    pkg_split = pkg.split(": ")
    _LOGGER.debug(pkg_split)
    _LOGGER.debug(pkg_split[0])
    _LOGGER.debug(pkg_split[1])
    _LOGGER.debug("IP: %s",ip)
    fully_speak('<speak>Starter '+pkg_split[0]+'</speak>',device)
    fully_action(ip,"startApplication","&package="+pkg_split[1])
    fully_set_brightness(device,255)
    fully_turn_on_screen(device)

@service
async def fully_speak(text,device):
    """yaml
name: Make fully speak
description: Say something with TTS through fully
fields:
    text:
        description: What to say
        required: true
        example: <speak>Torgeir!<break time="3s"/>Du må stå opp!<break time="5s"/>Du må stå opp!<break time="10s"/>Du må stå opp!</speak>
        selector:
            text:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
"""
    ip = device.split(" ")[1].strip("())")
    _LOGGER.debug("IP: %s",ip)
    fully_action(ip,"textToSpeech","&locale=nb_NO&text="+text)

@service
def fully_turn_on_screen(device):
    """yaml
name: Turn screen on for Fully Device
fields:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
"""
    fully_action(ip,"screenOn")

@service
def fully_start_screensaver(device):
    """yaml
name: Start screensaver for Fully Device
fields:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
"""
    fully_action(ip,"startScreensaver")

# Level is 0 to 255 (?)
@service
def fully_set_brightness(device,level):
    """yaml
name: Set screen brightness for Fully Device
fields:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
    level:
        description: Brightness level
        required: true
        example: 100
        selector:
            number:
                min: 0
                max: 255
                mode: slider
                step: 1
"""
    fully_action(ip,"setStringSetting","&key=screenBrightness&value="+str(level))

async def fully_action(ip,action,params=""):
    pwd = pyscript.config["fully_pwd"]
    _LOGGER.debug("Triggering action: %s",action)
    async with aiohttp.ClientSession() as session:
        async with session.get('http://'+ip+':2323/?password='+pwd+'&type=json&cmd='+action+params) as response:
            _LOGGER.debug("Response from fully: Status "+str(response.status)+", reply: "+response.text())
