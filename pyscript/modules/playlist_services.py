import logging
import spotify_token as st
import time
import datetime
from yarl import URL
import aiohttp
import json
import random
import urllib

_LOGGER = logging.getLogger(__name__)

# Useful links:
# Console, for testing endpoints: https://developer.spotify.com/console/
# Web api reference: https://developer.spotify.com/documentation/web-api/reference/
# My app for playlists: https://developer.spotify.com/dashboard/applications/02f9211580d043bca8a97f2b99890337

state.persist("pyscript.temp_token","volatile", {
    "token": "none",
    "expires": None
})
state.persist("pyscript.spotify_last_played","n/a", {})
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

async def spotify_get(relative_url,dump_to_log=False, GetAll=True, MaxCount=1000):
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
                if "items" in resp_json:
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
    data = state.getattr("pyscript.spotify_last_played")
    all_playdates = []
    for key in data:
        all_playdates.append(datetime.datetime.strptime(data[key]["last_played"].split(".")[0].replace("Z",""), '%Y-%m-%dT%H:%M:%S'))
    last_saved_info = max(all_playdates)
    _LOGGER.info("Getting updated data on recently played tracks. Last data saved on recently played is from: " + str(last_saved_info))
    unix_timestamp = int(last_saved_info.timestamp()*1000)
    # Get all data on "recently played" after this point in time
    items = spotify_get("/me/player/recently-played?limit=50&after="+str(unix_timestamp), False)
    # items = spotify_get("/me/player/recently-played?limit=50", False, MaxCount=1000)
    # Save this information as attributes on an entity (until HA says there is too much info...)
    for item in items:
        state.setattr("pyscript.spotify_last_played."+item["track"]["uri"],{
            "name": item["track"]["name"],
            "last_played": item["played_at"]
        })

def update_shuffle_playlist(playlistid, shuffleplaylistid):
    # Get stored data on last played time for tracks
    data = state.getattr("pyscript.spotify_last_played")
    # Get all tracks in playlist
    _LOGGER.info("Reading tracks from source playlist")
    items = spotify_get("/playlists/" + playlistid + "/tracks?limit=100", False)
    # Combine the data into an object that will be used to create the shuffled playlist
    tracks = []
    for item in items:
        track = item["track"]
        trackdata = {
            "name": track["name"],
            "uri":  track["uri"]
        }
        if track["uri"] in data:
            trackdata["last_played"] = datetime.datetime.strptime(data[track["uri"]]["last_played"].split(".")[0].replace("Z",""), '%Y-%m-%dT%H:%M:%S')
        else:
            trackdata["last_played"] = datetime.datetime.fromtimestamp(0)
        tracks.append(trackdata)
    # Sort tracks by last played
    sorted_tracks = sorted(tracks, key=lambda i:i["last_played"], reverse=False)
    # Split into lists, based on the most recently played and the least recently played
    # TODO: Consider more groups (or less?)
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
    shuffle_playlist_id = ensure_shuffle_playlist_exists(playlistid)
    update_shuffle_playlist(playlistid, shuffle_playlist_id)
    return shuffle_playlist_id