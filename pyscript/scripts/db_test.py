import logging
import database_services
import datetime
import spotify_services

_LOGGER = logging.getLogger(__name__)

@service
def db_test():
    """yaml
name: Database test code
"""
    # database_services.run_query("SELECT sql FROM sqlite_master WHERE type = 'table' AND tbl_name = 'states'")
    # database_services.recreate_played_tracks_list()
    # database_services.populate_played_tracks_list()
    # database_services.recreate_playlist_state()
    # database_services.populate_playlist_state()
    # database_services.recreate_playlist_cached_tracks()
    # database_services.populate_playlist_cached_tracks2()
    database_services.reset_playlist_state(None, "2pjB7wGkkoG9VYY8enMR5b")
    # data = database_services.run_select_query("SELECT * FROM played_tracks_list")
    # data = database_services.run_select_query("*", "played_tracks_list")
    # spotify_services.update_recently_played()
    # for row in data:
    #     _LOGGER.info(row["uri"])
    #     _LOGGER.info(row["name"])
    #     _LOGGER.info(row["played"].timestamp())
