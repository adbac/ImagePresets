import ezui
from imagePresetsLib import ImagePreset, ImagePresetsManager, RGBAColor
from mojo.extensions import ExtensionBundle


class ImagePresetsController(ezui.WindowController):

    def build(self):

        self.filterDefaults = ImagePreset.filterDefaults

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
        >>> : Brightness
        >>> ---X--- [__]        @brightness
        >>> : Contrast
        >>> ---X--- [__]        @contrast
        >>> : Saturation
        >>> ---X--- [__]        @saturation
        >>> : Sharpness
        >>> ---X--- [__]        @sharpness
        >> * TwoColumnForm      @form2
        >>> :
        >>> [ ] Use false color @useFalseColor
        >>> : Color
        >>> * ColorWell         @color
        """

        self.currentPreset = None

        self.showOriginal = False

        titleColumnWidth = 70
        itemColumnWidth = 130

        self.defaultColor = (
            self.filterDefaults["color"].rgbRange.default,
            self.filterDefaults["color"].rgbRange.default,
            self.filterDefaults["color"].rgbRange.default,
            self.filterDefaults["color"].alphaRange.default,
        )

        descriptionData=dict(
            presetsList=dict(
                width=175,
                items=[
                    dict(presetName=p.name) for p in ImagePresetsManager.presets
                ],
                columnDescriptions=[dict(
                    identifier="presetName",
                )],
                allowsEmptySelection=True,
                allowsMultipleSelection=False,
            ),
            formsHStack=dict(
                alignment="leading",
            ),
            form1=dict(
                titleColumnWidth=titleColumnWidth,
                itemColumnWidth=itemColumnWidth,
                height="fit",
            ),
            form2=dict(
                titleColumnWidth=titleColumnWidth,
                itemColumnWidth=itemColumnWidth,
                height="fit",
            ),
            brightness=dict(
                minValue=self.filterDefaults["brightness"].min,
                maxValue=self.filterDefaults["brightness"].max,
                value=self.filterDefaults["brightness"].default,
                tickMarks=1,
                valueType="integer",
            ),
            contrast=dict(
                minValue=self.filterDefaults["contrast"].min,
                maxValue=self.filterDefaults["contrast"].max,
                value=self.filterDefaults["contrast"].default,
                tickMarks=1,
                valueType="integer",
            ),
            saturation=dict(
                minValue=self.filterDefaults["saturation"].min,
                maxValue=self.filterDefaults["saturation"].max,
                value=self.filterDefaults["saturation"].default,
                tickMarks=1,
                valueType="integer",
            ),
            sharpness=dict(
                minValue=self.filterDefaults["sharpness"].min,
                maxValue=self.filterDefaults["sharpness"].max,
                value=self.filterDefaults["sharpness"].default,
                tickMarks=1,
                valueType="integer",
            ),
            color=dict(
                color=self.defaultColor,
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

        self.w.getItem("color").enable(False)

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

    def updateFiltersPreview(self):
        currentPreset = (
            self.currentPreset
            if self.currentPreset is not None
            else ImagePreset(name="default")
        )
        if self.showOriginal:
            self.imageLayer.setFilters([])
            self.imageLayer.setOpacity(1)
        else:
            currentPreset.applyToMerzLayer(self.imageLayer, overwriteFilters=True)

    def brightnessCallback(self, sender):
        self.currentPreset.brightness = sender.get()
        self.updateFiltersPreview()

    def contrastCallback(self, sender):
        self.currentPreset.contrast = sender.get()
        self.updateFiltersPreview()

    def saturationCallback(self, sender):
        self.currentPreset.saturation = sender.get()
        self.updateFiltersPreview()

    def sharpnessCallback(self, sender):
        self.currentPreset.sharpness = sender.get()
        self.updateFiltersPreview()

    def useFalseColorCallback(self, sender):
        self.w.getItem("color").enable(sender.get())
        if sender.get():
            self.colorCallback(self.w.getItem("color"))
        else:
            self.currentPreset.color = None
        self.updateFiltersPreview()

    def colorCallback(self, sender):
        self.currentPreset.color = RGBAColor(*sender.get()).denormalized()
        self.updateFiltersPreview()

    def showOriginalCallback(self, sender):
        self.showOriginal = sender.get()
        self.updateFiltersPreview()

    def setUIFieldsState(self, state):
        for key in self.filterDefaults.keys():
            self.w.getItem(key).enable(state)
        self.w.getItem("useFalseColor").enable(state)
        self.w.getItem("showOriginal").enable(state)
        self.w.getItem("presetName").enable(state)

    def forceUpdateUIFields(self):
        if self.currentPreset is None:
            preset = ImagePreset(name="")
            currentPresetIsNone = True
        else:
            preset = self.currentPreset
            currentPresetIsNone = False
        for key in self.filterDefaults.keys():
            if key == "color":
                self.w.getItem(key).set(
                    tuple(preset.color.normalized())
                    if preset.color is not None
                    else self.defaultColor
                )
            else:
                self.w.getItem(key).set(getattr(preset, key))
        if preset.color is not None:
            self.w.getItem("useFalseColor").set(True)
        self.w.getItem("presetName").set(preset.name)
        if currentPresetIsNone:
            self.setUIFieldsState(False)
        else:
            self.setUIFieldsState(True)
            self.useFalseColorCallback(self.w.getItem("useFalseColor"))

    def presetsListAddRemoveButtonAddCallback(self, sender):
        table = self.w.getItem("presetsList")
        name = "New Preset"
        baseName = name
        counter = 1
        while name in (p.name for p in ImagePresetsManager.presets):
            name = f"{baseName} {counter}"
            counter += 1
        table.appendItems([dict(presetName=name)])
        newPreset = ImagePreset(name=name, saveToDefaults=True)
        table.setSelectedIndexes([len(ImagePresetsManager.presets) - 1,])

    def presetsListAddRemoveButtonRemoveCallback(self, sender):
        table = self.w.getItem("presetsList")
        selectedIndex = table.getSelectedIndexes()
        if not selectedIndex:
            return
        else:
            index = selectedIndex[0]
        ImagePresetsManager.removePresetByName(self.currentPreset.name)
        presets = ImagePresetsManager.presets
        table.removeSelectedItems()
        if presets:
            table.setSelectedIndexes([index,] if index < len(presets) else [index - 1,])
        else:
            self.currentPreset = None
        self.forceUpdateUIFields()

    def presetsListSelectionCallback(self, sender):
        if not self.initialized:
            return
        if not sender.getSelectedItems():
            self.currentPreset = None
        else:
            self.currentPreset = ImagePresetsManager.getPresetByName(
                sender.getSelectedItems()[0]["presetName"]
            )
        self.forceUpdateUIFields()
        self.updateFiltersPreview()

    def presetNameCallback(self, sender):
        newName = sender.get()
        if ImagePresetsManager.hasPresetName(newName) and newName != self.currentPreset.name:
            self.showMessage(
                messageText="This name is already used by another preset",
                alertStyle="informational",
                icon=self.extensionBundle.get("icon"),
            )
            sender.set(self.currentPreset.name)
            return
        self.currentPreset.name = newName
        table = self.w.getItem("presetsList")
        index = table.getSelectedIndexes()[0]
        table.setItem(index, dict(presetName=newName))
        table.setSelectedIndexes([index,])

ImagePresetsController()
