from mojo.subscriber import registerSubscriberEvent


libKey = lambda s: f"com.adbac.ImagePresets.{s}"

# Subscriber events

imagePresetsManagerEvents = [
    "imagePresetsManagerWillAddPreset",
    "imagePresetsManagerDidAddPreset",
    "imagePresetsManagerWillRemovePreset",
    "imagePresetsManagerDidRemovePreset",
    "imagePresetsManagerDidChangePreset",
]

def imagePresetsManagerEventExtractor(subscriber, info):
    attributes = ["old", "new", "preset"]
    for attribute in attributes:
        data = info["lowLevelEvents"][-1]
        if attribute in data:
            info[attribute] = data[attribute]

for event in imagePresetsManagerEvents:
    documentation = (
        "".join(
            [
                " " + c if c.isupper() else c
                for c in event.replace("imagePresetsManager", "")
            ]
        )
        .lower()
        .strip()
    )
    registerSubscriberEvent(
        subscriberEventName=libKey(event),
        methodName=event,
        lowLevelEventNames=[libKey(event)],
        dispatcher="roboFont",
        documentation=f"Send when the Image Presets Manager {documentation}.",
        eventInfoExtractionFunction=imagePresetsManagerEventExtractor,
        delay=0,
        debug=True,
    )
