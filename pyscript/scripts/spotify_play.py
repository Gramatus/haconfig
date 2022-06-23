import logging
from homeassistant.helpers import entity_platform
import asyncio
import spotify_services
import database_services

# Purpose of this script: playing podcast episodes from HA.
# This cannot be done with the normal spotify integration (I think), so I need to use spotcast - but I need to play it on whatever is already the active entity...

@service
async def play_playlist_random(playlistid, device=None, shuffle_type="Update shadow playlist", fadein_seconds=10, final_volume=0.9, delay_seconds_start_spotcast=5):
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
    fadein_seconds:
        description: Number of seconds for the fadein
        required: true
        example: 60
        selector:
            number:
                min: 30
                max: 120
                mode: box
    final_volume:
        description: Volume to end at
        required: false
        example: 1.0
        selector:
            number:
                min: 0
                max: 1
                step: 0.01
                mode: box
"""
    shuffle = True
    if shuffle_type == "No shuffle":
        shuffle = False
    delay_seconds = 2
    if playlistid == None:
        return
    if device == None:
        device = "media_player.godehol"
    player_attr = state.getattr(device)
    log.info("  - Connecting to " + player_attr["friendly_name"] + " on spotcast with volume set to 0")
    spotify_uri = "spotify:playlist:" + playlistid
    if ":" in playlistid:
        spotify_uri = playlistid
    spotcast.start(entity_id=device, uri=spotify_uri, start_volume=0)
    source_playlistid = playlistid
    if shuffle and shuffle_type == "Reuse shadow playlist":
        # log.debug("  - Getting ID for the related shuffled shadow playlist")
        playlistid, playlist_exists = spotify_services.ensure_shuffle_playlist_exists(source_playlistid)
        if not playlist_exists:
            log.info("Shadow playlist not found, will create one")
            shuffle_type = "Update shadow playlist"
    if shuffle and shuffle_type == "Update shadow playlist":
        log.info("  - Updating the related shuffled shadow playlist")
        input_text.set_value(entity_id="input_text.shuffle_status", value="Shuffling: " + source_playlistid)
        playlistid = spotify_services.ensure_shuffled_playlist(source_playlistid)
        input_text.set_value(entity_id="input_text.shuffle_status", value="idle")
    # Stuff fails if the connection is not ready (i.e. Spotify is not aware of an active playback device)
    log.debug("  > Waiting " + str(delay_seconds_start_spotcast) + " seconds for connection to be ready")
    await asyncio.sleep(delay_seconds_start_spotcast)
    log.info("  - Playing playlist on spotify: \"" + playlistid + "\"")
    pyscript.play_playlist_at_position(playlistid=playlistid, position=1, shuffle=False) # Since we use shadow playlists for shuffling, we don't want another shuffle on top of our existing shuffle
    log.debug("  - Waiting " + str(delay_seconds) + " more seconds")
    await asyncio.sleep(delay_seconds)
    log.info(" - Starting volume increase over " + str(fadein_seconds) + " seconds")
    pyscript.volume_increase(fadein_seconds=fadein_seconds, device=device, initial_volume = 0.0, final_volume = final_volume)

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
        log.debug("Calling spotcast.start")
        spotcast.start(entity_id=playingEntity,uri="spotify:playlist:"+playlistid,shuffle=True,random_song=True)

@service
def play_playlist_random_godehol(playlistid):
    """yaml
name: Play a palylist randomly on Godehol (old code?)
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
        log.debug("Calling spotcast.start")
        spotcast.start(entity_id="media_player.godehol",uri="spotify:playlist:"+playlistid,shuffle=True,random_song=True)

@service
async def play_next_podcast_episode(showid, device=None):
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
    device:
        description: Media player (ChromeCast device) to play playlist on
        required: false
        example: media_player.spotify_gramatus
        selector:
            entity:
                domain: media_player
"""
    if showid is None:
        log.warning("No showid supplied")
        return
    if device == None:
        device = "media_player.godehol"
    log.info("Finding first episode that is not finished in show with id: " + showid)
    start_at = 0 # TODO: Save known current episode somewhere so I don't need to start looking at position #1
    offset_from_end = 0
    episodeToPlay = None
    reached_point = False
    loaded_episodes = 50
    show = spotify_services.spotify_get("/shows/" + showid + "?market=NO", ReturnRaw=True)
    total_episodes = show["total_episodes"]
    offset = 0
    descending = None
    while reached_point == False and loaded_episodes > 0:
        episodes = spotify_services.spotify_get("/shows/" + showid + "/episodes?offset=" + str(start_at) + "&limit=50&market=NO", GetAll=False)
        start_at = start_at + len(episodes)
        if descending == None:
            if len(episodes) > 2:
                descending = episodes[0]["release_date"] > episodes[1]["release_date"]
                if descending:
                    log.info("descending")
                else:
                    log.info("ascending")
            else:
                descending = False
        for episode in episodes:
            fully_played = episode["resume_point"]["fully_played"]
            # log.info(episode["name"] + ": " + str(fully_played))
            if descending:
                if not fully_played:
                    offset_from_end = offset_from_end + 1
                else:
                    episodeToPlay = episode
                    reached_point = True
                    break
            else:
                if fully_played:
                    offset = offset + 1
                    episodeToPlay = episode
                else:
                    reached_point = True
                    break
    if descending:
        offset = total_episodes - offset_from_end
    log.info("Last played episode #" + str(offset) + ": " + episodeToPlay["name"])
    spotify_uri = "spotify:show:"+showid
    # spotify_services.spotify_put("/me/player/play", {
    #     "context_uri": spotify_uri,
    #     "offset": {
    #         "position": offset
    #     }
    # })
    player_attr = state.getattr(device)
    log.info("  - Connecting to " + player_attr["friendly_name"] + " on spotcast with a rather random playlist since spotcast overrides my show selection")
    delay_seconds = 5
    spotcast_uri = "spotify:playlist:37i9dQZF1DX20xDs0SXeZu"
    spotcast.start(entity_id=device, uri=spotcast_uri)
    log.info("  > Waiting " + str(delay_seconds) + " seconds for connection to be ready")
    await asyncio.sleep(delay_seconds)
    log.info("  - Playing podcast on spotify: \"" + spotify_uri + "\"")
    pyscript.play_playlist_at_position(playlistid=spotify_uri, position=offset+1, shuffle=False)

@service
def play_podcast_episode(episodeid):
    """yaml
