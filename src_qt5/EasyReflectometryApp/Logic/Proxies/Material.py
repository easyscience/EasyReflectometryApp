__author__ = 'github.com/arm61'

import matplotlib
from matplotlib import colors

from PySide2.QtCore import QObject
from PySide2.QtCore import Signal
from PySide2.QtCore import Property
from PySide2.QtCore import Slot

from easyscience import global_object
from easyscience.utils.io.xml import XMLSerializer

from easyreflectometry.sample import MaterialCollection

COLOURMAP = matplotlib.colormaps['Blues'].resampled(100)
MIN_SLD = -3
MAX_SLD = 15


class MaterialProxy(QObject):

    materialsChanged = Signal()
    materialsIndexChanged = Signal()
    materialsAsXmlChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

        self._materials_as_xml = ""
        self._materials = MaterialCollection()

        self._current_materials_index = 0

        self.materialsChanged.connect(self._setMaterialsAsXml)

    # # #
    # Setters and getters
    # # #

    @property
    def materialsAsObj(self):
        """
        :return: A list of the materials to be converted to XML.
        """
        _materials_as_obj = []
        for i in self._materials:
            dictionary = i.as_dict(skip=['interface', 'min', 'max', 'error', 'fixed', 'description', 'url'])
            dictionary['color'] = colors.rgb2hex(
                COLOURMAP((dictionary['sld']['value'] - MIN_SLD) / (MAX_SLD - MIN_SLD)))
            _materials_as_obj.append(dictionary)
        return _materials_as_obj

    @property
    def last_material(self):
        if len(self._materials) == 0:
            self.addNewMaterials()
        return self._materials[-1]

    @Property(str, notify=materialsAsXmlChanged)
    def materialsAsXml(self):
        """
        :return: The list of materials as XML.
        """
        return self._materials_as_xml

    def _setMaterialsAsXml(self):
        """
        Sets the _materials_as_xml object. 
        """
        print(">>> _setMaterialsAsXml")
        self._materials_as_xml = XMLSerializer().encode({"item":self.materialsAsObj}, data_only=True)
        self.materialsAsXmlChanged.emit()

    @Property(list, notify=materialsChanged)
    def materialsName(self):
        """
        :return: A list of just the materials names
        """
        return self._materials.names

    @Property(int, notify=materialsIndexChanged)
    def currentMaterialsIndex(self):
        """
        :return: The index of the currently selected material.
        """
        return self._current_materials_index

    @currentMaterialsIndex.setter
    def currentMaterialsIndex(self, new_index: int):
        """
        Sets the _current_materials_index integer.
        """
        if self._current_materials_index == new_index or new_index == -1:
            return
        self._current_materials_index = new_index

    # # #
    # Slot
    # # #

    @Slot()
    def addNewMaterials(self):
        """
        Add a new material.
        """
        global_object.stack.enabled = False
        self._materials.add_material()

        global_object.stack.enabled = True
        self.materialsChanged.emit()
        self.parent.layersMaterialsChanged.emit()

    @Slot()
    def duplicateSelectedMaterials(self):
        """
        Duplicate the currently selected material.
        """
        global_object.stack.enabled = False
        self._materials.duplicate_material(self.currentMaterialsIndex)
        global_object.stack.enabled = True
        self.materialsChanged.emit()
        self.parent.layersMaterialsChanged.emit()

    @Slot(str)
    def removeMaterials(self, i: str):
        """
        Remove a material from the materials list.

        :param i: Index of the material
        """
        self._materials.remove_material(int(i))
        self.materialsChanged.emit()
        self.parent.layersMaterialsChanged.emit()

    @Slot()
    def moveSelectedMaterialsUp(self):
        """
        Move the currently selected material up.
        """
        self._materials.move_material_up(self.currentMaterialsIndex)
        self.materialsChanged.emit()
        self.parent.layersMaterialsChanged.emit()

    @Slot()
    def moveSelectedMaterialsDown(self):
        """
        Move the currently selected material down.
        """
        self._materials.move_material_down(self.currentMaterialsIndex)
        self.materialsChanged.emit()
        self.parent.layersMaterialsChanged.emit()

    @Slot(str)
    def setCurrentMaterialsName(self, name: str):
        """
        Sets the name of the currently selected material.

        :param sld: New material name
        """
        if self._materials[self.currentMaterialsIndex].name == name:
            return
        self._materials[self.currentMaterialsIndex].name = name
        self.materialsChanged.emit()
        self.parent.layersMaterialsChanged.emit()

    @Slot(float)
    def setCurrentMaterialsSld(self, sld: float):
        """
        Sets the SLD of the currently selected material.

        :param sld: New SLD value
        """
        if self._materials[self.currentMaterialsIndex].sld.value == sld:
            return
        self._materials[self.currentMaterialsIndex].sld.value = sld
        self.materialsChanged.emit()
        self.parent.layersChanged.emit()

    @Slot(float)
    def setCurrentMaterialsISld(self, isld: float):
        """
        Sets the iSLD of the currently selected material.

        :param isld: New iSLD value
        """
        if self._materials[self.currentMaterialsIndex].isld.value == isld:
            return
        self._materials[self.currentMaterialsIndex].isld.value = isld
        self.materialsChanged.emit()
        self.parent.layersChanged.emit()

    def resetMaterial(self):
        """
        Reset the materials to the default.
        """
        self._materials = MaterialCollection()
        self.materialsChanged.emit()
        self.parent.layersChanged.emit()
