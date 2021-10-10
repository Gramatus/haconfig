import sqlite3
import datetime
import logging
import json

_LOGGER = logging.getLogger(__name__)

def recreate_playlist_cached_tracks():
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    # c.execute('DROP TABLE playlist_cached_tracks')
    c.execute('''
        CREATE TABLE playlist_cached_tracks2 (
            uri VARCHAR(255),
            playlistid VARCHAR(255),
            name VARCHAR(255) NOT NULL,
            artist VARCHAR(255),
            album VARCHAR(255),
            last_played DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def recreate_playlist_state():
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    # c.execute('DROP TABLE playlist_state')
    c.execute('''
        CREATE TABLE playlist_state (
            uri VARCHAR(255),
            playlistid VARCHAR(255),
            data TEXT
        )
    ''')
    conn.commit()
    conn.close()

def recreate_played_tracks_list():
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    c.execute('DROP TABLE played_tracks_list')
    c.execute('''
        CREATE TABLE played_tracks_list (
            uri VARCHAR(255),
            name VARCHAR(255) NOT NULL,
            played DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def populate_played_tracks_list():
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    try:
        data = state.getattr("pyscript.spotify_last_played")
        for key in data:
            uri = key
            name = data[key]["name"]
            last_played = datetime.datetime.strptime(data[key]["last_played"].split(".")[0].replace("Z",""), '%Y-%m-%dT%H:%M:%S')
            c.execute('''
                INSERT INTO played_tracks_list VALUES(?, ?, ?)
            ''',(uri, name, last_played))
        conn.commit()
        _LOGGER.info("Inserted all data from pyscript.spotify_last_played into db")
    finally:
        conn.close()

def populate_playlist_cached_tracks():
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    try:
        cached_tracks = state.getattr("pyscript.playlist_cached_tracks")
        for playlistid in cached_tracks:
            for item in cached_tracks[playlistid]:
                uri = item["uri"]
                name = item["name"]
                artist = item["artist"]
                album = item["album"]
                last_played = item["last_played"]
                c.execute('INSERT INTO playlist_cached_tracks VALUES(?, ?, ?, ?, ?, ?)',(uri, playlistid, name, artist, album, last_played))
        conn.commit()
        _LOGGER.info("Inserted all data from pyscript.playlist_cached_tracks into db")
    finally:
        conn.close()

def populate_playlist_cached_tracks2():
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    try:
        cached_tracks = run_select_query("*","playlist_cached_tracks")
        for item in cached_tracks:
            item["last_played"] = datetime.datetime.strptime(item["last_played"].split(".")[0].replace("Z",""), '%Y-%m-%d %H:%M:%S')
            c.execute('INSERT INTO playlist_cached_tracks2 VALUES(?, ?, ?, ?, ?, ?)',(item["uri"], item["playlistid"], item["name"], item["artist"], item["album"], item["last_played"]))
        conn.commit()
        _LOGGER.info("Inserted all data from playlist_cached_tracks into playlist_cached_tracks2")
    finally:
        conn.close()

def populate_playlist_state():
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    try:
        playlist_states = state.getattr("pyscript.playliststate")
        for playlistid in playlist_states:
            for item in playlist_states[playlistid]:
                uri = item["track"]["uri"]
                json_data = json.dumps(item)
                c.execute('INSERT INTO playlist_state VALUES(?, ?, ?)',(uri, playlistid, json_data))
        conn.commit()
        _LOGGER.info("Inserted all data from pyscript.playliststate into db")
    finally:
        conn.close()

def add_played_tracks_list(items):
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    try:
        for item in items:
            album = ""
            if "album" in item["track"]:
                album = item["track"]["album"]["name"]
            artist = ""
            if "artists" in item["track"]:
                artist = item["track"]["artists"][0]["name"]
            c.execute('INSERT INTO played_tracks_list VALUES(?, ?, ?, ?, ?, ?, ?)', (item["track"]["uri"], item["track"]["name"], item["played_at"], album, artist, item["track"]["duration_ms"], item["track"]["duration_ms"]))
        conn.commit()
        _LOGGER.info("Inserted " + str(len(items)) + " new rows into [played_tracks_list]")
    finally:
        conn.close()

def add_skipped_track(item):
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    try:
        album = ""
        if "album" in item["track"]:
            album = item["track"]["album"]["name"]
        artist = ""
        if "artists" in item["track"]:
            artist = item["track"]["artists"][0]["name"]
        c.execute('INSERT INTO played_tracks_list VALUES(?, ?, ?, ?, ?, ?, ?)', (item["track"]["uri"], item["track"]["name"], item["played_at"], album, artist, item["progress_ms"], item["track"]["duration_ms"]))
        conn.commit()
        _LOGGER.info("Inserted info on skipped track into [played_tracks_list]: " + item["track"]["name"])
    finally:
        conn.close()

def update_played_tracks_data(item):
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    try:
        c.execute('UPDATE [played_tracks_list] SET [play_lenght_ms] = ? WHERE [uri] = ? AND [play_lenght_ms] IS NULL', (item["duration_ms"], item["uri"], ))
        c.execute('UPDATE [played_tracks_list] SET [duration_ms] = ? WHERE [uri] = ? AND [duration_ms] IS NULL', (item["duration_ms"], item["uri"], ))
        c.execute('UPDATE [played_tracks_list] SET [album] = ?, [artist] = ? WHERE [uri] = ?', (item["album"]["name"], item["artists"][0]["name"], item["uri"]))
        conn.commit()
        _LOGGER.info("Updated [play_lenght_ms], [duration_ms], [album] and [artist] where missing for track: " + item["name"])
    finally:
        conn.close()

def reset_playlist_cached_tracks(tracks, playlistid):
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    try:
        c.execute('DELETE FROM [playlist_cached_tracks] WHERE [playlistid] = ?', (playlistid,))
        for item in tracks:
            c.execute('INSERT INTO playlist_cached_tracks VALUES(?, ?, ?, ?, ?, ?)', (item["uri"], playlistid, item["name"], item["artist"], item["album"], item["last_played"]))
        conn.commit()
        _LOGGER.info("Inserted new rows into [playlist_cached_tracks]")
    finally:
        conn.close()

def reset_playlist_state(tracks, playlistid):
    conn = sqlite3.connect('home-assistant_v2.db')
    c = conn.cursor()
    try:
        c.execute('DELETE FROM [playlist_state] WHERE [playlistid] = ?', (playlistid,))
        for item in tracks:
            uri = item["track"]["uri"]
            json_data = json.dumps(item)
            c.execute('INSERT INTO [playlist_state] VALUES(?, ?, ?)',(uri, playlistid, json_data))
        conn.commit()
        _LOGGER.info("Inserted new rows into [playlist_state]")
    finally:
        conn.close()

def run_select_query(columns, table, prms=None):
    query = "SELECT {} FROM {}".format(columns, table)
    if prms != None:
        query = query + " " + prms
    conn = sqlite3.connect('home-assistant_v2.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('PRAGMA TABLE_INFO({})'.format(table))
    datetime_rows = []
    for row in c:
        # Columns from TABLE_INFO: cid, name, type, notnull, dflt_value, pk
        if row["type"] == "DATETIME":
            datetime_rows.append(row["name"])
    c.execute(query)
    data = []
    for row in c:
        datarow = {}
        for col in dict(row):
            if col in datetime_rows:
                datarow[col] = datetime.datetime.strptime(row[col].split(".")[0].replace("Z",""), '%Y-%m-%d %H:%M:%S')
            else:
                datarow[col] = row[col]
        data.append(datarow)
    conn.close()
    return data
