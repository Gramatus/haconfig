# https://hacs-pyscript.readthedocs.io/en/latest/
import logging
from homeassistant.helpers import entity_platform
_LOGGER = logging.getLogger(__name__)

# Purpose of this script: playing podcast episodes from HA.
# This cannot be done with the normal spotify integration (I think), so I need to use spotcast - but I need to play it on whatever is already the active entity...

#data:
#  playlistid: 2VarjDoOdeWCYjCtLLdkSM
@service
def play_playlist_random(playlistid):
    if playlistid is not None:
        playingEntity = getPlayingEntity()
        _LOGGER.debug("Calling spotcast.start")
        spotcast.start(entity_id=playingEntity,uri="spotify:playlist:"+playlistid,shuffle=True,random_song=True)

#data:
#  showid: 2VarjDoOdeWCYjCtLLdkSM
@service
def play_next_podcast_episode(showid):
    """yaml
name: Play next episode
description: Plays the next unplayed episode (or the currently playing if one is not finnished) of the podcast with the given showid
fields:
    showid:
        description: ID of the show (part of url that can be found in spotify)
        required: true
        example: 2VarjDoOdeWCYjCtLLdkSM
        selector:
            text:
"""
    _LOGGER.debug("TODO: update code for handling episodes in __init__.py for spotcast / fork repository...")
    if showid is not None:
        playingEntity = getPlayingEntity()
        _LOGGER.debug("Calling spotcast.start")
        spotcast.start(entity_id=playingEntity,uri="spotify:show:"+showid)

#data:
#  episodeid: 5Oma1LSh6prFDhbVmYXrXy
@service
def play_podcast_episode(episodeid):
    if episodeid is not None:
        playingEntity = getPlayingEntity()
        _LOGGER.debug("Calling spotcast.start")
        spotcast.start(entity_id=playingEntity,uri="spotify:episode:"+episodeid)

@service
def getPlayingEntity():
    defaultEntity = "media_player.kjokkenet"
    inGroup = ['media_player.badet' , 'media_player.fm', 'media_player.kjokkenet', 'media_player.kontoret']
    playState = "playing"
    group_state = media_player.Godehol
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


@service
def gramatus_test2(entity_id):
    _LOGGER.debug("Testing my python skillz")
    _LOGGER.debug("entity_id %s",entity_id)
    if entity_id is not None:
        inGroup = ['media_player.badet' , 'media_player.fm', 'media_player.kjokkenet', 'media_player.kontoret']
        playState = "playing"
        spotifyState = media_player.spotify_gramatus
        spotifyDetails = state.getattr(media_player.spotify_gramatus)
        _LOGGER.debug("Spotify status: %s",spotifyState)
        _LOGGER.debug("Spotify status details: %s",spotifyDetails)
        _LOGGER.debug("Spotify is playing: %s",spotifyState.media_content_id)
        if spotifyState == playState:
            _LOGGER.debug("Spotify is already playing, will only switch where it plays")
        else:
            _LOGGER.debug("Spotify is not playing, will also start playing stuff")
        group_state = media_player.Godehol
        if entity_id == "media_player.Godehol":
            if group_state == playState:
                _LOGGER.debug("Godehol was selected, but is already playing")
            else:
                _LOGGER.debug("Godehol was selected, and is not playing")
        elif entity_id in inGroup and group_state == playState:
            _LOGGER.debug("Godehol is playing and the selected entity is part of that group")
        elif state.get(entity_id) == playState:
            _LOGGER.debug("%s is already playing",entity_id)
        else:
            _LOGGER.debug("Seems the request is to do something new")
        _LOGGER.debug("entity_id state: %s",state.get(entity_id))
        service_data = {"entity_id": entity_id,"uri":"spotify:playlist:0C2U8SFwZ3Y9bBjVa2KSMx"}
        _LOGGER.debug("service_data %s",service_data)
        _LOGGER.debug("Calling spotcast.start")
        #spotcast.start(entity_id=entity_id,uri="spotify:playlist:0C2U8SFwZ3Y9bBjVa2KSMx")
        _LOGGER.debug("DONE")
