import logging
import spotify_token as st
import time
import datetime
from yarl import URL
import aiohttp
import json
import random
import urllib
import database_services

_LOGGER = logging.getLogger(__name__)

# Useful links:
# Console, for testing endpoints: https://developer.spotify.com/console/
# Web api reference: https://developer.spotify.com/documentation/web-api/reference/
# My app for playlists: https://developer.spotify.com/dashboard/applications/02f9211580d043bca8a97f2b99890337

state.persist("pyscript.temp_token","volatile", {
    "token": "none",
    "expires": None
})
# state.persist("pyscript.spotify_last_played","n/a", {})
state.persist("pyscript.spotify_shuffle_playlists","n/a", {})

spotify_username = "gramatus"

token_expires = state.getattr("pyscript.temp_token")["expires"]
token =  state.getattr("pyscript.temp_token")["token"]

sp_dc = pyscript.config["sp_dc"]
sp_key = pyscript.config["sp_key"]

async def get_spotify_token():
    try:
        global token, token_expires
        token, token_expires = task.executor(st.start_session, sp_dc, sp_key)
        expires = token_expires - int(time.time())
        _LOGGER.info("Got an updated token, it will expire in: " + str(datetime.timedelta(seconds=expires)))
        state.setattr("pyscript.temp_token.token", token)
        state.setattr("pyscript.temp_token.expires", token_expires)
    except:  # noqa: E722
        raise HomeAssistantError("Could not get spotify token")

async def ensure_token_valid():
    if float(token_expires) > time.time():
        return
    _LOGGER.debug("Token expired at: " + str(datetime.timedelta(seconds=token_expires - int(time.time()))) + ", will get a new token")
    get_spotify_token()

async def spotify_get(relative_url, dump_to_log=False, GetAll=True, MaxCount=1000, ReturnRaw=False):
    ensure_token_valid()
    full_url = "https://api.spotify.com/v1" + relative_url

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
    }
    
    items = []
    async with aiohttp.ClientSession() as session:
        has_more_data = True
        while has_more_data:
            encoded_url = URL(full_url,encoded=True)
            async with session.get(encoded_url, allow_redirects=False, headers=headers) as response:
                if response.status != 200:
                    _LOGGER.info(" > " + str(encoded_url) + ": Status "+str(response.status) + "Response from server:\n" + response.text())
                    return
                resp_json = response.json()
                # Used for debugging only
                # _LOGGER.info("From Spotify:\n" + response.text())
                # When there are no more results, the cursors property will be null (and items an empty array)
                cursor_text = ""
                if "cursors" in resp_json and resp_json["cursors"] != None:
                    if "after" in resp_json["cursors"] and "before" in resp_json["cursors"]:
                        cursor_text = ", This page goes from: " + datetime.datetime.utcfromtimestamp(int(resp_json["cursors"]["after"])/1000).strftime("%Y-%m-%d %H:%M:%S") + " to: " + datetime.datetime.utcfromtimestamp(int(resp_json["cursors"]["before"])/1000).strftime("%Y-%m-%d %H:%M:%S")
                    elif "after" in resp_json["cursors"]:
                        cursor_text = ", This page starts at: " + datetime.datetime.utcfromtimestamp(int(resp_json["cursors"]["after"])/1000).strftime("%Y-%m-%d %H:%M:%S")
                    elif "before" in resp_json["cursors"]:
                        cursor_text = ", This page ends at: " + datetime.datetime.utcfromtimestamp(int(resp_json["cursors"]["before"])/1000).strftime("%Y-%m-%d %H:%M:%S")
                _LOGGER.info(" > " + str(encoded_url) + ": Status "+str(response.status) + cursor_text)
                if ReturnRaw:
                    return resp_json
                elif "items" in resp_json:
                    # Probably a paged list of items
                    new_items = resp_json["items"]
                    items = items + new_items
                elif "playlists" in resp_json and "items" in resp_json["playlists"]:
                    # Probably a paged list of items
                    new_items = resp_json["playlists"]["items"]
                    items = items + new_items
                elif "uri" in resp_json:
                    # Return data has a single item (most items in Spotify have a uri)
                    has_more_data = False
                    if dump_to_log:
                        _LOGGER.info("JSON from Spotify:\n" + response.text())
                    return resp_json
                else:
                    _LOGGER.warning("No items key or uri key found, not sure what to do next")
                    _LOGGER.info("JSON from Spotify:\n" + response.text())
                    has_more_data = False
                    return
                if len(items) >= MaxCount:
                    _LOGGER.debug("Reached max number of items")
                    has_more_data = False
                elif "next" in resp_json and resp_json["next"] != None:
                    full_url = resp_json["next"]
                    _LOGGER.debug(full_url)
                else:
                    _LOGGER.debug("Reached end of paging")
                    has_more_data = False
    for item in items:
        if "track" in item and "available_markets" in item["track"]:
            item["track"]["available_markets"] = None
            if "album" in item["track"] and "available_markets" in item["track"]["album"]:
                item["track"]["album"]["available_markets"] = None
    if dump_to_log:
        _LOGGER.info("Items JSON from Spotify:\n" + json.dumps(items, indent=2))
    else:
        _LOGGER.debug("Return count: " + str(len(items)))
    return items

