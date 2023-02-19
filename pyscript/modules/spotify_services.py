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
import math
import asyncio

_LOGGER = logging.getLogger(__name__)

# Useful links:
# Console, for testing endpoints: https://developer.spotify.com/console/
# Web api reference: https://developer.spotify.com/documentation/web-api/reference/
# My app for playlists: https://developer.spotify.com/dashboard/applications/02f9211580d043bca8a97f2b99890337

state.persist("pyscript.temp_token","volatile", {
    "token": "none",
    "expires": None
})
state.persist("pyscript.spotify_shuffle_playlists","n/a", {})

spotify_username = "gramatus"

token_expires = state.getattr("pyscript.temp_token")["expires"]
token =  state.getattr("pyscript.temp_token")["token"]

sp_dc = pyscript.config["sp_dc"]
sp_key = pyscript.config["sp_key"]

async def get_spotify_token():
    try:
        global token, token_expires
        await gramatus_spotify_auth.reset_token()
        log.info("Sleeping for five seconds since await seems to fail here")
        await asyncio.sleep(5)
        session = hass.data["gramatus_spotify_auth"]["session"]
        token = session.token["access_token"]
        token_expires = session.token["expires_at"]
        # _LOGGER.info("Scopes for token: " + session.token["scope"])
        expires_in_seconds = token_expires - int(time.time())
        _LOGGER.info("Got an updated token from gramatus_spotify_auth, it will expire in: " + str(datetime.timedelta(seconds=expires_in_seconds)))
        state.setattr("pyscript.temp_token.token", token)
        state.setattr("pyscript.temp_token.expires", token_expires)
        return token
    except:
        raise HomeAssistantError("Could not get spotify token")

# async def get_spotify_token_web():
#     try:
#         global token, token_expires
#         token, token_expires = task.executor(st.start_session, sp_dc, sp_key)
#         expires = token_expires - int(time.time())
#         _LOGGER.info("Got an updated token, it will expire in: " + str(datetime.timedelta(seconds=expires)))
#         state.setattr("pyscript.temp_token.token_web", token)
#         state.setattr("pyscript.temp_token.expires_web", token_expires)
#         return token
#     except:
#         raise HomeAssistantError("Could not get spotify token")

async def ensure_token_valid():
    if float(token_expires) > time.time():
        return
    _LOGGER.debug("Token expired at: " + str(datetime.timedelta(seconds=token_expires - int(time.time()))) + ", will get a new token")
    get_spotify_token()

async def spotify_get(relative_url, dump_to_log=False, GetAll=True, MaxCount=1000, ReturnRaw=False, LogErrors=True):
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
                if response.status // 100 != 2:
                    if LogErrors:
                        _LOGGER.warning(" GET > " + str(encoded_url) + ": Status "+str(response.status) + ", Response from server:\n" + response.text())
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
                _LOGGER.debug(" > " + str(encoded_url) + ": Status "+str(response.status) + cursor_text)
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
                elif "episodes" in resp_json and "items" in resp_json["episodes"]:
                    # Probably a paged list of items
                    new_items = resp_json["episodes"]["items"]
                    items = items + new_items
                elif "uri" in resp_json:
                    # Return data has a single item (most items in Spotify have a uri)
                    has_more_data = False
                    if dump_to_log:
                        _LOGGER.info("JSON from Spotify:\n" + response.text())
                    return resp_json
                elif "tracks" in resp_json:
                    # Probably a paged list of items
                    new_items = resp_json["tracks"]
                    items = items + new_items
                else:
                    _LOGGER.warning("No items key or uri key found, not sure what to do next")
                    _LOGGER.info("JSON from Spotify:\n" + response.text())
                    has_more_data = False
                    return
                if len(items) >= MaxCount:
                    _LOGGER.debug("Reached max number of items")
                    has_more_data = False
                elif "next" in resp_json and resp_json["next"] != None and GetAll:
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

async def spotify_post(relative_url, json_data, return_response=False, RetryCount=0, Attempt=1):
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
            if RetryCount > Attempt and response.status // 100 == 5:
                _LOGGER.warning(" POST > Attempt " + str(Attempt) + " of " + str(RetryCount) + ": got status " + str(response.status) + ", retrying")
                spotify_post(relative_url, json_data, return_response, RetryCount=RetryCount, Attempt=Attempt + 1)
                return
            if response.status // 100 != 2:
                _LOGGER.warning(" POST > " + str(encoded_url) + ": Status "+str(response.status) + ", Response from server:\n" + response.text())
                return
            resp_text = response.text()
            if len(resp_text) < 200:
                _LOGGER.debug(" > " + str(encoded_url) + ": Status "+str(response.status) + ", Response: " + resp_text.replace("\n","").replace("\r",""))
            else:
                _LOGGER.debug(" > " + str(encoded_url) + ": Status "+str(response.status))
                _LOGGER.debug("Response: " + resp_text)
            if return_response:
                return response.json()

