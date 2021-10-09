# https://hacs-pyscript.readthedocs.io/en/latest/
import logging
from homeassistant.helpers import entity_platform
import asyncio
import spotify_services
import database_services

_LOGGER = logging.getLogger(__name__)

# Purpose of this script: playing podcast episodes from HA.
# This cannot be done with the normal spotify integration (I think), so I need to use spotcast - but I need to play it on whatever is already the active entity...

#data:
#  playlistid: 2VarjDoOdeWCYjCtLLdkSM
@service
async def play_playlist_random(playlistid, device=None, shuffle_type="Reuse shadow playlist"):
    """yaml
name: Play playlist with or without shuffle
description: Starts playing the playlist in shuffle mode on the "current" playing entity (default is media_player.kjokkenet)
fields:
    playlistid:
        description: ID of the playlist
        required: true
        example: 2pjB7wGkkoG9VYY8enMR5b
        selector:
            text:
    device:
        description: Media player (ChromeCast device) to play playlist on
        required: false
        example: media_player.spotify_gramatus
        selector:
            entity:
                domain: media_player
    shuffle_type:
        description: If the playlist should be shuffled
        required: false
        example: true
        selector:
            select:
                options:
                    - "No shuffle"
                    - "Reuse shadow playlist"
                    - "Update shadow playlist"
"""
    shuffle = True
    if shuffle_type == "No shuffle":
        shuffle = False
    delay_seconds = 2
    delay_seconds_start_spotcast = 5
    volume_fade_seconds = 10
    if playlistid == None:
        return
    if device == None:
        device = "media_player.godehol"
    player_attr = state.getattr(device)
    _LOGGER.info("  - Setting volume to 0 for " + player_attr["friendly_name"])
    media_player.volume_set(entity_id=device,volume_level=0)
    _LOGGER.info("  - Connecting to " + player_attr["friendly_name"] + " on spotcast")
    spotcast.start(entity_id=device)
    if shuffle and shuffle_type == "Reuse shadow playlist":
        _LOGGER.info("  - Getting ID for the related shuffled shadow playlist")
        playlistid, playlist_exists = spotify_services.ensure_shuffle_playlist_exists(playlistid)
        if not playlist_exists:
            shuffle_type = "Update shadow playlist"
    if shuffle and shuffle_type == "Update shadow playlist":
        _LOGGER.info("  - Updating the related shuffled shadow playlist")
        playlistid = spotify_services.ensure_shuffled_playlist(playlistid)
    else:
        # If we update the shadow playlist, that should take the required time - if not, we should wait some seconds
        _LOGGER.info("  > Waiting " + str(delay_seconds) + " seconds for connection to be ready")
        await asyncio.sleep(delay_seconds_start_spotcast)
    _LOGGER.info("  - Playing playlist on spotify: \"" + playlistid + "\"")
    pyscript.play_playlist_at_position(playlistid=playlistid, position=1)
    # is_playing = state.get("media_player.spotify_gramatus") == "playing"
    # if is_playing:
    #media_player.play_media(entity_id="media_player.spotify_gramatus", media_content_id="spotify:playlist:" + playlistid, media_content_type="playlist")
    _LOGGER.info("  - Waiting " + str(delay_seconds) + " more seconds")
    await asyncio.sleep(delay_seconds)
    # _LOGGER.info("Shuffling playlist and then starting volumne increase over " + str(volume_fade_seconds) + " seconds")
    _LOGGER.info(" - Starting volume increase over " + str(volume_fade_seconds) + " seconds")
    media_player.shuffle_set(entity_id="media_player.spotify_gramatus", shuffle=False) # Since we use shadow playlists for shuffling, we don't want another shuffle on top of our existing shuffle
    pyscript.volume_increase(fadein_seconds=volume_fade_seconds, device=device, initial_volume = 0.0, final_volume = 0.9)

@service
def play_playlist_random_old(playlistid):
    """yaml
name: Play playlist with shuffle (old version)
description: Starts playing the playlist in shuffle mode on the "current" playing entity (default is media_player.kjokkenet)
fields:
    playlistid:
        description: ID of the playlist
        required: true
        example: 5xddIVAtLrZKtt4YGLM1SQ
        selector:
            text:
"""
    if playlistid is not None:
        playingEntity, playState = getPlayingEntity()
        _LOGGER.debug("Calling spotcast.start")
        spotcast.start(entity_id=playingEntity,uri="spotify:playlist:"+playlistid,shuffle=True,random_song=True)