async def spotify_post(relative_url, json_data, return_response=False):
    ensure_token_valid()
    full_url = "https://api.spotify.com/v1" + relative_url
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
    }
    async with aiohttp.ClientSession() as session:
        encoded_url = URL(full_url,encoded=True)
        async with session.post(encoded_url, json=json_data, allow_redirects=False, headers=headers) as response:
            resp_text = response.text()
            if len(resp_text) < 200:
                _LOGGER.info(" > " + str(encoded_url) + ": Status "+str(response.status) + ", Response: " + resp_text.replace("\n","").replace("\r",""))
            else:
                _LOGGER.info(" > " + str(encoded_url) + ": Status "+str(response.status))
                _LOGGER.info("Response: " + resp_text)
            if return_response:
                return response.json()

async def spotify_put(relative_url, json_data, return_response=False):
    ensure_token_valid()
    full_url = "https://api.spotify.com/v1" + relative_url
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
    }
    async with aiohttp.ClientSession() as session:
        encoded_url = URL(full_url,encoded=True)
        async with session.put(encoded_url, json=json_data, allow_redirects=False, headers=headers) as response:
            resp_text = response.text()
            if len(resp_text) < 200:
                _LOGGER.info(" > " + str(encoded_url) + ": Status "+str(response.status) + ", Response: " + resp_text.replace("\n","").replace("\r",""))
            else:
                _LOGGER.info(" > " + str(encoded_url) + ": Status "+str(response.status))
                _LOGGER.info("Response: " + resp_text)
            if return_response:
                return response.json()

async def spotify_delete(relative_url, json_data):
    ensure_token_valid()
    full_url = "https://api.spotify.com/v1" + relative_url
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
    }
    async with aiohttp.ClientSession() as session:
        encoded_url = URL(full_url,encoded=True)
        async with session.delete(encoded_url, json=json_data, allow_redirects=False, headers=headers) as response:
            resp_text = response.text()
            if len(resp_text) < 200:
                _LOGGER.info(" > " + str(encoded_url) + ": Status "+str(response.status) + ", Response: " + resp_text.replace("\n","").replace("\r",""))
            else:
                _LOGGER.info(" > " + str(encoded_url) + ": Status "+str(response.status))
                _LOGGER.info("Response: " + resp_text)

def update_recently_played():
    # Figure out the most recent info I have
    last_saved_info = database_services.run_select_query("MAX(played) AS played", "played_tracks_list", "WHERE [play_lenght_ms] = [duration_ms]")[0]["played"]
    _LOGGER.info("Getting updated data on recently played tracks. Last data saved on recently played is from: " + str(last_saved_info))
    unix_timestamp = int(last_saved_info.replace(tzinfo=datetime.timezone.utc).timestamp()*1000)
    # Get all data on "recently played" after this point in time
    items = spotify_get("/me/player/recently-played?limit=50&after="+str(unix_timestamp), False)
    # items = spotify_get("/me/player/recently-played?limit=50", False, MaxCount=1000)
    filtered_items = []
    # _LOGGER.info(json.dumps(items[1], indent=2))
    for item in items:
        item["played_at"] = datetime.datetime.strptime(item["played_at"].split(".")[0].replace("Z",""), '%Y-%m-%dT%H:%M:%S')
        if item["played_at"] > last_saved_info:
            filtered_items.append(item)
        else:
            _LOGGER.info(item["track"]["name"] + " was played before " + str(last_saved_info) + ", at " + str(item["played_at"]))
    if len(filtered_items) > 0:
        database_services.add_played_tracks_list(filtered_items)
    _LOGGER.info("Finished updating recently played tracks")