async def spotify_put(relative_url, json_data=None, return_response=False, RetryCount=0, Attempt=1):
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
            if RetryCount > Attempt and response.status // 100 == 5:
                _LOGGER.warning(" PUT > Attempt " + str(Attempt) + " of " + str(RetryCount) + ": got status " + str(response.status) + ", retrying")
                spotify_put(relative_url, json_data, return_response, RetryCount=RetryCount, Attempt=Attempt + 1)
                return
            if response.status // 100 != 2:
                _LOGGER.warning(" PUT > " + str(encoded_url) + ": Status "+str(response.status) + ", Response from server:\n" + response.text())
                return
            resp_text = response.text()
            if len(resp_text) < 200:
                _LOGGER.debug(" > " + str(encoded_url) + ": Status "+str(response.status) + ", Response: " + resp_text.replace("\n","").replace("\r",""))
            else:
                _LOGGER.debug(" > " + str(encoded_url) + ": Status "+str(response.status))
                _LOGGER.debug("Response: " + resp_text)
            if return_response:
                return response.json()

async def spotify_delete(relative_url, json_data=None, log_data=False, RetryCount=0, Attempt=1):
    ensure_token_valid()
    full_url = "https://api.spotify.com/v1" + relative_url
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + token
    }
    if(log_data):
        _LOGGER.info(json_data)
    async with aiohttp.ClientSession() as session:
        encoded_url = URL(full_url,encoded=True)
        async with session.delete(encoded_url, json=json_data, allow_redirects=False, headers=headers) as response:
            if RetryCount > Attempt and response.status // 100 == 5:
                _LOGGER.warning("Attempt " + str(Attempt) + " of " + str(RetryCount) + ": got status " + str(response.status) + ", retrying")
                spotify_delete(relative_url, json_data, log_data, RetryCount=RetryCount, Attempt=Attempt + 1)
                return
            if response.status // 100 != 2:
                _LOGGER.warning(" DELETE > " + str(encoded_url) + ": Status "+str(response.status) + ", Response from server:\n" + response.text())
                return
            resp_text = response.text()
            if len(resp_text) < 200:
                _LOGGER.debug(" > " + str(encoded_url) + ": Status "+str(response.status) + ", Response: " + resp_text.replace("\n","").replace("\r",""))
            else:
                _LOGGER.debug(" > " + str(encoded_url) + ": Status "+str(response.status))
                _LOGGER.debug("Response: " + resp_text)

def update_recently_played():
    # Figure out the most recent info I have
    last_saved_info = database_services.run_select_query("MAX(played) AS played", "played_tracks_list", "WHERE [play_lenght_ms] = [duration_ms]")[0]["played"]
    _LOGGER.debug("Getting updated data on recently played tracks. Last data saved on recently played is from: " + str(last_saved_info))
    unix_timestamp = int(last_saved_info.replace(tzinfo=datetime.timezone.utc).timestamp()*1000)
    # Get all data on "recently played" after this point in time
    items = spotify_get("/me/player/recently-played?limit=50&after="+str(unix_timestamp), False)
    filtered_items = []
    for item in items:
        item["played_at"] = datetime.datetime.strptime(item["played_at"].split(".")[0].replace("Z",""), '%Y-%m-%dT%H:%M:%S')
        if item["played_at"] > last_saved_info:
            filtered_items.append(item)
    if len(filtered_items) > 0:
        database_services.add_played_tracks_list(filtered_items)
    _LOGGER.debug("Finished updating recently played tracks")

def skip_track():
    spotify_playing = state.get("media_player.spotify_gramatus") == "playing"
    if not spotify_playing:
        return False
    data = spotify_get("/me/player/currently-playing", ReturnRaw=True)
    progress_ms = data["progress_ms"]
    data["track"] = data["item"]
    data["played_at"] = datetime.datetime.utcnow();
    database_services.add_skipped_track(data)
    _LOGGER.debug("Skipping to next track on media_player.spotify_gramatus")
    media_player.media_next_track(entity_id="media_player.spotify_gramatus")
    return True

