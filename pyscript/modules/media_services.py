import logging
import json

_LOGGER = logging.getLogger(__name__)

def getMediaPlaySortKey(mediaPlayer, castDict):
    return ""

def getPlayingEntity(lookfor="both"):
    castDevices = state.getattr("sensor.chromecast_devices")["devices"]
    castDict = {}
    for device in castDevices:
        castDict[device["name"]] = { "is_group": device["model_name"] == "Google Cast Group" }
    allMediaPlayers = []
    massMediaPlayers = []
    use_spotcast = state.get("input_boolean.use_spotcast") == "on"
    for mediaPlayerName in state.names(domain="media_player"):
        player = state.getattr(mediaPlayerName)
        if "friendly_name" in player:
            deviceName = state.getattr(mediaPlayerName)["friendly_name"]
            is_group = (deviceName in castDict and castDict[deviceName]["is_group"]) or deviceName == "Godehol"
            sort_key = "0" + deviceName if is_group else "1" + deviceName
            # use_spotcast
            if use_spotcast and "mass_" in mediaPlayerName:
                continue
            allMediaPlayers.append({ "entity_id": mediaPlayerName, "friendly_name": deviceName, "is_group": is_group, "sortKey": sort_key, "state": state.get(mediaPlayerName) })
            if "mass_" in mediaPlayerName:
                massMediaPlayers.append({ "entity_id": mediaPlayerName, "friendly_name": deviceName, "is_group": is_group, "sortKey": sort_key, "state": state.get(mediaPlayerName) })
        else:
            log.info(state.getattr(mediaPlayerName))
    allMediaPlayers = sorted(allMediaPlayers, key=lambda i:i["sortKey"], reverse=False)
    playingEntity = None
    pausedEntity = None
    # Look for MASS entities first
    for mediaPlayer in massMediaPlayers:
        if mediaPlayer["state"] == "playing":
            playingEntity = mediaPlayer
            break
        elif mediaPlayer["state"] == "paused" and pausedEntity == None:
            pausedEntity = mediaPlayer
    if playingEntity == None:
        for mediaPlayer in allMediaPlayers:
            if mediaPlayer["state"] == "playing":
                playingEntity = mediaPlayer
                break
            elif mediaPlayer["state"] == "paused" and pausedEntity == None:
                pausedEntity = mediaPlayer
    # Look for other entities if no MASS entity was found playing
    if (lookfor=="both" or lookfor=="playing") and playingEntity is not None:
        _LOGGER.debug("Found playing entity: " + playingEntity["entity_id"])
        return playingEntity["entity_id"], playingEntity["state"]
    elif (lookfor=="both" or lookfor=="paused") and pausedEntity is not None:
        _LOGGER.debug("Found paused entity: " + pausedEntity["entity_id"])
        return pausedEntity["entity_id"], pausedEntity["state"]
    else:
        _LOGGER.debug("No playing entity found")
        return None, "idle"

def getPlayingEntity_old():
    defaultEntity = "media_player.godehol"
    inGroup = ['media_player.badet' , 'media_player.fm', 'media_player.kjokkenet', 'media_player.kontoret']
    playState = "playing"
    playingEntity = None
    spotifyDetails = state.getattr(media_player.spotify_gramatus)
    _LOGGER.debug("Spotify status details: %s",spotifyDetails)
    try:
        playingSource = spotifyDetails["source"]
        _LOGGER.debug("Spotify is playing on: %s",playingSource)
        allMediaPlayers = state.names(domain="media_player")
        for mediaPlayer in allMediaPlayers:
            if state.getattr(mediaPlayer)["friendly_name"] == playingSource:
                playingEntity = mediaPlayer
        if playingEntity is not None:
            _LOGGER.debug("Found entity by friendly name: %s",playingEntity)
    except Exception as e:
        _LOGGER.error("Something went wrong:"+str(e))

    _LOGGER.debug("Currently playing entity: %s",playingEntity)
    if playingEntity is None:
        _LOGGER.debug("Found no currently playing entity, will start playing on default entity")
        playingEntity = defaultEntity
    else:
        _LOGGER.debug("Will change currently playing content on entity: %s",playingEntity)
    return playingEntity