@service
def play_playlist_random_godehol(playlistid):
    """yaml
name: Play next episode
description: Starts playing the playlist in shuffle mode on the "Godehol" group
fields:
    playlistid:
        description: ID of the playlist
        required: true
        example: 5xddIVAtLrZKtt4YGLM1SQ
        selector:
            text:
"""
    if playlistid is not None:
        playingEntity, playState = getPlayingEntity()
        _LOGGER.debug("Calling spotcast.start")
        spotcast.start(entity_id="media_player.godehol",uri="spotify:playlist:"+playlistid,shuffle=True,random_song=True)

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
        playingEntity, playState = getPlayingEntity()
        _LOGGER.debug("Calling spotcast.start")
        spotcast.start(entity_id=playingEntity,uri="spotify:show:"+showid)

#data:
#  episodeid: 5Oma1LSh6prFDhbVmYXrXy
@service
def play_podcast_episode(episodeid):
    if episodeid is not None:
        playingEntity, playState = getPlayingEntity()
        _LOGGER.debug("Calling spotcast.start")
        spotcast.start(entity_id=playingEntity,uri="spotify:episode:"+episodeid)

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

@service
def ensure_shuffled_playlist(playlistid):
    """yaml
name: Ensure shuffled playlist
description: Creates or uppdates a "shadow" playlist that is shuffled according to my own custom algorithm
fields:
    playlistid:
        description: ID of the playlist
        required: true
        example: 2pjB7wGkkoG9VYY8enMR5b
        selector:
            text:
"""
    shuffle_playlist_id = spotify_services.ensure_shuffled_playlist(playlistid)
    # update_recently_played()
    # shuffle_playlist_id = ensure_shuffle_playlist_exists(playlistid)
    # update_shuffle_playlist(playlistid, shuffle_playlist_id)
    return shuffle_playlist_id

@service
def spotify_test():
    """yaml
name: Spotify test code
"""
    # truncate_playlist("6bA10TtiyuqQP0yEYnrd3X")
    #spotify_services.update_shuffle_playlist("2pjB7wGkkoG9VYY8enMR5b","6bA10TtiyuqQP0yEYnrd3X")
    # update_shuffle_playlist("3FVKcokzHla6424Cj74LzL","52w4nPUOmgaal2IMdL6Cqk")
    # playlistid = "78RaOXPHXD4zJWFRwzbuEI" # TP 23.5.19
    # playlistid = "2pjB7wGkkoG9VYY8enMR5b" # Alle gromlåter
    # playlistid = "3FVKcokzHla6424Cj74LzL" # Min våkneliste
    # playlist = spotify_get("/playlists/" + playlistid, False)
    # ensure_shuffle_playlist_exists(playlistid)
    # update_shuffle_playlist("78RaOXPHXD4zJWFRwzbuEI")
    spotify_services.update_recently_played()
    # spotify_services.skip_track()

@service
def play_playlist_at_position(playlistid,position):
    """yaml
name: Play playlist and start at the given position
fields:
    playlistid:
        description: ID of the playlist
        required: true
        example: 6bA10TtiyuqQP0yEYnrd3X
        selector:
            text:
    position:
        description: Position to start on
        required: false
        example: media_player.spotify_gramatus
        selector:
            number:
                min: 1
                mode: box
"""
    spotify_services.spotify_put("/me/player/play", {
        "context_uri": "spotify:playlist:"+playlistid,
        "offset": {
            "position": position-1
        }
    })

@service
def update_played_tracks_list():
    track_list = database_services.run_select_query("DISTINCT [Uri]","[played_tracks_list]", "WHERE [album] IS NULL OR [artist] IS NULL OR [play_lenght_ms] IS NULL OR [duration_ms] IS NULL")
    group_size = 50
    group_count = int(len(track_list)/group_size) + 1
    if len(track_list) == 0:
        group_count = 0
    _LOGGER.info(group_count)
    for i in range(group_count):
        track_ids = ""
        group = None
        if i == group_count - 1:
            group = track_list[group_size*i:]
        else:
            group = track_list[group_size*i:group_size*(i+1)]
        for track in group:
            track_ids += track["uri"].split(":")[2] + ","
        track_ids = track_ids[:-1]
        _LOGGER.info(track_ids)
        items = spotify_services.spotify_get("/tracks?ids=" + track_ids)
        for item in items:
            database_services.update_played_tracks_data(item)