def fix_repeat_artist_album(sorted_tracks, lowest_last_played_datetime, logResult=False):
    max_passes = 10
    parent_track = None
    grandparent_track = None
    # log.info("Track list to fix has a length of: " + str(len(sorted_tracks)))
    for i in range(max_passes):
        # _LOGGER.info("Avoid groupings, pass #" + str(i + 1))
        updated_list = []
        order_updated = False
        track_num = 0
        for track in sorted_tracks:
            track_num = track_num + 1
            equal_parent = parent_track != None and (parent_track["artist"] == track["artist"] or parent_track["album"] == track["album"])
            equal_grandparent = grandparent_track != None and (grandparent_track["artist"] == track["artist"] or grandparent_track["album"] == track["album"])
            if equal_parent or equal_grandparent:
                seconds_from_min_to_this = int((track["last_played"] - lowest_last_played_datetime).total_seconds())
                if seconds_from_min_to_this <= 0:
                    seconds_from_min_to_this = seconds_from_min_to_this * -1 # Handles tracks that has not been played before
                # _LOGGER.debug("seconds_from_min_to_this:" + str(seconds_from_min_to_this))
                if seconds_from_min_to_this == 0:
                    seconds_from_min_to_this = 1
                # Get a random number +/- half the distance between the oldest track and the position of this track
                rand_range = (seconds_from_min_to_this * 0.5) - random.randrange(0, seconds_from_min_to_this)
                # Increase the move time if we are on subsequent passes (to increase the likelihood of "fixing" stuff), this number will be approximately
                # log4: 1.4 -> 1.6 -> 1.9 -> 2.2 -> 2.5 -> 2.8 -> 3.2 -> 3.5 -> 3.9 -> 4.3 -> 4.7
                # log5: 1.5 -> 1.8 -> 2.2 -> 2.6 -> 3.0 -> 3.4 -> 3.9 -> 4.4 -> 4.9 -> 5.5 -> 6.0
                # In windows calc graph mode: 1+0,1(floor(𝑥))^2/(ln(floor(𝑥)+1)/ln(5))^2 
                pass_offset = 1 + 0.1 * i**2 / math.log(i+2,5)**2
                move_secs = int(rand_range * pass_offset)
                if logResult:
                    _LOGGER.info("Pass #" + str(i+1) + ": Seconds to move #" + str(track_num)+" \"" + track["name"] + "\" (" + track["artist"] + " / " + track["album"] + "): " + str(move_secs) + " (" + str(datetime.timedelta(seconds=move_secs)) + "), original datetime: " + str(track["last_played"]) + ", rand_range: " + str(datetime.timedelta(seconds=rand_range)) + ", pass_offset: " + str(pass_offset))
                track["last_played"] = track["last_played"] + datetime.timedelta(seconds=move_secs)
                order_updated = True
            # else:
            #     if logResult and track["album"]=="Cocktail Bar Jazz":
            #         _LOGGER.debug("#" + str(track_num) + ": These are different: \"" + previous_track["album"] + "\" / \"" + track["album"] + "\"")
            grandparent_track = parent_track
            parent_track = track
            updated_list.append(track)
        sorted_tracks = sorted(updated_list, key=lambda i:i["last_played"], reverse=False)
        if i == max_passes - 1:
            _LOGGER.info(">>> Final number of passes to avoid groupings: " + str(i + 1))
        if order_updated == False:
            _LOGGER.info(">>> Final number of passes to avoid groupings: " + str(i + 1))
            break
    return sorted_tracks