def skip_track():
    spotify_playing = state.get("media_player.spotify_gramatus") == "playing"
    if not spotify_playing:
        return False
    data = spotify_get("/me/player/currently-playing", ReturnRaw=True)
    progress_ms = data["progress_ms"]
    data["track"] = data["item"]
    data["played_at"] = datetime.datetime.utcnow();
    database_services.add_skipped_track(data)
    _LOGGER.info("Skipping to next track on media_player.spotify_gramatus")
    media_player.media_next_track(entity_id="media_player.spotify_gramatus")
    return True

def update_shuffle_playlist(playlistid, shuffleplaylistid):
    # Get stored data on last played time for tracks
    # TODO: Look into if Spotify is actually reporting the wrong uri's for me, thus giving me the wrong keys
    base_data = database_services.run_select_query("[uri], [name], MAX([played]) as [played]", "played_tracks_list", "GROUP BY [uri], [name]")
    data = {}
    for track in base_data:
        data[track["uri"]] = track
        data[track["uri"]]["last_played"] = track["played"]
    cached_tracks = database_services.run_select_query("*", "playlist_cached_tracks", "WHERE [playlistid] = '{}'".format(playlistid))
    use_cache = False
    if not use_cache:
        cached_tracks = None
    if cached_tracks != None:
        sorted_tracks = cached_tracks
        _LOGGER.info("Read sorted tracks from cached data")
    else:
        db_items = database_services.run_select_query("[uri], [data]", "playlist_state", "WHERE [playlistid] = '{}'".format(playlistid))
        cached_items = []
        for item in db_items:
            cached_items.append(json.loads(item["data"]))
        if not use_cache:
            cached_items = None
        if cached_items != None:
            _LOGGER.info("Read tracks from cached data")
            items = cached_items
        else:
            # Get all tracks in playlist
            _LOGGER.info("Reading tracks from source playlist")
            # Note: we are using market here as the data in recently_played is using the uri based on market
            items = spotify_get("/playlists/" + playlistid + "/tracks?market=NO&limit=100", False)
            _LOGGER.info("Writing updated data on playlist to DB table [playlist_state]")
            database_services.reset_playlist_state(items, playlistid)

        # Combine the data into an object that will be used to create the shuffled playlist
        tracks = []
        for item in items:
            track = item["track"]
            trackdata = {
                "name": track["name"],
                "uri":  track["uri"],
                "market_uri":  track["uri"],
                "artist": track["artists"][0]["name"],
                "album": track["album"]["name"]
            }
            if "linked_from" in track:
                trackdata["uri"] = track["linked_from"]["uri"]
            if trackdata["market_uri"] in data:
                trackdata["last_played"] = data[trackdata["market_uri"]]["last_played"]
            else:
                trackdata["last_played"] = datetime.datetime.fromtimestamp(0)
            if trackdata["last_played"].timestamp() < 25*365*24*60*60:
                trackdata["last_played"] = datetime.datetime.fromtimestamp(0)
            tracks.append(trackdata)
        # Sort tracks by last played
        sorted_tracks = sorted(tracks, key=lambda i:i["last_played"], reverse=False)
        _LOGGER.info("Writing updated playlist_cached_tracks data to DB")
        database_services.reset_playlist_cached_tracks(sorted_tracks, playlistid)

    day_offset = 1
    for track in sorted_tracks:
        if track["last_played"].timestamp() == 0:
            track["last_played"] = track["last_played"] + datetime.timedelta(days=day_offset)
            day_offset = day_offset + 1

    # TODO: Look for unwanted groupings in the sorted data
    max_passes = 100
    previous_track = None
    lowest_last_played_date = min(sorted_tracks, key=lambda x: x["last_played"])["last_played"]
    for i in range(max_passes):
        updated_list = []
        order_updated = False
        for track in sorted_tracks:
            if previous_track != None:
                if previous_track["artist"] == track["artist"] or previous_track["album"] == track["album"]:
                    # if previous_track["artist"] == track["artist"]:
                    #     _LOGGER.info("Found two by each other for: " + track["artist"])
                    # if previous_track["album"] == track["album"]:
                    #     _LOGGER.info("Found two by each other for: " + track["album"])
                    seconds_from_min_to_this = (track["last_played"] - lowest_last_played_date).total_seconds()
                    move_secs = 0
                    if seconds_from_min_to_this > 0:
                        move_secs = random.randrange(seconds_from_min_to_this) * -1
                    # _LOGGER.info("Seconds to move " + track["name"] + ": " + str(move_secs))
                    track["last_played"] = track["last_played"] + datetime.timedelta(seconds=move_secs)
                    order_updated = True
            previous_track = track
            updated_list.append(track)
        sorted_tracks = sorted(updated_list, key=lambda i:i["last_played"], reverse=False)
        if order_updated == False:
            break

    sorted_tracks = sorted(sorted_tracks, key=lambda i:i["last_played"], reverse=False)
    report_sort_data = False
    if report_sort_data:
        result_list = []
        order = 1
        for track in sorted_tracks:
            result = ""
            if order < 10: result = "00"
            elif order < 100: result = "0"
            result = result + str(order) + " " + track["artist"] + " " + track["name"] # + " (last played: " + str(track["last_played"]) + ")"
            result = result[:45]
            result = result + " (" + str(track["last_played"]) + ")"
            result_list.append(result)
            order = order + 1
        result_list = result_list[:75]
        _LOGGER.info(result_list)
        state.persist("pyscript.playlist_sort_test","n/a",{
            playlistid: result_list
        })
        state.setattr("pyscript.playlist_sort_test." + playlistid, result_list)
    # Split into lists, based on the most recently played and the least recently played
    group_size = 25
    min_group_count = 10
    if len(sorted_tracks) < 25:
        min_group_count = 5
    if len(sorted_tracks) < 10:
        min_group_count = 2
    group_count = int(len(sorted_tracks)/group_size)
    if group_count < min_group_count:
        group_count = min_group_count
    groups = []
    final_track_list = []
    group_count_total = 0
    group_size = int(len(sorted_tracks)/group_count)
    for i in range(group_count):
        group = None
        if i == group_count - 1:
            group = sorted_tracks[group_size*i:]
        else:
            group = sorted_tracks[group_size*i:group_size*(i+1)]
        random.shuffle(group)
        group_count_total = group_count_total + len(group)
        final_track_list = final_track_list + group
        groups.append(group)
    _LOGGER.info(str(len(sorted_tracks)) + " tracks has been shuffled in " + str(group_count) + " groups of " + str(group_size) + ", Total number of tracks shuffled: " + str(group_count_total))

    _LOGGER.info("Removing all items from shadow playlist")
    truncate_playlist(shuffleplaylistid)
    _LOGGER.info("Adding items to shadow playlist")
    count = 0
    # Add all the tracks to the shuffled playlist
    uris = []
    batch_size = 50
    _LOGGER.info(" > Adding shuffled tracks to shadow playlist in batches of " + str(batch_size))
    for group in groups:
        for track in group:
            count = count + 1
            # _LOGGER.info(str(count) + " " + track["name"] + ": " + str(track["last_played"]))
            uris.append(track["uri"])
            if len(uris) >= batch_size:
                _LOGGER.debug("Will post " + str(len(uris)) + " uris to /playlists/" + shuffleplaylistid + "/tracks")
                spotify_post("/playlists/" + shuffleplaylistid + "/tracks", {"uris": uris})
                uris = []
    # Handle the last group
    if len(uris) > 0:
        _LOGGER.debug("Will post " + str(len(uris)) + " uris to /playlists/" + shuffleplaylistid + "/tracks")
        spotify_post("/playlists/" + shuffleplaylistid + "/tracks", {"uris": uris})
    _LOGGER.info("DONE! Shadow playlist has been updated")

