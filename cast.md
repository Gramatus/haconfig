# Useful info on casting

> https://www.home-assistant.io/integrations/cast/
> https://developers.google.com/cast/docs/reference/messages#MediaInformation

## Casting apps
It’s possible to play with other apps than the default media receiver. To do so, media_content_type should be set to cast, and media_content_id should be a JSON dict with parameters for the app, including the app name.
```
      data:
        media_content_type: cast
        media_content_id: '
          {
            "app_name": "youtube",
            "media_id": "dQw4w9WgXcQ"
          }'
```

## Metadata
Extra media metadata (for example title, subtitle, artist or album name) can be passed into the service and that will be shown on the Chromecast display. For the possible metadata types and values check Google cast documentation > MediaInformation > metadata field.

```
# Play a movie from the internet, with extra metadata provided:
service: media_player.play_media
target:
  entity_id: media_player.chromecast
data:
  media_content_type: "video/mp4"
  media_content_id: "http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
  extra:
    metadata:
      metadataType: 1
      title: "Big Buck Bunny"
      subtitle: "By Blender Foundation, Licensed under the Creative Commons Attribution license"
      images:
        - url: "https://peach.blender.org/wp-content/uploads/watchtrailer.gif"
```

GenericMediaMetadata
Describes a generic media artifact.

Name	Type	Description
metadataType	integer	0  (the only value)
title	string	optional Descriptive title of the content. Player can independently retrieve title using content_id or it can be given by the sender in the Load message
subtitle	string	optional Descriptive subtitle of the content. Player can independently retrieve title using content_id or it can be given by the sender in the Load message
images	Image[]	optional Array of URL(s) to an image associated with the content. The initial value of the field can be provided by the sender in the Load message. Should provide recommended sizes
releaseDate	string (ISO 8601)	optional ISO 8601 date and time this content was released. Player can independently retrieve title using content_id or it can be given by the sender in the Load message