def update_shuffle_playlist(playlistid, shuffleplaylistid, consider_play_date=True, debug_log=False):
    # Get stored data on last played time for tracks
    base_data = database_services.run_select_query("[uri], [name], [album], [artist], MAX([played]) as [played]", "played_tracks_list", "GROUP BY [uri], [name], [album], [artist]")
    _LOGGER.debug("Rows returned from database: " + str(len(base_data)))
    # _LOGGER.info(len(base_data))
    played_tracks_uri = {}
    played_tracks_identifier = {}
    played_tracks_name = {}
    for track in base_data:
        if(track["uri"] in played_tracks_uri and played_tracks_uri[track["uri"]]["last_played"] > track["played"]):
            continue
        played_tracks_uri[track["uri"]] = track
        played_tracks_uri[track["uri"]]["last_played"] = track["played"]
        track_identifier = track["name"] + "|" + track["album"] + "|" + track["artist"]
        if(track_identifier in played_tracks_identifier and played_tracks_identifier[track_identifier]["last_played"] > track["played"]):
            continue
        played_tracks_identifier[track_identifier] = track
        played_tracks_identifier[track_identifier]["last_played"] = track["played"]
        if(track["name"] in played_tracks_name and played_tracks_name[track["name"]]["last_played"] > track["played"]):
            continue
        played_tracks_name[track["name"]] = track
        played_tracks_name[track["name"]]["last_played"] = track["played"]
    use_cache = False
    if use_cache:
        sorted_tracks = database_services.run_select_query("*", "playlist_cached_tracks", "WHERE [playlistid] = '{}'".format(playlistid))
        _LOGGER.info("Read sorted tracks from cached data")
    else:
        # Get all tracks in playlist
        _LOGGER.debug("Reading tracks from source playlist")
        # Note: we are using market here as the data in recently_played is using the uri based on market
        items = spotify_get("/playlists/" + playlistid + "/tracks?market=NO&limit=100", False)

        # Combine the data into an object that will be used to create the shuffled playlist
        tracks = []
        for item in items:
            track = item["track"]
            trackdata = {
                "name": track["name"],
                "uri":  track["uri"],
                "market_uri":  track["uri"],
                "artist": track["artists"][0]["name"],
                "album": track["album"]["name"],
                "track_identifier": track["name"] + "|" + track["album"]["name"] + "|" + track["artists"][0]["name"]
            }
            if "linked_from" in track:
                trackdata["uri"] = track["linked_from"]["uri"]
            if trackdata["market_uri"] in played_tracks_uri:
                trackdata["last_played"] = played_tracks_uri[trackdata["market_uri"]]["last_played"]
            elif trackdata["track_identifier"] in played_tracks_identifier:
                _LOGGER.warning("Track has different uri in DB: " + trackdata["uri"]+" / " + trackdata["track_identifier"] + ", DB: " + str(played_tracks_identifier[trackdata["track_identifier"]]))
                # TODO: Consider updating playlist with uri from DB? Or perhaps not? Seems like this might be hard to do, also this "backup" solution makes sure stuff actually works as expected anyways
                trackdata["last_played"] = played_tracks_identifier[trackdata["track_identifier"]]["last_played"]
            else:
                if trackdata["name"] in played_tracks_name:
                    _LOGGER.warning("No match in DB, but DB has track with same name: " + trackdata["uri"]+" / " + trackdata["name"])
                    _LOGGER.info(played_tracks_name[track["name"]])
                trackdata["last_played"] = datetime.datetime.fromtimestamp(0)
            if trackdata["last_played"].timestamp() < 25*365*24*60*60:
                trackdata["last_played"] = datetime.datetime.fromtimestamp(0)
            trackdata["original_last_played"] = trackdata["last_played"]
            tracks.append(trackdata)
        # Sort tracks by last played
        sorted_tracks = sorted(tracks, key=lambda i:i["last_played"], reverse=False)

    # For tracks that haven't been played before, add a last_played value so things gets a bit more sorted. Before doing that, do a simple shuffle on the list to add some seed into "added order" stuff
    random.shuffle(sorted_tracks)
    day_offset = 1
    one_year_ago = datetime.datetime.fromtimestamp(datetime.datetime.now().timestamp() - 365*24*60*60)
    for track in sorted_tracks:
        if track["last_played"].timestamp() == 0 or not consider_play_date:
            track["last_played"] = one_year_ago - datetime.timedelta(days=day_offset)
            # _LOGGER.debug("Last played set to: " + str(track["last_played"]))
            day_offset = day_offset + 1

    tracks_played_last_year = list(filter(lambda x: x["last_played"].timestamp() >= datetime.datetime.now().timestamp() - 365*24*60*60, sorted_tracks))
    if not consider_play_date or len(tracks_played_last_year) == 0:
        tracks_played_last_year = sorted_tracks
    # if len(tracks_played_last_year) > 0:
    lowest_last_played_datetime = min(tracks_played_last_year, key=lambda x: x["last_played"])["last_played"]
    # else:
    #     lowest_last_played_datetime = min(sorted_tracks, key=lambda x: x["last_played"])["last_played"]
    sorted_tracks = fix_repeat_artist_album(sorted_tracks, lowest_last_played_datetime, True)
    # log.info(list(sorted_tracks)[0]["last_played"])
    # log.info(datetime.datetime.now() - datetime.timedelta(days=365))
    # log.info(list(sorted_tracks)[0]["last_played"].timestamp())
    # log.info(datetime.datetime.now().timestamp() - 365*24*60*60)
    # log.info(list(sorted_tracks))
    # tmp = list(tracks_played_last_year)
    # log.info(tmp)
    # log.info(len(tmp))
    # log.info(lowest_last_played_datetime)
    # return

    sorted_tracks = sorted(sorted_tracks, key=lambda i:i["last_played"], reverse=False)
    report_sort_data = False
    # if report_sort_data:
    #     result_list = []
    #     order = 1
    #     for track in sorted_tracks:
    #         result = ""
    #         if order < 10: result = "00"
    #         elif order < 100: result = "0"
    #         result = result + str(order) + " " + track["artist"] + " " + track["name"] # + " (last played: " + str(track["last_played"]) + ")"
    #         result = result[:45]
    #         result = result + " (" + str(track["last_played"]) + ")"
    #         result_list.append(result)
    #         order = order + 1
    #     result_list = result_list[:75]
    #     _LOGGER.info(result_list)
    #     state.persist("pyscript.playlist_sort_test","n/a",{
    #         playlistid: result_list
    #     })
    #     state.setattr("pyscript.playlist_sort_test." + playlistid, result_list)
    # Split into lists, based on the most recently played and the least recently played
    group_size = 50
    if len(sorted_tracks) > 200:
        group_size = 100
    if len(sorted_tracks) > 500:
        group_size = 150
    min_group_count = 3
    min_group_size = 50
    if len(sorted_tracks) < 100:
        min_group_count = 2
    if len(sorted_tracks) < 50:
        min_group_count = 1
    group_count = int(len(sorted_tracks)/group_size)
    if group_count < min_group_count:
        _LOGGER.debug("Too few groups, increasing group count to: " + str(min_group_count))
        group_count = min_group_count
    if len(sorted_tracks)/group_count < min_group_size:
        group_count = int(len(sorted_tracks)/min_group_size)
        _LOGGER.debug("Too small groups, reduced group count to: " + str(group_count))
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
        # track_debug_list = []
        # for track in group:
        #     track_debug_list.append(track["name"])
        # _LOGGER.info(track_debug_list)
        group_count_total = group_count_total + len(group)
        final_track_list = final_track_list + group
        groups.append(group)
    _LOGGER.info(str(len(sorted_tracks)) + " tracks has been shuffled in " + str(group_count) + " groups of " + str(group_size) + ", Total number of tracks shuffled: " + str(group_count_total))

    fix_after_shuffle = True
    shuffled_tracks = []
    group_num = 1
    for group in groups:
        updated_group = group
        if fix_after_shuffle:
            updated_group = fix_repeat_artist_album(updated_group, lowest_last_played_datetime, True)
            _LOGGER.info("Group#" + str(group_num) + ": Updated after shuffling to avoid groupings of same artist/album")
        for track in group:
            shuffled_tracks.append(track)
        group_num = group_num + 1

    _LOGGER.debug("Removing all items from shadow playlist")
    truncate_playlist(shuffleplaylistid)
    _LOGGER.debug("Adding items to shadow playlist")
    count = 0
    # Add all the tracks to the shuffled playlist
    uris = []
    batch_size = 50
    _LOGGER.debug(" > Adding shuffled tracks to shadow playlist in batches of " + str(batch_size))
    for track in shuffled_tracks:
        if debug_log:
            _LOGGER.info("\t#" + str(count) + "\t" + track["name"] + "\toriginal_last_played:\t" + str(track["original_last_played"]) + "\tlast_played:\t" + str(track["last_played"]))
        count = count + 1
        uris.append(track["uri"])
        if len(uris) >= batch_size:
            _LOGGER.debug("Will post " + str(len(uris)) + " uris to /playlists/" + shuffleplaylistid + "/tracks")
            spotify_post("/playlists/" + shuffleplaylistid + "/tracks", {"uris": uris}, RetryCount=3)
            uris = []
    # Handle the last batch
    if len(uris) > 0:
        _LOGGER.debug("Will post " + str(len(uris)) + " uris to /playlists/" + shuffleplaylistid + "/tracks")
        spotify_post("/playlists/" + shuffleplaylistid + "/tracks", {"uris": uris}, RetryCount=3)
    _LOGGER.debug("DONE! Shadow playlist has been updated")