name: Play next episode
description: Plays the given podcast episode
fields:
    episodeid:
        description: ID of the episode to play
        required: true
        example: 5Oma1LSh6prFDhbVmYXrXy
        selector:
            text:
"""
    if episodeid is not None:
        playingEntity, playState = getPlayingEntity()
        log.debug("Calling spotcast.start")
        spotcast.start(entity_id=playingEntity,uri="spotify:episode:"+episodeid)

@service
def gramatus_test2(entity_id):
    log.debug("Testing my python skillz")
    log.debug("entity_id %s",entity_id)
    if entity_id is not None:
        inGroup = ['media_player.badet' , 'media_player.fm', 'media_player.kjokkenet', 'media_player.kontoret']
        playState = "playing"
        spotifyState = media_player.spotify_gramatus
        spotifyDetails = state.getattr(media_player.spotify_gramatus)
        log.debug("Spotify status: %s",spotifyState)
        log.debug("Spotify status details: %s",spotifyDetails)
        log.debug("Spotify is playing: %s",spotifyState.media_content_id)
        if spotifyState == playState:
            log.debug("Spotify is already playing, will only switch where it plays")
        else:
            log.debug("Spotify is not playing, will also start playing stuff")
        group_state = media_player.Godehol
        if entity_id == "media_player.Godehol":
            if group_state == playState:
                log.debug("Godehol was selected, but is already playing")
            else:
                log.debug("Godehol was selected, and is not playing")
        elif entity_id in inGroup and group_state == playState:
            log.debug("Godehol is playing and the selected entity is part of that group")
        elif state.get(entity_id) == playState:
            log.debug("%s is already playing",entity_id)
        else:
            log.debug("Seems the request is to do something new")
        log.debug("entity_id state: %s",state.get(entity_id))
        service_data = {"entity_id": entity_id,"uri":"spotify:playlist:0C2U8SFwZ3Y9bBjVa2KSMx"}
        log.debug("service_data %s",service_data)
        log.debug("Calling spotcast.start")
        #spotcast.start(entity_id=entity_id,uri="spotify:playlist:0C2U8SFwZ3Y9bBjVa2KSMx")
        log.debug("DONE")

@service
def ensure_shuffled_playlist(playlistid, consider_play_date=True):
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
    consider_play_date:
        description: Should recently played tracks be played later?
        required: false
        example: true
        selector:
            boolean:
"""
    input_text.set_value(entity_id="input_text.shuffle_status", value="Shuffling: " + playlistid)
    shuffle_playlist_id = spotify_services.ensure_shuffled_playlist(playlistid, consider_play_date)
    input_text.set_value(entity_id="input_text.shuffle_status", value="idle")
    return shuffle_playlist_id

@service
def spotify_test():
    """yaml
name: Spotify test code
"""
    spotify_services.update_recently_played()
    # spotify_services.skip_track()

@service
def play_playlist_at_position(playlistid, position, shuffle=False):
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
    shuffle:
        description: Should shuffle be active?
        required: false
        example: false
        selector:
            boolean:
"""
    spotify_uri = "spotify:playlist:" + playlistid
    if ":" in playlistid:
        spotify_uri = playlistid
    spotify_services.spotify_put("/me/player/play", {
        "context_uri": spotify_uri,
        "offset": {
            "position": position-1
        }
    })
    spotify_services.spotify_put("/me/player/shuffle?state=" + str(shuffle))

@service
def update_played_tracks_list():
    track_list = database_services.run_select_query("DISTINCT [Uri]","[played_tracks_list]", "WHERE [album] IS NULL OR [artist] IS NULL OR [play_lenght_ms] IS NULL OR [duration_ms] IS NULL")
    group_size = 50
    group_count = int(len(track_list)/group_size) + 1
    if len(track_list) == 0:
        group_count = 0
    log.info(group_count)
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
        log.info(track_ids)
        items = spotify_services.spotify_get("/tracks?ids=" + track_ids)
        for item in items:
            database_services.update_played_tracks_data(item)
