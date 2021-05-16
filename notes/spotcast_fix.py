# From line 292 in __init__.py
        if uri.find("show") > 0:
            show_episodes_info = client.show_episodes(uri)
            readCount = len(show_episodes_info["items"])
            _LOGGER.debug("Readcount: %s",readCount)
            lastEpisode = show_episodes_info["items"][0];
            episodeToPlay = None
            for episode in show_episodes_info["items"]:
                if episodeToPlay is None:
                    playState = episode["resume_point"]
                    if playState["fully_played"]:
                        episodeToPlay = lastEpisode
                        _LOGGER.debug("Found that this is fully played: %s",episode)
                    lastEpisode = episode
            if episodeToPlay is None:
                show_episodes_info = client.show_episodes(uri,50,readCount)
                readCount = readCount+len(show_episodes_info["items"])
                _LOGGER.debug("Readcount: %s",readCount)
                for episode in show_episodes_info["items"]:
                    if episodeToPlay is None:
                        playState = episode["resume_point"]
                        if playState["fully_played"]:
                            episodeToPlay = lastEpisode
                            _LOGGER.debug("Found that this is fully played: %s",episode)
                        lastEpisode = episode
            if episodeToPlay is None:
                show_episodes_info = client.show_episodes(uri,50,readCount)
                readCount = readCount+len(show_episodes_info["items"])
                _LOGGER.debug("Readcount: %s",readCount)
                for episode in show_episodes_info["items"]:
                    if episodeToPlay is None:
                        playState = episode["resume_point"]
                        if playState["fully_played"]:
                            episodeToPlay = lastEpisode
                            _LOGGER.debug("Found that this is fully played: %s",episode)
                        lastEpisode = episode
            if episodeToPlay is None:
                show_episodes_info = client.show_episodes(uri,50,readCount)
                readCount = readCount+len(show_episodes_info["items"])
                _LOGGER.debug("Readcount: %s",readCount)
                for episode in show_episodes_info["items"]:
                    if episodeToPlay is None:
                        playState = episode["resume_point"]
                        if playState["fully_played"]:
                            episodeToPlay = lastEpisode
                            _LOGGER.debug("Found that this is fully played: %s",episode)
                        lastEpisode = episode
            if episodeToPlay is None:
                show_episodes_info = client.show_episodes(uri,50,readCount)
                readCount = readCount+len(show_episodes_info["items"])
                _LOGGER.debug("Readcount: %s",readCount)
                for episode in show_episodes_info["items"]:
                    if episodeToPlay is None:
                        playState = episode["resume_point"]
                        if playState["fully_played"]:
                            episodeToPlay = lastEpisode
                            _LOGGER.debug("Found that this is fully played: %s",episode)
                        lastEpisode = episode
            if episodeToPlay is not None:
                _LOGGER.debug("episodeToPlay (found to be the oldest one not yet fully played): %s",episodeToPlay)
                episode_uri = episodeToPlay["external_urls"]["spotify"]
                _LOGGER.debug(
                    "Playing episode using uris (latest podcast playlist)= for uri: %s",
                    episode_uri,
                )
                client.start_playback(device_id=spotify_device_id, uris=[episode_uri])                
            elif show_episodes_info and len(show_episodes_info["items"]) < 0:
                episode_uri = show_episodes_info["items"][0]["external_urls"]["spotify"]
                _LOGGER.debug(
                    "Playing episode using uris (latest podcast playlist)= for uri: %s",
                    episode_uri,
                )
                client.start_playback(device_id=spotify_device_id, uris=[episode_uri])
            else:
                _LOGGER.info("Umm...")
