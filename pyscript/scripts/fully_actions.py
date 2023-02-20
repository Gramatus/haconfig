import aiohttp
import asyncio
import logging
import urllib
from yarl import URL
import requests
import time
import datetime

_LOGGER = logging.getLogger(__name__)

@service
def fully_set_wifi_off_between(timeoff, timeon, device):
    """yaml
name: Fully device WiFi off between
fields:
    timeoff:
        description: Time to turn WiFi off
        required: true
        example: 21:10:00
        selector:
            time:
    timeon:
        description: Time to turn WiFi on
        required: true
        example: 21:10:00
        selector:
            time:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett1
        selector:
            entity:
                domain: fully
"""
    ip = state.getattr(device)["ip"]
    timeOffParts = timeoff.split(":")
    timeOnParts = timeon.split(":")
    queryParams = urllib.parse.quote_plus("intent:hourOff:"+timeOffParts[0]+";minuteOff:"+timeOffParts[1]+";hourOn:"+timeOnParts[0]+";minuteOn:"+timeOnParts[1]+"#Intent;launchFlags=0x10000000;component=com.gramatus.torgeirswificontroller/.MainActivity;end")
    fully_action(ip,"loadUrl","&url="+queryParams)

@service
def fully_set_wakeup_alarm(playlistID,device):
    """yaml
name: Set alarm to wakeup
fields:
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
    fully_set_alarm(time=input_datetime.vekking,playlistID=playlistID,device=device)

@service
def fully_set_backup_wakeup_alarm(device):
    """yaml
name: Set backup alarm to wakeup
fields:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
"""
    wakeuptime = time.strptime(state.get("input_datetime.vekking"),"%H:%M:%S")
    wakeuptime = datetime.datetime.strptime(state.get("input_datetime.vekking"),"%H:%M:%S") + datetime.timedelta(minutes=30)
    _LOGGER.info("Setting backup alarm to 30 minutes later: " + wakeuptime.strftime("%H:%M:%S"))
    fully_set_alarm(time=wakeuptime.strftime("%H:%M:%S"),playlistID="",device=device)

@service
async def fully_set_alarm(time,device,playlistID=None,screenBrightness=None,showAlarmTime=30,turnOffAfter=True):
    """yaml
name: Set alarm
fields:
    time:
        description: Time to start alarm
        required: true
        example: 23:59:59
        selector:
            time:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
    playlistID:
        description: ID of playlist to start
        required: false
        example: 37i9dQZF1DWVpjAJGB70vU
        selector:
            text:
    screenBrightness:
        description: Brightness level
        required: false
        example: 100
        selector:
            number:
                min: 0
                max: 255
                mode: box
                step: 1
    showAlarmTime:
        description: Time to show the alarm app on the screen (so you can see the result)
        required: false
        example: 30
        selector:
            number:
                min: 0
                max: 120
                mode: box
                step: 15
    turnOffAfter:
        description: If true (default), the screen will turn off after. If false it will return to fully (it will also return to fully if the screen turns off, but you will not see that)
        required: false
        example: true
        selector:
            boolean:
"""
    ip = state.getattr(device)["ip"]
    timeParts = time.split(":")
    if screenBrightness != None:
        fully_set_brightness(device,screenBrightness)
    fully_turn_on_screen(device=device)
    playlistID = None
    if playlistID:
        queryParams = urllib.parse.quote_plus("intent:playlistid:"+playlistID+";hour:"+timeParts[0]+";minute:"+timeParts[1]+"#Intent;launchFlags=0x10000000;component=com.gramatus.setalarm/.MainActivity;end")
    else:
        queryParams = urllib.parse.quote_plus("intent:hour:"+timeParts[0]+";minute:"+timeParts[1]+"#Intent;launchFlags=0x10000000;component=com.gramatus.setalarm/.MainActivity;end")
    fully_action(ip,"loadUrl","&url="+queryParams)
    _LOGGER.info("Waiting for " + str(showAlarmTime) + " seconds")
    await asyncio.sleep(showAlarmTime)
    if turnOffAfter:
        fully_turn_off_screen(device=device)
    fully_to_foreground(device=device)

@service
def fully_dismiss_alarm(device):
    """yaml
name: Dismiss alarm
description: Dismisses the first alarm set by com.gramatus.setalarm
fields:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
"""
    ip = state.getattr(device)["ip"]
    queryParams = urllib.parse.quote_plus("intent:dismiss:true#Intent;launchFlags=0x10000000;component=com.gramatus.setalarm/.MainActivity;end")
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
    ip = state.getattr(device)["ip"]
    fully_action(ip,"screenOn")

@service
def fully_turn_off_screen(device):
    """yaml
name: Turn screen off for Fully Device
fields:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
"""
    ip = state.getattr(device)["ip"]
    fully_action(ip,"screenOff")

@service
def fully_to_foreground(device):
    """yaml
name: Load fully app in the foreground
fields:
    device:
        description: Device with Fully installed to contact
        required: true
        example: fully.nettbrett2
        selector:
            entity:
                domain: fully
"""
    ip = state.getattr(device)["ip"]
    fully_action(ip,"toForeground")

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
    ip = state.getattr(device)["ip"]
    fully_action(ip,"setStringSetting","&key=screenBrightness&value="+str(level))

async def fully_action(ip,action,params=""):
    pwd = pyscript.config["fully_pwd"]
    full_url = 'http://'+ip+':2323/?password='+pwd+'&type=json&cmd='+action+params
    encoded_url = URL(full_url,encoded=True)
    
    _LOGGER.debug(" > Calling: " + str(encoded_url))
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(encoded_url, allow_redirects=False) as response:
                _LOGGER.info("Response from fully: Status " + str(response.status) + ", reply: " + response.text())
    except Exception as e:
        _LOGGER.error("Failed to connect to Fully, error: " + str(e))
