from typing import Iterable, Self

import AppKit
from mojo.events import postEvent
from mojo.extensions import (ExtensionBundle, getExtensionDefault,
                             setExtensionDefault)
from mojo.tools import CallbackWrapper
from Quartz import CIFilter


_LIB_KEY = lambda s: f"com.adbac.ImagePresets.{s}"


def normalizeValue(value, sourceRange, targetRange):
    """
    Normalize a value from the current range to the target range.
    Args:
        value: The value to normalize.
        sourceRange (tuple or list): An iterable (min, max) representing the source range of the value.
        targetRange (tuple or list): An iterable (min, max) representing the target range for the value.
    Returns:
        The normalized value.
    """
    sourceMin, sourceMax = sourceRange
    targetMin, targetMax = targetRange

    # Normalize the value to a 0-1 range
    normalizedValue = (value - sourceMin) / (sourceMax - sourceMin)

    # Scale the normalized value to the target range
    scaled_value = normalizedValue * (targetMax - targetMin) + targetMin

    return scaled_value


class RangeDescriptor:
    """"""

    def __init__(self, mini, maxi, default):
        self.min = mini
        self.max = maxi
        self.default = default


class ColorRangeDescriptor:
    """"""

    def __init__(
        self,
        rgbMin,
        rgbMax,
        rgbDefault,
        alphaMin,
        alphaMax,
        alphaDefault,
        singleDefault,
    ):
        self.rgbRange = RangeDescriptor(rgbMin, rgbMax, rgbDefault)
        self.alphaRange = RangeDescriptor(alphaMin, alphaMax, alphaDefault)
        self.singleDefault = singleDefault


class RGBAColor:
    """"""

    _attrs = ("red", "green", "blue", "alpha")

    def __init__(self, r, g, b, a):
        self.red = r
        self.green = g
        self.blue = b
        self.alpha = a

    def __iter__(self):
        yield self.red
        yield self.green
        yield self.blue
        yield self.alpha

    def __len__(self):
        return 4

    def __getitem__(self, index):
        if isinstance(index, slice):
            return tuple(self)[index]
        if index == 0:
            return self.red
        if index == 1:
            return self.green
        if index == 2:
            return self.blue
        if index == 3:
            return self.alpha
        raise IndexError(f"{self.__class__.__name__} index out of range")

    def __repr__(self):
        return f"RGBA({self.red}, {self.green}, {self.blue}, {self.alpha})"

    def normalized(self):
        color = self.copy()
        for attr in self._attrs:
            if attr == "alpha":
                color.alpha = normalizeValue(color.alpha, (0, 100), (0, 1))
            else:
                setattr(
                    color, attr, normalizeValue(getattr(color, attr), (0, 255), (0, 1))
                )
        return color

    def normalize(self):
        normalizedColor = self.normalized()
        for attr in self._attrs:
            setattr(self, attr, getattr(normalizedColor, attr))
    
    def denormalized(self):
        color = self.copy()
        for attr in self._attrs:
            if attr == "alpha":
                color.alpha = normalizeValue(color.alpha, (0, 1), (0, 100))
            else:
                setattr(
                    color, attr, normalizeValue(getattr(color, attr), (0, 1), (0, 255))
                )
        return color

    def denormalize(self):
        denormalizedColor = self.denormalized()
        for attr in self._attrs:
            setattr(self, attr, getattr(denormalizedColor, attr))

    def copy(self):
        cls = type(self)
        return cls(self.red, self.green, self.blue, self.alpha)


