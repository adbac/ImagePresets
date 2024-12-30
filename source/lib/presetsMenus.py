from mojo.extensions import getExtensionDefault, setExtensionDefault
from mojo.subscriber import Subscriber, registerGlyphEditorSubscriber
from common import normalizeColor, KEY, BASE_PRESETS

testPresets = getExtensionDefault(KEY, fallback=None)
if testPresets is None:
    setExtensionDefault(KEY, BASE_PRESETS)

class ImagePresetsMenuSubscriber(Subscriber):

    debug = True

    def glyphEditorWantsImageContextualMenuItems(self, info):
        self.addMenuItems(info)

    def glyphEditorWantsContextualMenuItems(self, info):
        self.addMenuItems(info)

    def addMenuItems(self, info):
        presets = getExtensionDefault(KEY, fallback={})
        if not presets:
            return
        menuItems = [
            ("Apply Image Preset", [
                (name, self.applyPreset) for name in presets.keys()
            ])
        ]
        info["itemDescriptions"].extend(menuItems)

    def applyPreset(self, sender):
        
        presets = getExtensionDefault(KEY, fallback={})
        if not presets:
            return
        
        presetName = sender.title()
        preset = presets[presetName]

        glyphEditor = self.getGlyphEditor()
        glyph = glyphEditor.getGlyph()
        image = glyph.image
        if image is None:
            return
        
        image.color = normalizeColor((preset["red"], preset["green"], preset["blue"], preset["alpha"])) if preset["enableColor"] else None
        image.brightness = preset["brightness"] / 100
        image.contrast = preset["contrast"] / 100
        image.saturation = preset["saturation"] / 100
        image.sharpness = preset["sharpness"] / 100

registerGlyphEditorSubscriber(ImagePresetsMenuSubscriber)