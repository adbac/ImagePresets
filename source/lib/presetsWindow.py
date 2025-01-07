import ezui
import AppKit
from mojo.extensions import getExtensionDefault, setExtensionDefault, ExtensionBundle
from common import normalizeColor, KEY, BASE_PRESETS

class ImagePresetsController(ezui.WindowController):

    def build(self):

        self.defaults = dict(
            brightness=0,
            contrast=100,
            saturation=100,
            sharpness=0,
            enableColor=False,
            red=0,
            green=0,
            blue=0,
            alpha=100,
        )

        self.presets = getExtensionDefault(KEY, fallback=BASE_PRESETS)

        content = """
        = HorizontalStack

        |-----------------------------| @presetsList
        |                             |
        |-----------------------------|
        > (+-)    @presetsListAddRemoveButton

        * VerticalStack         @settingsVStack
        > Name: [__]            @presetName
        > * MerzView            @imagePreview
        > * HorizontalStack     @formsHStack
        >> * TwoColumnForm      @form1
        >>> :
        >>> [ ] Show original   @showOriginal
        >>> : Brightness:
        >>> ---X--- [__]        @brightness
        >>> : Contrast:
        >>> ---X--- [__]        @contrast
        >>> : Saturation:
        >>> ---X--- [__]        @saturation
        >>> : Sharpness:
        >>> ---X--- [__]        @sharpness
        >> * TwoColumnForm      @form2
        >>> :
        >>> [ ] Color           @enableColor
        >>> : Red 🔴
        >>> ---X--- [__]        @red
        >>> : Green 🟢
        >>> ---X--- [__]        @green
        >>> : Blue 🔵
        >>> ---X--- [__]        @blue
        >>> : Alpha 💧
        >>> ---X--- [__]        @alpha
        """

        self.currentPreset = None

        self.showOriginal = False

        titleColumnWidth = 70
        itemColumnWidth = 130

        colorInputSettings = dict(
            minValue=0,
            maxValue=255,
            value=self.defaults["red"],
            tickMarks=3,
            valueType="integer",
        )

        descriptionData=dict(
            presetsList=dict(
                width=175,
                items=[
                    dict(presetName=name) for name in self.presets.keys()
                ],
                columnDescriptions=[dict(
                    identifier="presetName",
                )],
                allowsEmptySelection=True,
                allowsMultipleSelection=False,
            ),
            form1=dict(
                titleColumnWidth=titleColumnWidth,
                itemColumnWidth=itemColumnWidth,
            ),
            form2=dict(
                titleColumnWidth=titleColumnWidth,
                itemColumnWidth=itemColumnWidth,
            ),
            brightness=dict(
                minValue=-100,
                maxValue=100,
                value=self.defaults["brightness"],
                tickMarks=1,
                valueType="integer",
            ),
            contrast=dict(
                minValue=25,
                maxValue=400,
                value=self.defaults["contrast"],
                tickMarks=1,
                valueType="integer",
            ),
            saturation=dict(
                minValue=0,
                maxValue=200,
                value=self.defaults["saturation"],
                tickMarks=1,
                valueType="integer",
            ),
            sharpness=dict(
                minValue=0,
                maxValue=200,
                value=self.defaults["sharpness"],
                tickMarks=1,
                valueType="integer",
            ),
            red=colorInputSettings,
            green=colorInputSettings,
            blue=colorInputSettings,
            alpha=dict(
                minValue=0,
                maxValue=100,
                value=self.defaults["alpha"],
                tickMarks=3,
                valueType="integer",
            ),
            settingsVStack=dict(
                spacing=18,
            ),
            presetName=dict(
                continuous=False,
            ),
            imagePreview=dict(
                width="fit",
                height=280,
                backgroundColor=(1, 1, 1, 1),
            ),
        )

        self.initialized = False

        self.w = ezui.EZWindow(
            title="Image Presets",
            size=("auto", 200),
            content=content,
            descriptionData=descriptionData,
            controller=self,
        )

        self.initialized = True

        imagePreview = self.w.getItem("imagePreview")
        merzContainer = imagePreview.getMerzContainer()
        self.imageLayer = merzContainer.appendImageSublayer(
            position=("center", "center"),
            alignment="center",
        )
        self.extensionBundle = ExtensionBundle("ImagePresets")
        image = self.extensionBundle.get("placeholder")
        imWidth, imHeight = image.size()
        scale = 280 / imHeight
        image.setSize_((imWidth * scale, imHeight * scale))
        self.imageLayer.setImage(image)

        self.presetsListSelectionCallback(self.w.getItem("presetsList"))

    def started(self):
        self.w.open()

    def savePresets(self):
        setExtensionDefault("com.adbac.ImagePresets.presets", self.presets)

    def updateFiltersPreview(self, savePresets=True):
        if savePresets:
            self.savePresets()
        currentPreset = self.presets[self.currentPreset] if self.currentPreset else self.defaults.copy()
        filters = [
            dict(
                name="colorControls",
                filterType="colorControls",
                saturation=currentPreset["saturation"] / 100,
                brightness=currentPreset["brightness"] / 100,
                contrast=currentPreset["contrast"] / 100,
            ),
            dict(
                name="noiseReduction",
                filterType="noiseReduction",
                noiseLevel=0,
                sharpness=currentPreset["sharpness"] / 100,
            ),
        ] if not self.showOriginal else []
        if currentPreset["enableColor"] and not self.showOriginal:
            filters.append(dict(
                name="falseColor",
                filterType="falseColor",
                color0=normalizeColor((currentPreset["red"], currentPreset["green"], currentPreset["blue"], 100)),
                color1=(1, 1, 1, 1),
            ))
            self.imageLayer.setOpacity(currentPreset["alpha"] / 100)
        self.imageLayer.setFilters(filters)

    def brightnessCallback(self, sender):
        self.presets[self.currentPreset]["brightness"] = sender.get()
        self.updateFiltersPreview()

    def contrastCallback(self, sender):
        self.presets[self.currentPreset]["contrast"] = sender.get()
        self.updateFiltersPreview()

    def saturationCallback(self, sender):
        self.presets[self.currentPreset]["saturation"] = sender.get()
        self.updateFiltersPreview()

    def sharpnessCallback(self, sender):
        self.presets[self.currentPreset]["sharpness"] = sender.get()
        self.updateFiltersPreview()

    def redCallback(self, sender):
        self.presets[self.currentPreset]["red"] = sender.get()
        self.updateFiltersPreview()

    def greenCallback(self, sender):
        self.presets[self.currentPreset]["green"] = sender.get()
        self.updateFiltersPreview()
    
    def blueCallback(self, sender):
        self.presets[self.currentPreset]["blue"] = sender.get()
        self.updateFiltersPreview()

    def alphaCallback(self, sender):
        self.presets[self.currentPreset]["alpha"] = sender.get()
        self.updateFiltersPreview()

    def enableColorCallback(self, sender):
        self.presets[self.currentPreset]["enableColor"] = sender.get()
        for key in ["red", "green", "blue", "alpha"]:
            self.w.getItem(key).enable(sender.get())
        self.forceUpdatePresetData()

    def showOriginalCallback(self, sender):
        self.showOriginal = sender.get()
        self.updateFiltersPreview()

    def forceUpdatePresetData(self):
        for key in self.defaults.keys():
            self.presets[self.currentPreset][key] = self.w.getItem(key).get()
        self.updateFiltersPreview()

    def setUIFieldsState(self, state):
        for key in self.defaults.keys():
            self.w.getItem(key).enable(state)
        self.w.getItem("showOriginal").enable(state)
        self.w.getItem("presetName").enable(state)

    def forceUpdateUIFields(self):
        if self.currentPreset is None:
            self.setUIFieldsState(False)
            self.w.getItem("presetName").set("")
        else:
            for key in self.defaults.keys():
                self.w.getItem(key).set(self.presets[self.currentPreset][key])
            self.w.getItem("presetName").set(self.currentPreset)
            self.setUIFieldsState(True)
            self.enableColorCallback(self.w.getItem("enableColor"))

    def presetsListAddRemoveButtonAddCallback(self, sender):
        table = self.w.getItem("presetsList")
        name = "New Preset"
        baseName = name
        counter = 1
        while name in self.presets:
            name = f"{baseName} {counter}"
            counter += 1
        item = dict(presetName=name)
        table.appendItems([item])
        self.presets[name] = self.defaults.copy()
        table.setSelectedIndexes([len(self.presets.keys()) - 1,])
        self.savePresets()

    def presetsListAddRemoveButtonRemoveCallback(self, sender):
        table = self.w.getItem("presetsList")
        selectedIndex = table.getSelectedIndexes()
        if not selectedIndex:
            return
        else:
            index = selectedIndex[0]
        self.presets.pop(self.currentPreset)
        table.removeSelectedItems()
        if self.presets:
            table.setSelectedIndexes([index,] if index < len(self.presets.keys()) else [index - 1,])
        else:
            self.currentPreset = None
        self.savePresets()
        self.forceUpdateUIFields()

    def presetsListSelectionCallback(self, sender):
        if not self.initialized:
            return
        if not sender.getSelectedItems():
            self.currentPreset = None
        else:
            self.currentPreset = sender.getSelectedItems()[0]["presetName"]
        self.forceUpdateUIFields()
        self.updateFiltersPreview(savePresets=False)

    def presetNameCallback(self, sender):
        newName = sender.get()
        if newName in self.presets and newName != self.currentPreset:
            self.showMessage(
                messageText="This name is already used by another preset",
                alertStyle="informational",
                icon=self.extensionBundle.get("icon"),
            )
            sender.set(self.currentPreset)
            return
        table = self.w.getItem("presetsList")
        index = table.getSelectedIndexes()[0]
        previousName = self.currentPreset
        self.currentPreset = newName
        settings = self.presets.pop(previousName)
        self.presets[self.currentPreset] = settings
        table.setItem(index, dict(presetName=self.currentPreset))
        table.setSelectedIndexes([index,])
        self.savePresets()

ImagePresetsController()