from easyreflectometry import Project as ProjectLib
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .logic.assemblies import Assemblies as AssembliesLogic
from .logic.layers import Layers as LayersLogic
from .logic.material import Material as MaterialLogic
from .logic.models import Models as ModelsLogic
from .logic.parameters import Parameters as ParametersLogic
from .logic.project import Project as ProjectLogic


class Sample(QObject):
    materialsTableChanged = Signal()
    materialsIndexChanged = Signal()

    modelsTableChanged = Signal()
    modelsIndexChanged = Signal()

    assembliesTableChanged = Signal()
    assembliesIndexChanged = Signal()

    layersChange = Signal()
    layersIndexChanged = Signal()

    qRangeChanged = Signal()

    externalRefreshPlot = Signal()
    externalSampleChanged = Signal()

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._project_lib = project_lib
        self._material_logic = MaterialLogic(project_lib)
        self._models_logic = ModelsLogic(project_lib)
        self._assemblies_logic = AssembliesLogic(project_lib)
        self._layers_logic = LayersLogic(project_lib)
        self._project_logic = ProjectLogic(project_lib)
        self._parameters_logic = ParametersLogic(project_lib)

        self._chached_layers = None

        self.connect_logic()

    def connect_logic(self) -> None:
        self.assembliesIndexChanged.connect(self.layersConnectChanges)

    # # #
    # Materials
    # # #
    @Property('QVariantList', notify=materialsTableChanged)
    def materials(self) -> list[dict[str, str]]:
        return self._material_logic.materials

    @Property(int, notify=materialsIndexChanged)
    def currentMaterialIndex(self) -> int:
        return self._material_logic.index

    @Property('QVariantList', notify=materialsTableChanged)
    def materialNames(self) -> list[str]:
        return self._material_logic.material_names

    @Property(str, notify=materialsIndexChanged)
    def currentMaterialName(self) -> str:
        return self._material_logic.name_at_current_index

    # Setters
    @Slot(int)
    def setCurrentMaterialIndex(self, new_value: int) -> None:
        self._material_logic.index = new_value
        self.materialsIndexChanged.emit()

    @Slot(str)
    def setCurrentMaterialName(self, new_value: str) -> None:
        if self._material_logic.set_name_at_current_index(new_value):
            self.materialsTableChanged.emit()

    @Slot(float)
    def setCurrentMaterialSld(self, new_value: float) -> None:
        if self._material_logic.set_sld_at_current_index(new_value):
            self.materialsTableChanged.emit()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(float)
    def setCurrentMaterialISld(self, new_value: float) -> None:
        if self._material_logic.set_isld_at_current_index(new_value):
            self.materialsTableChanged.emit()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    # Actions
    @Slot(str)
    def removeMaterial(self, value: str) -> None:
        self._material_logic.remove_at_index(value)
        self.materialsTableChanged.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def addNewMaterial(self) -> None:
        self._material_logic.add_new()
        self.materialsTableChanged.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def duplicateSelectedMaterial(self) -> None:
        self._material_logic.duplicate_selected()
        self.materialsTableChanged.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def moveSelectedMaterialUp(self) -> None:
        self._material_logic.move_selected_up()
        self.materialsTableChanged.emit()

    @Slot()
    def moveSelectedMaterialDown(self) -> None:
        self._material_logic.move_selected_down()
        self.materialsTableChanged.emit()

    # # #
    # Models
    # # #
    @Property('QVariantList', notify=modelsTableChanged)
    def models(self) -> list[dict[str, str]]:
        return self._models_logic.models

    @Property(int, notify=modelsIndexChanged)
    def currentModelIndex(self) -> int:
        return self._models_logic.index

    @Property('QVariantList', notify=modelsTableChanged)
    def modelslNames(self) -> list[str]:
        return self._models_logic.models_names

    @Property(str, notify=modelsIndexChanged)
    def currentModelName(self) -> str:
        return self._models_logic.name_at_current_index

    # Setters
    @Slot(int)
    def setCurrentModelIndex(self, new_value: int) -> None:
        self._project_lib.current_model_index = new_value
        self.modelsIndexChanged.emit()
        self.assembliesTableChanged.emit()
        self.externalRefreshPlot.emit()

    @Slot(str)
    def setCurrentModelName(self, value: str) -> None:
        if self._models_logic.set_name_at_current_index(value):
            self.modelsTableChanged.emit()

    # Actions
    @Slot(str)
    def removeModel(self, value: str) -> None:
        self._models_logic.remove_at_index(value)
        self.modelsTableChanged.emit()

    @Slot()
    def addNewModel(self) -> None:
        self._models_logic.add_new()
        self.modelsTableChanged.emit()
        self.materialsTableChanged.emit()

    @Slot()
    def duplicateSelectedModel(self) -> None:
        self._models_logic.duplicate_selected_model()
        self.modelsTableChanged.emit()

    @Slot()
    def moveSelectedModelUp(self) -> None:
        self._models_logic.move_selected_up()
        self.modelsTableChanged.emit()

    @Slot()
    def moveSelectedModelDown(self) -> None:
        self._models_logic.move_selected_down()
        self.modelsTableChanged.emit()

    # # #
    # Assemblies
    # # #
    @Property('QVariantList', notify=assembliesTableChanged)
    def assemblies(self) -> list[dict[str, str]]:
        return self._assemblies_logic.assemblies

    @Property(int, notify=assembliesIndexChanged)
    def currentAssemblyIndex(self) -> int:
        return self._assemblies_logic.index

    @Property('QVariantList', notify=assembliesTableChanged)
    def assembliesNames(self) -> list[str]:
        return self._assemblies_logic.assemblies_names

    @Property(str, notify=assembliesTableChanged)
    def currentAssemblyName(self) -> str:
        return self._assemblies_logic.name_at_current_index

    @Property(str, notify=assembliesIndexChanged)
    def currentAssemblyType(self) -> str:
        return self._assemblies_logic.type_at_current_index

    # Setters
    @Slot(int)
    def setCurrentAssemblyIndex(self, new_value: int) -> None:
        self._project_lib.current_assembly_index = new_value
        self._clearCacheAndEmitLayersChanged()
        self.assembliesTableChanged.emit()
        self.assembliesIndexChanged.emit()

    @Slot(str)
    def setCurrentAssemblyName(self, new_value: str) -> None:
        if self._assemblies_logic.set_name_at_current_index(new_value):
            self.assembliesTableChanged.emit()

    @Slot(str)
    def setCurrentAssemblyType(self, new_value: str) -> None:
        self._assemblies_logic.set_type_at_current_index(new_value)
        self._clearCacheAndEmitLayersChanged()
        self.assembliesTableChanged.emit()
        self.assembliesIndexChanged.emit()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    # Assembly specific
    @Property(str, notify=assembliesTableChanged)
    def currentAssemblyRepeatedLayerReptitions(self) -> str:
        return self._assemblies_logic.repetitions_at_current_index

    @Slot(int)
    def setCurrentAssemblyRepeatedLayerReptitions(self, new_value: int) -> None:
        if self._assemblies_logic.set_repeated_layer_reptitions(new_value):
            self.assembliesTableChanged.emit()
            self.externalRefreshPlot.emit()

    @Slot(bool)
    def setCurrentAssemblyConstrainAPM(self, new_value: bool) -> None:
        if self._assemblies_logic.set_constrain_apm(new_value):
            self.assembliesTableChanged.emit()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(bool)
    def setCurrentAssemblyConformalRoughness(self, new_value: bool) -> None:
        if self._assemblies_logic.set_conformal_roughness(new_value):
            self.assembliesTableChanged.emit()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    # Actions
    @Slot(str)
    def removeAssembly(self, value: str) -> None:
        self._assemblies_logic.remove_at_index(value)
        self.assembliesTableChanged.emit()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def addNewAssembly(self) -> None:
        self._assemblies_logic.add_new()
        self.assembliesTableChanged.emit()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def duplicateSelectedAssembly(self) -> None:
        self._assemblies_logic.duplicate_selected()
        self.assembliesTableChanged.emit()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def moveSelectedAssemblyUp(self) -> None:
        self._assemblies_logic.move_selected_up()
        self.assembliesTableChanged.emit()
        self.externalRefreshPlot.emit()

    @Slot()
    def moveSelectedAssemblyDown(self) -> None:
        self._assemblies_logic.move_selected_down()
        self.assembliesTableChanged.emit()
        self.externalRefreshPlot.emit()

    # # #
    # Layers
    # # #
    def layersConnectChanges(self) -> None:
        self._clearCacheAndEmitLayersChanged()

    @Property('QVariantList', notify=layersChange)
    def layers(self) -> list[dict[str, str]]:
        if self._chached_layers is None:
            self._chached_layers = self._layers_logic.layers
        return self._chached_layers

    @Property(int, notify=layersIndexChanged)
    def currentLayerIndex(self) -> int:
        return self._layers_logic.index

    @Property('QVariantList', notify=layersChange)
    def layersNames(self) -> list[str]:
        return self._layers_logic.layers_names

    @Property(str, notify=layersChange)
    def currentLayerName(self) -> str:
        return self._layers_logic.name_at_current_index

    # Setters
    @Slot(int)
    def setCurrentLayerIndex(self, new_value: int) -> None:
        self._project_lib.current_layer_index = new_value
        self.layersIndexChanged.emit()

    @Slot(str)
    def setCurrentLayerName(self, new_value: str) -> None:
        if self._layers_logic.set_name_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()

    @Slot(int)
    def setCurrentLayerMaterial(self, new_value: int) -> None:
        if self._layers_logic.set_material_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int)
    def setCurrentLayerSolvent(self, new_value: int) -> None:
        if self._layers_logic.set_solvent_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(float)
    def setCurrentLayerThickness(self, new_value: float) -> None:
        if self._layers_logic.set_thickness_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(float)
    def setCurrentLayerRoughness(self, new_value: float) -> None:
        if self._layers_logic.set_roughness_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(str)
    def setCurrentLayerFormula(self, new_value: str) -> None:
        if self._layers_logic.set_formula(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(float)
    def setCurrentLayerAPM(self, new_value: float) -> None:
        if self._layers_logic.set_apm_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(float)
    def setCurrentLayerSolvation(self, new_value: float) -> None:
        if self._layers_logic.set_solvation_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    # Actions
    @Slot(str)
    def removeLayer(self, value: str) -> None:
        self._layers_logic.remove_at_index(value)
        self._clearCacheAndEmitLayersChanged()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def addNewLayer(self) -> None:
        self._layers_logic.add_new()
        self._clearCacheAndEmitLayersChanged()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def duplicateSelectedLayer(self) -> None:
        self._layers_logic.duplicate_selected()
        self._clearCacheAndEmitLayersChanged()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def moveSelectedLayerUp(self) -> None:
        self._layers_logic.move_selected_up()
        self._clearCacheAndEmitLayersChanged()
        self.externalRefreshPlot.emit()

    @Slot()
    def moveSelectedLayerDown(self) -> None:
        self._layers_logic.move_selected_down()
        self._clearCacheAndEmitLayersChanged()
        self.externalRefreshPlot.emit()

    def _clearCacheAndEmitLayersChanged(self):
        self._chached_layers = None
        self.layersChange.emit()

    # # #
    # Constraints
    # # #
    @Property('QVariantList', notify=layersChange)
    def parameterNames(self) -> list[dict[str, str]]:
        return [parameter['name'] for parameter in self._parameters_logic.parameters]

    @Property('QVariantList', notify=layersChange)
    def relationOperators(self) -> list[str]:
        return self._parameters_logic.constraint_relations()

    @Property('QVariantList', notify=layersChange)
    def arithmicOperators(self) -> list[str]:
        return self._parameters_logic.constraint_arithmetic()

    @Slot(str, str, str, str, str)
    def addConstraint(self, value1: str, value2: str, value3: str, value4: str, value5: str) -> None:
        self._parameters_logic.add_constraint(
            dependent_idx=int(value1),
            relational_operator=value2,
            value=float(value3),
            arithmetic_operator=value4,
            independent_idx=int(value5),
        )
        self.externalSampleChanged.emit()

    # # #
    # Q Range
    # # #
    @Property(float, notify=qRangeChanged)
    def q_min(self) -> float:
        return self._project_logic.q_min

    @Property(float, notify=qRangeChanged)
    def q_max(self) -> float:
        return self._project_logic.q_max

    @Property(int, notify=qRangeChanged)
    def q_resolution(self) -> int:
        return self._project_logic.q_resolution

    @Property(bool, notify=qRangeChanged)
    def experimentalData(self) -> bool:
        return self._project_logic.experimental_data_at_current_index

    # Setters
    @Slot(int)
    def setModelIndex(self, value: int) -> None:
        self._models_logic.index = value

    @Slot(float)
    def setQMin(self, new_value: float) -> None:
        if self._project_logic.set_q_min(new_value):
            self.qRangeChanged.emit()
            self.externalRefreshPlot.emit()

    @Slot(float)
    def setQMax(self, new_value: float) -> None:
        if self._project_logic.set_q_max(new_value):
            self.qRangeChanged.emit()
            self.externalRefreshPlot.emit()

    @Slot(int)
    def setQElements(self, new_value: float) -> None:
        if self._project_logic.set_q_resolution(new_value):
            self.qRangeChanged.emit()
            self.externalRefreshPlot.emit()