def truncate_playlist(playlistid, iteration = 1):
    if(iteration == 1):
        playlist = spotify_get("/playlists/" + playlistid, False)
        if "name" not in playlist:
            _LOGGER.info("Could not find a name for the playlist we are about to everything stuff from, will not do anything")
            return
        if not playlist["name"].startswith("Shuffled:"):
            _LOGGER.info("Playlist we are about to delete everything from is not marked as a shuffled playlist, will not do anything")
            _LOGGER.info("Playlist name: " + playlist["name"])
            return
        _LOGGER.debug(" > All safeguards reports ok, will proceed to empty the playlist.")
    # Get all tracks in playlist
    _LOGGER.debug(" > Getting all tracks (so we can tell Spotify to delete them)")
    # Note: we are NOT using market here as we want the actual URI stored in the playlist
    items = spotify_get("/playlists/" + playlistid + "/tracks?limit=100", False)
    uris = []
    batch_size = 50
    _LOGGER.debug(" > Deleting all tracks in batches of " + str(batch_size))
    for item in items:
        track = item["track"]
        uris.append({ "uri": track["uri"] })
        if len(uris) >= batch_size:
            _LOGGER.debug("Will delete " + str(len(uris)) + " uris from /playlists/" + playlistid + "/tracks")
            spotify_delete("/playlists/" + playlistid + "/tracks", {"tracks": uris}, RetryCount=3)
            uris = []
    # Handle the last group
    if len(uris) > 0:
        _LOGGER.debug("Will delete " + str(len(uris)) + " uris from /playlists/" + playlistid + "/tracks")
        spotify_delete("/playlists/" + playlistid + "/tracks", {"tracks": uris}, RetryCount=3)
    # Retry a few times if some delete operations failed
    max_retries = 5
    if(iteration > max_retries):
        _LOGGER.warning("Reached " + str(max_retries) + " retries, giving up on fully truncating the playlist")
        return
    items = spotify_get("/playlists/" + playlistid + "/tracks?limit=100", False, LogErrors=False)
    if items != None and len(items) > 0:
        _LOGGER.warn("Not all tracks deleted after iteration #" + str(iteration))
        truncate_playlist(playlistid, iteration + 1)

