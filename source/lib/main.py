import imagePresetsLib  # make it available everywhere else
from mojo.subscriber import (Subscriber, registerGlyphEditorSubscriber,
                             registerSubscriberEvent)

manager = imagePresetsLib.ImagePresetsManager

if not manager.hasPresets():
    manager.loadFactoryPresets()


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


# Glyph Editor contextual submenus

class ImagePresetsMenuSubscriber(Subscriber):

    debug = True

    def glyphEditorWantsImageContextualMenuItems(self, info):
        self.addMenuItems(info)

    def glyphEditorWantsContextualMenuItems(self, info):
        self.addMenuItems(info)

    def addMenuItems(self, info):
        presets = manager.presets
        if not presets:
            return
        menuItems = [
            (
                "Apply Image Preset",
                imagePresetsLib.ImagePresetsManager.makeMenuItems(
                    includeNone=False,
                    callback=self.applyPreset,
                ),
            )
        ]
        info["itemDescriptions"].extend(menuItems)

    def applyPreset(self, sender):
        if not manager.presets:
            return
        preset = manager.getPresetByName(sender.title())
        preset.applyToImage(self.getGlyphEditor().getGlyph().image)


registerGlyphEditorSubscriber(ImagePresetsMenuSubscriber)