class ImagePreset:
    """
    An object storing the data of an image preset
    """

    filterDefaults = dict(
        brightness=RangeDescriptor(-100, 100, 0),
        contrast=RangeDescriptor(25, 400, 100),
        saturation=RangeDescriptor(0, 200, 100),
        sharpness=RangeDescriptor(0, 200, 0),
        color=ColorRangeDescriptor(0, 255, 0, 0, 100, 100, None),
    )

    factoryPresets = {
        "Black & White": dict(
            brightness=0,
            contrast=100,
            saturation=100,
            sharpness=0,
            color=(0, 0, 0, 100),
        ),
        "Black & White - 40%": dict(
            brightness=0,
            contrast=100,
            saturation=100,
            sharpness=0,
            color=(0, 0, 0, 40),
        ),
        "Red": dict(
            brightness=0,
            contrast=100,
            saturation=100,
            sharpness=0,
            color=(255, 0, 0, 100),
        ),
        "Green": dict(
            brightness=0,
            contrast=100,
            saturation=100,
            sharpness=0,
            color=(0, 255, 0, 100),
        ),
        "Blue": dict(
            brightness=0,
            contrast=100,
            saturation=100,
            sharpness=0,
            color=(0, 0, 255, 100),
        ),
    }

    _filterAttrs = ("brightness", "contrast", "saturation", "sharpness", "color")
    _attrs = ("name", *_filterAttrs)

    def __init__(
        self,
        name: str,
        brightness=0,
        contrast=100,
        saturation=100,
        sharpness=0,
        color=None,
        denormalizeValues=False,
        saveToDefaults=False,
    ):
        self._holdEvents = True
        self._addedToManager = False

        # Initialize private attributes to avoid AttributeError
        self._name = None
        self._brightness = None
        self._contrast = None
        self._saturation = None
        self._sharpness = None
        self._color = None

        # Set attributes using setters
        self.name = name
        self.brightness = (
            self._convertFilterValueToUserValue("brightness", brightness)
            if denormalizeValues
            else brightness
        )
        self.contrast = (
            self._convertFilterValueToUserValue("contrast", contrast)
            if denormalizeValues
            else contrast
        )
        self.saturation = (
            self._convertFilterValueToUserValue("saturation", saturation)
            if denormalizeValues
            else saturation
        )
        self.sharpness = (
            self._convertFilterValueToUserValue("sharpness", sharpness)
            if denormalizeValues
            else sharpness
        )
        self.color = (
            self._convertFilterValueToUserValue("color", color)
            if denormalizeValues
            else color
        )
        self._menuItemTargets = []
        self._holdEvents = False
        if saveToDefaults:
            self.saveToDefaults()

    def __repr__(self):
        return (
            self.__class__.__name__ + "(\n    "
            + ",\n    ".join(f"{attr}={getattr(self, attr)!r}" for attr in self._attrs)
            + "\n)"
        )

    @classmethod
    def getFactoryPresets(cls):
        factoryPresets = [
            cls.fromDict(dict(**data, name=name))
            for name, data in cls.factoryPresets.items()
        ]
        return tuple(factoryPresets)

    def _setFilterValueByName(self, name: str, value):
        r = self.filterDefaults[name]
        attr = f"_{name}"
        oldDict = self.asDict()
        if value is None:
            setattr(self, attr, r.default)
        else:
            assert (
                r.min <= value <= r.max
            ), f"{name.capitalize()} value must be comprised between {r.min} and {r.max}"
            setattr(self, attr, value)
        self._saveDefaultsIfAddedToManager()
        if not self._holdEvents:
            postEvent(
                "imagePresetsManagerDidChangePreset",
                old=oldDict,
                new=self.asDict(),
                preset=self,
            )

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        assert isinstance(value, str), "Name must be a string"
        oldDict = self.asDict()
        self._name = value
        self._saveDefaultsIfAddedToManager()
        if not self._holdEvents:
            postEvent(
                "imagePresetsManagerDidChangePreset",
                old=oldDict,
                new=self.asDict(),
                preset=self,
            )

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._setFilterValueByName("brightness", value)

    @property
    def contrast(self):
        return self._contrast

    @contrast.setter
    def contrast(self, value):
        self._setFilterValueByName("contrast", value)

    @property
    def saturation(self):
        return self._saturation

    @saturation.setter
    def saturation(self, value):
        self._setFilterValueByName("saturation", value)

    @property
    def sharpness(self):
        return self._sharpness

    @sharpness.setter
    def sharpness(self, value):
        self._setFilterValueByName("sharpness", value)

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, value):
        oldDict = self.asDict()
        colorRange = self.filterDefaults["color"]
        rgbRange = colorRange.rgbRange
        alphaRange = colorRange.alphaRange
        if isinstance(value, RGBAColor) or value is None:
            self._color = value
        else:
            assert (
                isinstance(value, Iterable) and len(value) == 4
            ), "Color must be an RGBA iterable"
            assert (
                all(rgbRange.min <= v <= rgbRange.max for v in value[:3])
                and alphaRange.min <= value[3] <= alphaRange.max
            ), f"RGB values must be comprised between {rgbRange.min} and {rgbRange.max}, and alpha value between {alphaRange.min} and {alphaRange.max}"
            self._color = RGBAColor(*value)
        self._saveDefaultsIfAddedToManager()
        if not self._holdEvents:
            postEvent(
                "imagePresetsManagerDidChangePreset",
                old=oldDict,
                new=self.asDict(),
                preset=self,
            )

    @classmethod
    def fromDict(cls, sourceDict: dict):
        # Use a shallow copy so we don't mutate the caller's dict
        src = dict(sourceDict)

        # Support old preset dict format: only convert when enableColor is True.
        if "enableColor" in src:
            if src.get("enableColor"):
                # build color tuple from components (use defaults if missing)
                color = (
                    src.pop("red", 0),
                    src.pop("green", 0),
                    src.pop("blue", 0),
                    src.pop("alpha", 255),
                )
                src["color"] = color
            # remove the legacy flag in either case but don't set color to None
            src.pop("enableColor", None)

        # Initialize new preset instance
        preset = cls(**src)
        return preset

    @classmethod
    def fromImage(cls, image, name: str):
        preset = cls(
            name=name,
            brightness=image.brightness,
            contrast=image.contrast,
            saturation=image.saturation,
            sharpness=image.sharpness,
            color=image.color,
            denormalizeValues=True,
        )
        return preset

    def asDict(self, includeName=True) -> dict:
        d = {}
        for attr in self._filterAttrs:
            value = getattr(self, attr)
            if attr == "color" and value is not None:
                value = tuple(value)
            d[attr] = value
        if includeName:
            d["name"] = self.name
        return d

    _filterConversionDivisionDict = dict(
        saturation=100,
        brightness=100,
        contrast=100,
        sharpness=100,
    )

    def _convertUserValueToFilterValue(
        self, filterName, userValue=None, ignoreColorOpacity=True
    ):
        userValue = userValue if userValue is not None else getattr(self, filterName)
        if filterName == "color":
            return (
                RGBAColor(
                    *userValue[:3], (100 if ignoreColorOpacity else userValue[3])
                ).normalized()
                if userValue is not None
                else None
            )
        else:
            return userValue / self._filterConversionDivisionDict[filterName]

    def _convertFilterValueToUserValue(
        self, filterName, filterValue, ignoreColorOpacity=True
    ):
        if filterName == "color":
            return (
                RGBAColor(
                    *filterValue[:3], (1 if ignoreColorOpacity else filterValue[3])
                ).denormalized()
                if filterValue is not None
                else None
            )
        else:
            return filterValue * self._filterConversionDivisionDict[filterName]

    def asMerzFilterDicts(self):
        filters = [
            dict(
                name="colorControls",
                filterType="colorControls",
                saturation=self._convertUserValueToFilterValue("saturation"),
                brightness=self._convertUserValueToFilterValue("brightness"),
                contrast=self._convertUserValueToFilterValue("contrast"),
            ),
            dict(
                name="noiseReduction",
                filterType="noiseReduction",
                noiseLevel=0,
                sharpness=self._convertUserValueToFilterValue("sharpness"),
            ),
        ]
        if self.color is not None:
            filters.append(dict(
                name="falseColor",
                filterType="falseColor",
                color0=self._convertUserValueToFilterValue("color"),
                color1=(1, 1, 1, 1),
            ))
        return filters

    def applyToMerzLayer(self, layer, overwriteFilters=False):
        if hasattr(layer, "clearFilters") and hasattr(layer, "appendFilter"):
            if overwriteFilters:
                layer.setFilters([])
            filterDicts = self.asMerzFilterDicts()
            for fd in filterDicts:
                layer.appendFilter(fd)
            if hasattr(layer, "setOpacity"):
                if self.color is not None:
                    layer.setOpacity(self.color.normalized().alpha)
                else:
                    layer.setOpacity(1)

    def applyToImage(self, image):
        if not image:
            return
        image.prepareUndo(f"Apply Image Preset {self.name!r}")
        color = self._convertUserValueToFilterValue("color", ignoreColorOpacity=False)
        image.color = tuple(color) if color is not None else None
        image.brightness = self._convertUserValueToFilterValue("brightness")
        image.contrast = self._convertUserValueToFilterValue("contrast")
        image.saturation = self._convertUserValueToFilterValue("saturation")
        image.sharpness = self._convertUserValueToFilterValue("sharpness")
        image.performUndo()

    def _saveDefaultsIfAddedToManager(self):
        if self._addedToManager:
            ImagePresetsManager.savePresetsToDefaults()

    def saveToDefaults(self):
        if ImagePresetsManager.hasPresetName(self.name):
            ImagePresetsManager.savePresetsToDefaults()
        else:
            ImagePresetsManager.addPreset(self)

    def removeFromDefaults(self):
        ImagePresetsManager.removePreset(self)

    def copy(self):
        cls = type(self)
        return cls.fromDict(self.asDict())

    # UI methods

    def makeMenuItem(self, callback=None):
        # initialize menu item
        target = None
        action = ""
        if callback is not None:
            target = CallbackWrapper(callback)
            self._menuItemTargets.append(target)
            action = "action:"
        item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            self.name, action, ""
        )
        if target is not None:
            item.setTarget_(target)

        # extract placeholder image
        image = ExtensionBundle("ImagePresets").get("placeholder")
        size = image.size()
        scale = 16 / size.height
        image.setSize_((size.width * scale, size.height * scale))
        size = image.size()

        # create a rounded rectangle path
        roundedRectPath = (
            AppKit.NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                AppKit.NSMakeRect(0, 0, size.width, size.height), 2, 2
            )
        )

        # create a new image with rounded corners
        adjustedImage = AppKit.NSImage.alloc().initWithSize_((size.width, size.height))
        adjustedImage.lockFocus()
        roundedRectPath.addClip()
        image.drawAtPoint_fromRect_operation_fraction_(
            AppKit.NSZeroPoint,
            AppKit.NSMakeRect(0, 0, size.width, size.height),
            AppKit.NSCompositingOperationSourceOver,
            1.0,
        )
        adjustedImage.unlockFocus()

        # apply false color transformation
        if self.color is not None:
            falseColorFilter = CIFilter.filterWithName_("CIFalseColor")
            falseColorFilter.setDefaults()
            falseColorFilter.setValue_forKey_(
                AppKit.CIImage.imageWithData_(adjustedImage.TIFFRepresentation()),
                "inputImage",
            )
            falseColorFilter.setValue_forKey_(
                AppKit.CIColor.colorWithRed_green_blue_alpha_(*self.color.normalized()), "inputColor0"
            )
            falseColorFilter.setValue_forKey_(
                AppKit.CIColor.colorWithRed_green_blue_alpha_(1, 1, 1, 1), "inputColor1"
            )
            adjustedImage = falseColorFilter.valueForKey_("outputImage")

        # apply brightness, contrast and saturation adjustments
        colorControlsFilter = CIFilter.filterWithName_("CIColorControls")
        colorControlsFilter.setDefaults()
        colorControlsFilter.setValue_forKey_(adjustedImage, "inputImage")
        colorControlsFilter.setValue_forKey_(
            self._convertUserValueToFilterValue("brightness"), "inputBrightness"
        )
        colorControlsFilter.setValue_forKey_(
            self._convertUserValueToFilterValue("contrast"), "inputContrast"
        )
        colorControlsFilter.setValue_forKey_(
            self._convertUserValueToFilterValue("saturation"), "inputSaturation"
        )
        adjustedImage = colorControlsFilter.valueForKey_("outputImage")

        noiseReductionFilter = CIFilter.filterWithName_("CINoiseReduction")
        noiseReductionFilter.setDefaults()
        noiseReductionFilter.setValue_forKey_(adjustedImage, "inputImage")
        noiseReductionFilter.setValue_forKey_(0, "inputNoiseLevel")
        noiseReductionFilter.setValue_forKey_(
            self._convertUserValueToFilterValue("sharpness"), "inputSharpness"
        )
        adjustedImage = noiseReductionFilter.valueForKey_("outputImage")

        # convert CIImage back to NSImage
        rep = AppKit.NSCIImageRep.imageRepWithCIImage_(adjustedImage)
        transformedImage = AppKit.NSImage.alloc().initWithSize_(rep.size())
        transformedImage.addRepresentation_(rep)
        transformedImage.setSize_(size)

        # set menu item image
        item.setImage_(transformedImage)
        item.setRepresentedObject_(self)

        # set callback
        if callback is not None:
            ...

        return item