def truncate_playlist(playlistid):
    # { "tracks": [{ "uri": "spotify:track:4iV5W9uYEdYUVa79Axb7Rh" },{ "uri": "spotify:track:1301WleyT98MSxVHPZCA6M" }] }
    playlist = spotify_get("/playlists/" + playlistid, False)
    if "name" not in playlist:
        _LOGGER.info("Could not find a name for the playlist we are about to everything stuff from, will not do anything")
        return
    if not playlist["name"].startswith("Shuffled:"):
        _LOGGER.info("Playlist we are about to delete everything from is not marked as a shuffled playlist, will not do anything")
        _LOGGER.info("Playlist name: " + playlist["name"])
        return
    _LOGGER.info(" > All safeguards reports ok, will proceed to empty the playlist.")
    # Get all tracks in playlist
    _LOGGER.info(" > Getting all tracks (so we can tell Spotify to delete them)")
    # Note: we are NOT using market here as we want the actual URI stored in the playlist
    items = spotify_get("/playlists/" + playlistid + "/tracks?limit=100", False)
    uris = []
    batch_size = 50
    _LOGGER.info(" > Deleting all tracks in batches of " + str(batch_size))
    for item in items:
        track = item["track"]
        uris.append({ "uri": track["uri"] })
        if len(uris) >= batch_size:
            _LOGGER.debug("Will delete " + str(len(uris)) + " uris from /playlists/" + playlistid + "/tracks")
            spotify_delete("/playlists/" + playlistid + "/tracks", {"tracks": uris})
            uris = []
    # Handle the last group
    if len(uris) > 0:
        _LOGGER.debug("Will delete " + str(len(uris)) + " uris from /playlists/" + playlistid + "/tracks")
        spotify_delete("/playlists/" + playlistid + "/tracks", {"tracks": uris})

