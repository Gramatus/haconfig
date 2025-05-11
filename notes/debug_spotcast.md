# HUSK!

Music Assistant er alltid et alternativ, om enn ikke like bra som Spotcast...

# Debugging
Test action:

```yaml
action: pyscript.play_playlist_random
data:
  playlistid: 6tmVPMqA41iGssO9gfDBoJ
  device: media_player.godehol
  shuffle_type: No shuffle
  fadein_seconds: 60
  final_volume: 1
```

More logging:
```yaml
action: logger.set_level
data:
  custom_components.spotcast: debug
  spotipy: debug
```