def ensure_shuffle_playlist_exists(playlistid):
    # _LOGGER.info("Making sure we have a shadow playlist")
    known_playlists = state.getattr("pyscript.spotify_shuffle_playlists")
    playlisturi = "spotify:playlist:" + playlistid
    if playlisturi in known_playlists:
        _LOGGER.debug(" > Shuffle playlist is known with ID: \"" + known_playlists[playlisturi]["shuffle_playlist_id"] + "\"")
        return known_playlists[playlisturi]["shuffle_playlist_id"], True
    _LOGGER.debug(" > Shuffle playlist id is not saved, trying to find it by searching Spotify")
    playlist = spotify_get("/playlists/" + playlistid, False)
    playlistname = playlist["name"]
    playlisturi = playlist["uri"]
    shuffle_playlist_name = "Shuffled: " + playlistname
    shuffle_playlist_matches = spotify_get("/search?q=" + urllib.parse.quote_plus(shuffle_playlist_name) + "&type=playlist", False)
    shuffle_playlist = None
    if len(shuffle_playlist_matches) > 0:
        for playlist in shuffle_playlist_matches:
            if playlist["owner"]["id"] == spotify_username:
                shuffle_playlist = playlist
    if shuffle_playlist != None:
        _LOGGER.debug(" > Shuffle playlist already exists with ID: \"" + shuffle_playlist["id"] + "\"")
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
    shuffle_playlist = spotify_post("/users/" + spotify_username + "/playlists", playlist_data, True)
    _LOGGER.info(" > Created shuffle playlist with ID: \"" + shuffle_playlist["id"] + "\"")
    state.setattr("pyscript.spotify_shuffle_playlists." + playlisturi, {
        "name": playlistname,
        "shuffle_playlist_id": shuffle_playlist["id"]
    })
    return shuffle_playlist["id"], False

def ensure_shuffled_playlist(playlistid, consider_play_date=True):
    update_recently_played()
    shuffle_playlist_id, playlist_exists = ensure_shuffle_playlist_exists(playlistid)
    state.get("input_boolean.shuffle_debug")
    debug_log = state.get("input_boolean.shuffle_debug") == "on"
    update_shuffle_playlist(playlistid, shuffle_playlist_id, consider_play_date, debug_log)
    return shuffle_playlist_id