class ImagePresetsManager:
    """"""

    presets = []
    for name, data in getExtensionDefault(_LIB_KEY("presets"), fallback={}).items():
        __p = ImagePreset.fromDict(dict(**data, name=name))
        __p._addedToManager = True
        presets.append(__p)

    @classmethod
    def hasPresets(cls):
        return bool(getExtensionDefault(_LIB_KEY("presets"), fallback=False))

    @classmethod
    def hasPresetName(cls, name: str):
        for p in cls.presets:
            if p.name == name:
                return True
        return False

    @classmethod
    def getPresetByName(cls, name: str):
        for p in cls.presets:
            if p.name == name:
                return p
        return None

    @classmethod
    def addPreset(cls, preset: ImagePreset):
        assert preset.name not in [p.name for p in cls.presets], f"{preset.name!r} is a name already used by another preset"
        postEvent("imagePresetsManagerWillAddPreset", preset=preset)
        cls.presets.append(preset)
        preset._addedToManager = True
        cls.savePresetsToDefaults()
        postEvent("imagePresetsManagerDidAddPreset", preset=preset)

    @classmethod
    def removePreset(cls, preset: ImagePreset):
        if preset in cls.presets:
            postEvent("imagePresetsManagerWillRemovePreset", preset=preset)
            preset._addedToManager = False
            cls.presets.remove(preset)
            cls.savePresetsToDefaults()
            postEvent("imagePresetsManagerDidRemovePreset", preset=preset)

    @classmethod
    def removePresetByName(cls, presetName: str):
        preset = cls.getPresetByName(presetName)
        if preset is not None:
            cls.removePreset(preset)

    @classmethod
    def reloadPresets(cls):
        presets = [
            ImagePreset.fromDict(dict(**data, name=name))
            for name, data in getExtensionDefault(_LIB_KEY("presets"), fallback={}).items()
        ]
        for p in presets:
            p._addedToManager = True
        cls.presets = presets
        cls.savePresetsToDefaults()

    @classmethod
    def loadFactoryPresets(cls, overwrite=True):
        if overwrite:
            cls.presets = []
        for preset in ImagePreset.getFactoryPresets():
            try:
                cls.addPreset(preset)
            except:
                pass
        cls.savePresetsToDefaults()

    @classmethod
    def savePresetsToDefaults(cls):
        data = {preset.name: preset.asDict(includeName=False) for preset in cls.presets}
        setExtensionDefault(_LIB_KEY("presets"), data)

    # UI methods

    @classmethod
    def makeMenuItems(cls, includeNone=True, callback=None):
        if includeNone:
            firstItem = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_("None", "", "")
            firstItem.setRepresentedObject_(None)
            items = [firstItem]
        else:
            items  =[]
        for preset in cls.presets:
            items.append(preset.makeMenuItem(callback))
        return items
