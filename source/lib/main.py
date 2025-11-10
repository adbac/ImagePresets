import imagePresetsLib  # make it available everywhere else
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber


manager = imagePresetsLib.ImagePresetsManager

if not manager.hasPresets():
    manager.loadFactoryPresets()


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