def ensure_shuffle_playlist_exists(playlistid):
    _LOGGER.info("Making sure we have a shadow playlist")
    known_playlists = state.getattr("pyscript.spotify_shuffle_playlists")
    playlisturi = "spotify:playlist:" + playlistid
    if playlisturi in known_playlists:
        _LOGGER.info(" > Shuffle playlist is known with ID: \"" + known_playlists[playlisturi]["shuffle_playlist_id"] + "\"")
        return known_playlists[playlisturi]["shuffle_playlist_id"], True
    playlist = spotify_get("/playlists/" + playlistid, False)
    playlistname = playlist["name"]
    playlisturi = playlist["uri"]
    shuffle_playlist_name = "Shuffled: " + playlistname
    # shuffle_playlist_name = "Shuffled: Alle gromlåter"
    shuffle_playlist_matches = spotify_get("/search?q=" + urllib.parse.quote_plus(shuffle_playlist_name) + "&type=playlist", False)
    shuffle_playlist = None
    if len(shuffle_playlist_matches) > 0:
        for playlist in shuffle_playlist_matches:
            if playlist["owner"]["id"] == spotify_username:
                shuffle_playlist = playlist
    _LOGGER.info(shuffle_playlist)
    if shuffle_playlist != None:
        _LOGGER.info(" > Shuffle playlist already exists with ID: \"" + shuffle_playlist["id"] + "\"")
        state.setattr("pyscript.spotify_shuffle_playlists." + playlisturi, {
            "name": playlistname,
            "shuffle_playlist_id": shuffle_playlist["id"]
        })
        return shuffle_playlist["id"], True
    playlist_data = {
         "name": shuffle_playlist_name,
         "description": "Skyggespilleliste for shuffling med min manuelle algoritme",
         "public": False
    }
    _LOGGER.info(playlist_data)
    shuffle_playlist = spotify_post("/users/" + spotify_username + "/playlists", playlist_data, True)
    # shuffle_playlist = spotify_post("/users/" + spotify_username + "/playlists", None, True)
    _LOGGER.info(" > Created shuffle playlist with ID: \"" + shuffle_playlist["id"] + "\"")
    state.setattr("pyscript.spotify_shuffle_playlists." + playlisturi, {
        "name": playlistname,
        "shuffle_playlist_id": shuffle_playlist["id"]
    })
    return shuffle_playlist["id"], False

def ensure_shuffled_playlist(playlistid):
    update_recently_played()
    shuffle_playlist_id, playlist_exists = ensure_shuffle_playlist_exists(playlistid)
    update_shuffle_playlist(playlistid, shuffle_playlist_id)
    return shuffle_playlist_id
