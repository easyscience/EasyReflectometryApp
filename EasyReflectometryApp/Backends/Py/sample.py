import logging
import math
import numbers
import re
from typing import Any
from typing import Dict
from typing import Tuple

import numpy as np
from asteval import Interpreter
from easyreflectometry import Project as ProjectLib
from easyreflectometry.inequality_constraints import InequalitySpec
from easyreflectometry.inequality_constraints import check_units
from easyreflectometry.inequality_constraints import evaluate_spec
from easyscience.variable.descriptor_number import DescriptorNumber
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import QTimer
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .logic.assemblies import Assemblies as AssembliesLogic
from .logic.calculators import Calculators as CalculatorsLogic
from .logic.layers import Layers as LayersLogic
from .logic.material import Material as MaterialLogic
from .logic.models import Models as ModelsLogic
from .logic.parameters import Parameters as ParametersLogic
from .logic.physics_constraints import PhysicsConstraints as PhysicsConstraintsLogic
from .logic.project import Project as ProjectLogic

logger = logging.getLogger(__name__)

_ASTEVAL_CONFIG = {
    'import': False,
    'importfrom': False,
    'assert': False,
    'augassign': False,
    'delete': False,
    'if': True,
    'ifexp': True,
    'for': False,
    'formattedvalue': False,
    'functiondef': False,
    'print': False,
    'raise': False,
    'listcomp': False,
    'dictcomp': False,
    'setcomp': False,
    'try': False,
    'while': False,
    'with': False,
}

_GLOBAL_SYMBOLS: Dict[str, Any] = {
    'np': np,
    'numpy': np,
    'math': math,
    'pi': math.pi,
    'e': math.e,
}


class Sample(QObject):
    materialsTableChanged = Signal()
    materialsIndexChanged = Signal()

    modelsTableChanged = Signal()
    modelsIndexChanged = Signal()

    assembliesTableChanged = Signal()
    assembliesIndexChanged = Signal()

    layersChange = Signal()
    layersIndexChanged = Signal()

    # Per-layer magnetism (rho_m / theta_m) and calculator capability.
    magnetismChanged = Signal()
    magnetismFailed = Signal(str)
    # Emitted with (layer index, engine name) when making a layer magnetic needs
    # a different calculation engine; the UI asks before anything is changed.
    magnetismNeedsEngine = Signal(int, str)
    # Emitted when the Sample page changed the project's calculation engine, so
    # the Analysis page's selector and the plots follow.
    calculationEngineChanged = Signal()
    # Emitted with the reason when a requested engine switch is refused (e.g.
    # the sample has magnetic layers the engine cannot model). Logs are not
    # visible in the GUI, so the engine selector shows this in a dialog.
    calculationEngineRejected = Signal(str)

    qRangeChanged = Signal()
    constraintsChanged = Signal()

    externalRefreshPlot = Signal()
    externalSampleChanged = Signal()

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._project_lib = project_lib
        self._material_logic = MaterialLogic(project_lib)
        self._models_logic = ModelsLogic(project_lib)
        # The engine is a project-wide setting; this logic derives its index
        # from the project, so the Analysis page's selector cannot disagree.
        self._calculators_logic = CalculatorsLogic(project_lib)
        self._assemblies_logic = AssembliesLogic(project_lib)
        self._layers_logic = LayersLogic(project_lib)
        self._project_logic = ProjectLogic(project_lib)
        self._parameters_logic = ParametersLogic(project_lib)

        self._chached_layers = None
        self._constraint_states: Dict[str, dict[str, Any]] = {}
        # Child of self (not QTimer.singleShot) so a pending notification can
        # never outlive this backend or keep it - and the project - alive.
        self._constraints_notify_timer = QTimer(self)
        self._constraints_notify_timer.setSingleShot(True)
        self._constraints_notify_timer.setInterval(0)
        self._constraints_notify_timer.timeout.connect(self.constraintsChanged)
        self._physics_constraints_logic = PhysicsConstraintsLogic(project_lib)

        self.connect_logic()

    def connect_logic(self) -> None:
        self.assembliesIndexChanged.connect(self.layersConnectChanges)
        # Inequality rows carry a "satisfied" flag evaluated at the current
        # values, so parameter edits must refresh the constraints list too.
        # `constraintsList` is expensive (asteval of every expression, recipe
        # ownership across all assemblies), so bursts of layersChange within one
        # event-loop turn are coalesced into a single constraintsChanged.
        self.layersChange.connect(self._scheduleConstraintsChanged)
        # The magnetism table lists the current assembly's layers.
        self.assembliesIndexChanged.connect(self.magnetismChanged)

    def _scheduleConstraintsChanged(self) -> None:
        self._constraints_notify_timer.start()

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

    @Slot(int, str)
    def setMaterialNameAtIndex(self, index: int, new_value: str) -> None:
        if self._material_logic.set_name_at_index(index, new_value):
            self.materialsTableChanged.emit()

    @Slot(float)
    def setCurrentMaterialSld(self, new_value: float) -> None:
        if self._material_logic.set_sld_at_current_index(new_value):
            self.materialsTableChanged.emit()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int, float)
    def setMaterialSldAtIndex(self, index: int, new_value: float) -> None:
        if self._material_logic.set_sld_at_index(index, new_value):
            self.materialsTableChanged.emit()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(float)
    def setCurrentMaterialISld(self, new_value: float) -> None:
        if self._material_logic.set_isld_at_current_index(new_value):
            self.materialsTableChanged.emit()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int, float)
    def setMaterialISldAtIndex(self, index: int, new_value: float) -> None:
        if self._material_logic.set_isld_at_index(index, new_value):
            self.materialsTableChanged.emit()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    # Actions
    @Slot(str)
    def removeMaterial(self, value: str) -> None:
        self._material_logic.remove_at_index(value)
        self.materialsTableChanged.emit()
        self.externalRefreshPlot.emit()
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
    def modelsNames(self) -> list[str]:
        return self._models_logic.models_names

    @Property(str, notify=modelsIndexChanged)
    def currentModelName(self) -> str:
        return self._models_logic.name_at_current_index

    # Setters
    @Slot(int)
    def setCurrentModelIndex(self, new_value: int) -> None:
        if self._project_lib.current_model_index != new_value:
            self._project_lib.current_model_index = new_value
            self.modelsIndexChanged.emit()
            self.assembliesTableChanged.emit()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(str)
    def setCurrentModelName(self, value: str) -> None:
        if self._models_logic.set_name_at_current_index(value):
            self.modelsTableChanged.emit()
            self.modelsIndexChanged.emit()
            self._clearCacheAndEmitLayersChanged()

    @Slot(int, str)
    def setModelNameAtIndex(self, index: int, value: str) -> None:
        if self._models_logic.set_name_at_index(index, value):
            self.modelsTableChanged.emit()
            self.modelsIndexChanged.emit()
            self._clearCacheAndEmitLayersChanged()

    # Actions
    @Slot(str)
    def removeModel(self, value: str) -> None:
        self._models_logic.remove_at_index(value)
        self.modelsTableChanged.emit()

    @Slot()
    def addNewModel(self) -> None:
        self._models_logic.add_new()
        self._project_logic._update_enablement_of_fixed_layers_for_model(self._models_logic.index)
        self.modelsTableChanged.emit()
        self.materialsTableChanged.emit()

    @Slot()
    def duplicateSelectedModel(self) -> None:
        self._models_logic.duplicate_selected_model()
        self._project_logic._update_enablement_of_fixed_layers_for_model(self._models_logic.index)
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

    def _refreshCurrentAssemblySelectionState(self) -> None:
        sample = self._project_lib._models[self._project_lib.current_model_index].sample
        assembly_count = len(sample)

        if assembly_count == 0:
            self._project_lib.current_assembly_index = 0
            self._project_lib.current_layer_index = 0
        else:
            self._project_lib.current_assembly_index = max(
                0,
                min(self._project_lib.current_assembly_index, assembly_count - 1),
            )
            layer_count = len(sample[self._project_lib.current_assembly_index].layers)
            self._project_lib.current_layer_index = max(
                0,
                min(self._project_lib.current_layer_index, max(layer_count - 1, 0)),
            )

        self._clearCacheAndEmitLayersChanged()
        self.assembliesIndexChanged.emit()
        self.layersIndexChanged.emit()

    # Setters
    @Slot(int)
    def setCurrentAssemblyIndex(self, new_value: int) -> None:
        self._project_lib.current_assembly_index = new_value
        self._refreshCurrentAssemblySelectionState()
        self.assembliesTableChanged.emit()

    @Slot(str)
    def setCurrentAssemblyName(self, new_value: str) -> None:
        if self._assemblies_logic.set_name_at_current_index(new_value):
            self.assembliesTableChanged.emit()
            self.materialsTableChanged.emit()
            self.externalSampleChanged.emit()

    @Slot(int, str)
    def setAssemblyNameAtIndex(self, index: int, new_value: str) -> None:
        if self._assemblies_logic.set_name_at_index(index, new_value):
            self.assembliesTableChanged.emit()
            self.materialsTableChanged.emit()
            self.externalSampleChanged.emit()

    @Slot(str)
    def setCurrentAssemblyType(self, new_value: str) -> None:
        if self._assemblies_logic.set_type_at_current_index(new_value):
            self._refreshCurrentAssemblySelectionState()
            self.assembliesTableChanged.emit()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int, str)
    def setAssemblyTypeAtIndex(self, index: int, new_value: str) -> None:
        if self._assemblies_logic.set_type_at_index(index, new_value):
            self._refreshCurrentAssemblySelectionState()
            self.assembliesTableChanged.emit()
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
        self._refreshCurrentAssemblySelectionState()
        self._project_logic._update_enablement_of_fixed_layers_for_model(self._models_logic.index)
        self.assembliesTableChanged.emit()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def addNewAssembly(self) -> None:
        self._assemblies_logic.add_new()
        self._refreshCurrentAssemblySelectionState()
        self._project_logic._update_enablement_of_fixed_layers_for_model(self._models_logic.index)
        self.assembliesTableChanged.emit()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def duplicateSelectedAssembly(self) -> None:
        self._assemblies_logic.duplicate_selected()
        self._refreshCurrentAssemblySelectionState()
        self._project_logic._update_enablement_of_fixed_layers_for_model(self._models_logic.index)
        self.assembliesTableChanged.emit()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def moveSelectedAssemblyUp(self) -> None:
        self._assemblies_logic.move_selected_up()
        self._refreshCurrentAssemblySelectionState()
        self._project_logic._update_enablement_of_fixed_layers_for_model(self._models_logic.index)
        self.assembliesTableChanged.emit()
        self.externalRefreshPlot.emit()

    @Slot()
    def moveSelectedAssemblyDown(self) -> None:
        self._assemblies_logic.move_selected_down()
        self._refreshCurrentAssemblySelectionState()
        self._project_logic._update_enablement_of_fixed_layers_for_model(self._models_logic.index)
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

    @Slot(int, str)
    def setLayerNameAtIndex(self, index: int, new_value: str) -> None:
        if self._layers_logic.set_name_at_index(index, new_value):
            self._clearCacheAndEmitLayersChanged()

    @Slot(int)
    def setCurrentLayerMaterial(self, new_value: int) -> None:
        if self._layers_logic.set_material_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int, int)
    def setLayerMaterialAtIndex(self, index: int, new_value: int) -> None:
        if self._layers_logic.set_material_at_index(index, new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int)
    def setCurrentLayerSolvent(self, new_value: int) -> None:
        if self._layers_logic.set_solvent_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int, int)
    def setLayerSolventAtIndex(self, index: int, new_value: int) -> None:
        if self._layers_logic.set_solvent_at_index(index, new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(float)
    def setCurrentLayerThickness(self, new_value: float) -> None:
        if self._layers_logic.set_thickness_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int, float)
    def setLayerThicknessAtIndex(self, index: int, new_value: float) -> None:
        if self._layers_logic.set_thickness_at_index(index, new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(float)
    def setCurrentLayerRoughness(self, new_value: float) -> None:
        if self._layers_logic.set_roughness_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int, float)
    def setLayerRoughnessAtIndex(self, index: int, new_value: float) -> None:
        if self._layers_logic.set_roughness_at_index(index, new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(str)
    def setCurrentLayerFormula(self, new_value: str) -> None:
        if self._layers_logic.set_formula(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int, str)
    def setLayerFormulaAtIndex(self, index: int, new_value: str) -> None:
        if self._layers_logic.set_formula_at_index(index, new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(float)
    def setCurrentLayerAPM(self, new_value: float) -> None:
        if self._layers_logic.set_apm_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int, float)
    def setLayerAPMAtIndex(self, index: int, new_value: float) -> None:
        if self._layers_logic.set_apm_at_index(index, new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(float)
    def setCurrentLayerSolvation(self, new_value: float) -> None:
        if self._layers_logic.set_solvation_at_current_index(new_value):
            self._clearCacheAndEmitLayersChanged()
            self.externalRefreshPlot.emit()
            self.externalSampleChanged.emit()

    @Slot(int, float)
    def setLayerSolvationAtIndex(self, index: int, new_value: float) -> None:
        if self._layers_logic.set_solvation_at_index(index, new_value):
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
        # The magnetism table lists the same layers, so it goes stale whenever
        # a layer is added, removed, reordered or renamed.
        self.magnetismChanged.emit()

    # # #
    # Calculation engine (shared project setting, shown here because magnetism
    # depends on it)
    # # #
    @Property('QVariantList', notify=calculationEngineChanged)
    def calculationEngines(self) -> list[str]:
        """Available calculation engines."""
        return self._calculators_logic.available()

    @Property(int, notify=calculationEngineChanged)
    def calculationEngineIndex(self) -> int:
        """The project's active calculation engine."""
        return self._calculators_logic.current_index()

    @Property('QVariantList', notify=calculationEngineChanged)
    def calculationEnginesSupportingMagnetism(self) -> list[str]:
        """Engines that can model magnetic layers."""
        return self._calculators_logic.supporting_magnetism()

    @Slot(int)
    def setCalculationEngineIndex(self, new_value: int) -> None:
        """Switch the project's calculation engine from the Sample page."""
        try:
            changed = self._calculators_logic.set_current_index(new_value)
        except NotImplementedError as exception:
            logger.warning('Cannot change the calculation engine: %s', exception)
            self.calculationEngineRejected.emit(str(exception))
            self.calculationEngineChanged.emit()
            return
        if changed:
            self.calculationEngineChanged.emit()
            self.magnetismChanged.emit()

    # # #
    # Layer magnetism
    # # #
    @Property(bool, notify=magnetismChanged)
    def magnetismSupported(self) -> bool:
        """Whether the active calculator can model magnetic layers (refl1d only)."""
        return self._layers_logic.magnetism_supported

    @Property('QVariantList', notify=magnetismChanged)
    def layersMagnetism(self) -> list[dict[str, str]]:
        """Per-layer magnetism of the current assembly, one row per layer."""
        return self._layers_logic.magnetism

    @Slot(int, bool)
    def setLayerMagneticAtIndex(self, index: int, new_value: bool) -> None:
        """Attach or remove magnetism on one layer.

        Magnetism is only modelled by some calculation engines. Rather than
        refusing and pointing at another page, ask the UI to confirm the switch
        (`magnetismNeedsEngine`); nothing is changed until it comes back through
        `enableMagnetismWithEngineAtIndex`. A calculator that cannot model
        magnetism still reports the reason instead of raising out of a
        QML-invoked slot (which would abort the process).
        """
        if new_value and not self._layers_logic.magnetism_supported:
            engines = self._calculators_logic.supporting_magnetism()
            if engines:
                self.magnetismNeedsEngine.emit(index, engines[0])
                return
        try:
            changed = self._layers_logic.set_magnetic_at_index(index, new_value)
        except NotImplementedError as exception:
            logger.warning('Cannot change layer magnetism: %s', exception)
            self.magnetismFailed.emit(str(exception))
            return
        if changed:
            self._emitMagnetismChanged()

    @Slot(int, str)
    def enableMagnetismWithEngineAtIndex(self, index: int, engine: str) -> None:
        """Switch the calculation engine, then make the layer magnetic.

        The confirmed half of `magnetismNeedsEngine`: the user has been told
        that the engine changes, so both steps happen as one action. If
        attaching magnetism fails after the engine switch, the switch is
        rolled back rather than left half-applied (engine changed, layer
        still non-magnetic, with no indication to the user).
        """
        engine_index = self._calculators_logic.index_of(engine)
        if engine_index < 0:
            self.magnetismFailed.emit(f'The {engine} calculation engine is not available.')
            return
        previous_calculator = self._project_lib.calculator
        engine_switched = False
        try:
            engine_switched = self._calculators_logic.set_current_index(engine_index)
            changed = self._layers_logic.set_magnetic_at_index(index, True)
        except NotImplementedError as exception:
            if engine_switched:
                self._project_lib.calculator = previous_calculator
            logger.warning('Cannot enable magnetism: %s', exception)
            self.magnetismFailed.emit(str(exception))
            return
        if engine_switched:
            self.calculationEngineChanged.emit()
        if changed:
            self._emitMagnetismChanged()

    @Slot(int, float)
    def setLayerRhoMAtIndex(self, index: int, new_value: float) -> None:
        if self._layers_logic.set_rho_m_at_index(index, new_value):
            self._emitMagnetismChanged()

    @Slot(int, float)
    def setLayerThetaMAtIndex(self, index: int, new_value: float) -> None:
        if self._layers_logic.set_theta_m_at_index(index, new_value):
            self._emitMagnetismChanged()

    def _emitMagnetismChanged(self) -> None:
        """Magnetism edits change the model, its parameters and every curve."""
        self._clearCacheAndEmitLayersChanged()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    # # #
    # Constraints
    # # #
    def _build_constraint_context(self) -> Tuple[list[dict[str, Any]], Dict[str, DescriptorNumber], Dict[str, str]]:
        context = self._parameters_logic.constraint_context()
        alias_lookup: Dict[str, DescriptorNumber] = {}
        display_lookup: Dict[str, str] = {}
        for entry in context:
            alias = entry['alias']
            if alias:  # Only add non-empty aliases
                alias_lookup[alias] = entry['object']
                display_lookup[alias] = entry['display_name']
        return context, alias_lookup, display_lookup

    def _extract_dependency_map(
        self,
        expression: str,
        alias_lookup: Dict[str, DescriptorNumber],
    ) -> Dict[str, DescriptorNumber]:
        used_aliases: Dict[str, DescriptorNumber] = {}
        for alias, parameter in alias_lookup.items():
            if not alias:
                continue
            pattern = rf'\b{re.escape(alias)}\b'
            if re.search(pattern, expression):
                used_aliases[alias] = parameter
        return used_aliases

    @staticmethod
    def _make_interpreter(aliases: Dict[str, DescriptorNumber], numeric: bool = False) -> Interpreter:
        """A sandboxed interpreter with the globals and parameter aliases in scope.

        With `numeric`, aliases resolve to plain float values instead of the
        unit-carrying parameter objects.
        """
        interpreter = Interpreter(config=_ASTEVAL_CONFIG)
        for name, value in _GLOBAL_SYMBOLS.items():
            interpreter.symtable[name] = value
            if isinstance(value, numbers.Number):
                interpreter.readonly_symbols.add(name)
        for alias, dependency in aliases.items():
            interpreter.symtable[alias] = float(dependency.value) if numeric else dependency
            interpreter.readonly_symbols.add(alias)
        return interpreter

    def _evaluate_constraint_expression(
        self,
        expression: str,
        dependency_map: Dict[str, DescriptorNumber],
        all_aliases: Dict[str, DescriptorNumber] | None = None,
    ) -> DescriptorNumber | numbers.Number:
        """Evaluate constraint expression with all available parameter aliases in scope."""
        # Add ALL parameter aliases to the symbol table (not just dependencies)
        # This allows validation to work even if we haven't detected the parameter yet
        aliases_to_add = all_aliases if all_aliases is not None else dependency_map
        interpreter = self._make_interpreter(aliases_to_add)

        try:
            result = interpreter.eval(expression, raise_errors=True)
        except Exception as e:
            # Provide helpful error message showing available aliases
            if 'not defined' in str(e):
                available = ', '.join(sorted(aliases_to_add.keys())[:10])  # Show first 10
                raise NameError(f'{str(e)}\nAvailable aliases: {available}...') from None
            raise
        return result

    def _evaluate_constraint_expression_numeric(
        self,
        expression: str,
        all_aliases: Dict[str, DescriptorNumber],
    ) -> numbers.Number:
        """Evaluate a constraint expression over plain parameter *values*.

        Fallback for inequality expressions mixing literals with parameters
        ('90 - t_b'), which the unit-carrying evaluation cannot represent.
        """
        interpreter = self._make_interpreter(all_aliases, numeric=True)
        result = interpreter.eval(expression, raise_errors=True)
        if not isinstance(result, numbers.Number):
            raise TypeError('Expression must evaluate to a numeric value.')
        return result

    @staticmethod
    def _to_float(value: DescriptorNumber | numbers.Number) -> float:
        if isinstance(value, DescriptorNumber):
            return float(value.value)
        if isinstance(value, numbers.Number):
            return float(value)
        raise TypeError('Expression must evaluate to a numeric value.')

    @staticmethod
    def _pretty_expression(expression: str, alias_display: Dict[str, str]) -> str:
        pretty_expression = expression
        for alias in sorted(alias_display.keys(), key=len, reverse=True):
            replacement = alias_display[alias]
            if not replacement:
                continue
            pattern = rf'\b{re.escape(alias)}\b'
            pretty_expression = re.sub(pattern, replacement, pretty_expression)
        return pretty_expression

    @staticmethod
    def _sanitize_relation(operator: str) -> str:
        mapping = {
            '=': '=',
            '==': '=',
            '≡': '=',
            '>': '>',
            '≥': '>',
            '&gt': '>',
            '<': '<',
            '≤': '<',
            '&lt': '<',
        }
        return mapping.get(operator, '=')

    @staticmethod
    def _format_numeric(value: float) -> str:
        return f'{value:.6g}'

    def _get_independent_parameter_entries(self) -> list[dict]:
        """Return the filtered list of independent+enabled parameter entries.

        This must match the same filtering as dependentParameterNames so that
        the QML dropdown index maps to the correct parameter object.
        """
        entries = []
        for parameter in self._parameters_logic.parameters:
            if not parameter['independent']:
                continue
            if hasattr(parameter['object'], 'enabled') and not parameter['object'].enabled:
                continue
            entries.append(parameter)
        return entries

    def _prepare_constraint_instruction(
        self,
        dependent_index: int,
        relation_operator: str,
        expression: str,
    ) -> dict[str, Any]:
        independent_entries = self._get_independent_parameter_entries()
        if dependent_index < 0 or dependent_index >= len(independent_entries):
            raise ValueError('Select a dependent parameter before defining a constraint.')

        relation = self._sanitize_relation(relation_operator)
        expression_text = expression.strip()
        if not expression_text:
            raise ValueError('Expression cannot be empty.')

        context, alias_lookup, display_lookup = self._build_constraint_context()
        dependency_map = self._extract_dependency_map(expression_text, alias_lookup)

        try:
            # Pass all available aliases so validation can check any parameter reference
            evaluation_result = self._evaluate_constraint_expression(expression_text, dependency_map, all_aliases=alias_lookup)
        except NameError as error:
            raise NameError(str(error).split('\n')[-1]) from None
        except SyntaxError as error:
            raise SyntaxError(str(error).split('\n')[-1]) from None
        except Exception as error:
            # Inequality expressions may mix numeric literals with parameters
            # ('90 - t_b'), which the unit-carrying arithmetic rejects. They are
            # evaluated numerically during the fit anyway (literals read in the
            # unit of the dependent parameter), so always retry any inequality
            # that references parameters with plain values — the numeric path is
            # strictly more permissive and `check_units` still verifies the
            # resulting spec. Equality constraints go through
            # `make_dependent_on`, which needs the unit-carrying form — no
            # fallback there.
            if relation == '=' or not dependency_map:
                raise RuntimeError(str(error)) from None
            try:
                evaluation_result = self._evaluate_constraint_expression_numeric(
                    expression_text, all_aliases=alias_lookup
                )
            except Exception:
                # Report the original, unit-aware error: it names the actual
                # conflict instead of the fallback's symptom.
                raise RuntimeError(str(error)) from None

        pretty_expression = self._pretty_expression(expression_text, display_lookup)

        if relation == '=':
            if dependency_map:
                if not isinstance(evaluation_result, DescriptorNumber):
                    raise TypeError('Expressions referencing parameters must evaluate to a parameter quantity.')
                return {
                    'mode': 'dynamic',
                    'expression': expression_text,
                    'dependency_map': dependency_map,
                    'pretty_expression': pretty_expression,
                    'relation': relation,
                }
            numeric_value = self._to_float(evaluation_result)
            return {
                'mode': 'static',
                'value': numeric_value,
                'pretty_expression': self._format_numeric(numeric_value),
                'relation': relation,
            }

        if dependency_map:
            # Cross-parameter inequality: a fit penalty (BUMPS engines only),
            # not a bound on the parameter itself.
            return self._prepare_inequality_instruction(
                dependent_entry=independent_entries[dependent_index],
                relation=relation,
                expression_text=expression_text,
                dependency_map=dependency_map,
                pretty_expression=pretty_expression,
            )

        numeric_value = self._to_float(evaluation_result)
        mode = 'lower_bound' if relation == '>' else 'upper_bound'
        return {
            'mode': mode,
            'value': numeric_value,
            'pretty_expression': self._format_numeric(numeric_value),
            'relation': relation,
        }

    # The GUI's '>' / '<' relations read as ≥ / ≤.
    _INEQUALITY_OPS = {'>': '>=', '<': '<='}

    def _prepare_inequality_instruction(
        self,
        dependent_entry: dict[str, Any],
        relation: str,
        expression_text: str,
        dependency_map: Dict[str, DescriptorNumber],
        pretty_expression: str,
    ) -> dict[str, Any]:
        dependent = dependent_entry['object']
        lhs_alias = dependent_entry.get('alias') or 'lhs'
        if dependent in dependency_map.values():
            raise ValueError('The expression cannot reference the constrained parameter itself.')
        lhs_path = self._project_lib.parameter_path(dependent)
        if lhs_path is None:
            raise ValueError('The dependent parameter cannot be addressed in the project.')
        rhs_paths: Dict[str, str] = {}
        for alias, parameter in dependency_map.items():
            path = self._project_lib.parameter_path(parameter)
            if path is None:
                raise ValueError(f"Parameter '{alias}' cannot be addressed in the project.")
            rhs_paths[alias] = path
        spec = InequalitySpec(
            lhs_expression=lhs_alias,
            op=self._INEQUALITY_OPS[relation],
            rhs_expression=expression_text,
            lhs_paths={lhs_alias: lhs_path},
            rhs_paths=rhs_paths,
            name=f"{dependent_entry.get('display_name', lhs_alias)} {self._INEQUALITY_OPS[relation]} {pretty_expression}",
        )
        check_units(spec, self._project_lib.resolve_parameter_path)
        evaluation = evaluate_spec(spec, self._project_lib.resolve_parameter_path)
        return {
            'mode': 'inequality',
            'expression': expression_text,
            'dependency_map': dependency_map,
            'pretty_expression': pretty_expression,
            'relation': relation,
            'spec': spec,
            'satisfied': evaluation.satisfied,
            'warning': (
                ''
                if evaluation.satisfied
                else (
                    f'Current values violate this constraint ({self._format_numeric(evaluation.lhs)} vs '
                    f'{self._format_numeric(evaluation.rhs)}); fits will not start until they do. '
                    'Inequality constraints are enforced by the BUMPS minimizers only.'
                )
            ),
        }

    def _inequality_constraint_rows(self, display_lookup: Dict[str, str]) -> list[dict[str, Any]]:
        """Rows of `constraintsList` describing the project's inequality constraints."""
        rows: list[dict[str, Any]] = []
        context = self._parameters_logic.constraint_context()
        display_by_object = {id(entry['object']): entry['display_name'] for entry in context}
        relation_text = {'<=': '≤', '<': '<', '>=': '≥', '>': '>'}
        for index, spec in enumerate(self._project_lib.inequality_constraints):
            alias_display: Dict[str, str] = {}
            for alias, path in spec.paths.items():
                try:
                    parameter = self._project_lib.resolve_parameter_path(path)
                    alias_display[alias] = display_by_object.get(id(parameter), display_lookup.get(alias, alias))
                except KeyError:
                    # The parameter behind this alias no longer exists (e.g. its
                    # layer was removed); keep the alias so the user can tell
                    # which term broke, but label it clearly.
                    alias_display[alias] = f'{alias} (missing)'
            lhs_display = self._pretty_expression(spec.lhs_expression, alias_display)
            rhs_display = self._pretty_expression(spec.rhs_expression, alias_display)
            try:
                satisfied = evaluate_spec(spec, self._project_lib.resolve_parameter_path).satisfied
            except Exception:  # noqa: BLE001 - unresolved path: shown, flagged, never crashes the list
                satisfied = False
            rows.append(
                {
                    'dependentName': lhs_display,
                    'uniqueName': f'inequality:{index}',
                    'inequalityIndex': index,
                    'expression': rhs_display,
                    'rawExpression': str(spec),
                    'relation': relation_text.get(spec.op, spec.op),
                    'type': 'inequality',
                    'enabled': bool(spec.enabled),
                    'satisfied': bool(satisfied),
                }
            )
        return rows

    @staticmethod
    def _ensure_parameter_independent(parameter: DescriptorNumber) -> None:
        try:
            parameter.make_independent()
        except AttributeError:
            parameter._independent = True

    def _infer_constraint_state(
        self,
        parameter_obj: DescriptorNumber,
        display_lookup: Dict[str, str],
    ) -> dict[str, Any] | None:
        if getattr(parameter_obj, 'independent', True):
            return None

        try:
            raw_expression = parameter_obj.dependency_expression
        except AttributeError:
            value = float(parameter_obj.value)
            formatted = self._format_numeric(value)
            return {
                'mode': 'static',
                'relation': '=',
                'expression': formatted,
                'raw_expression': formatted,
                'pretty_expression': formatted,
                'value': value,
            }

        dependency_map = getattr(parameter_obj, 'dependency_map', {}) or {}
        alias_display_subset = {alias: display_lookup.get(alias, alias) for alias in dependency_map.keys()}
        pretty_expression = self._pretty_expression(raw_expression, alias_display_subset)
        return {
            'mode': 'dynamic',
            'relation': '=',
            'expression': raw_expression,
            'raw_expression': raw_expression,
            'pretty_expression': pretty_expression,
            'dependency_map': dependency_map,
        }

    def _resolve_constraint_state(
        self,
        parameter_obj: DescriptorNumber,
        display_lookup: Dict[str, str],
    ) -> dict[str, Any] | None:
        unique_name = getattr(parameter_obj, 'unique_name', None)
        if unique_name is not None:
            stored = self._constraint_states.get(unique_name)
            if stored is not None:
                return stored
        return self._infer_constraint_state(parameter_obj, display_lookup)

    @staticmethod
    def _capture_parameter_state(parameter: DescriptorNumber) -> dict[str, Any]:
        state: dict[str, Any] = {
            'value': float(parameter.value),
            'free': bool(parameter.free),
            'independent': getattr(parameter, 'independent', True),
            '_independent': getattr(parameter, '_independent', True),
        }
        if hasattr(parameter, 'min'):
            try:
                state['min'] = float(parameter.min)
            except Exception:  # noqa: BLE001
                state['min'] = parameter.min
        if hasattr(parameter, 'max'):
            try:
                state['max'] = float(parameter.max)
            except Exception:  # noqa: BLE001
                state['max'] = parameter.max
        return state

    @staticmethod
    def _restore_parameter_state(parameter: DescriptorNumber, state: dict[str, Any]) -> None:
        try:
            parameter.make_independent()
        except AttributeError:
            parameter._independent = True

        if 'value' in state and state['value'] is not None:
            parameter.value = state['value']
        if 'min' in state and state['min'] is not None:
            parameter.min = state['min']
        if 'max' in state and state['max'] is not None:
            parameter.max = state['max']
        if 'free' in state and state['free'] is not None:
            parameter.free = state['free']
        if '_independent' in state and state['_independent'] is not None:
            parameter._independent = state['_independent']

    @Property('QVariantList', notify=layersChange)
    def parameterNames(self) -> list[dict[str, str]]:
        return [parameter['name'] for parameter in self._parameters_logic.parameters]

    @Property('QVariantList', notify=layersChange)
    def enabledParameterNames(self) -> list[str]:
        enabled_param_names = []
        for parameter in self._parameters_logic.parameters:
            if hasattr(parameter['object'], 'enabled') and not parameter['object'].enabled:
                continue
            enabled_param_names.append(parameter['name'])
        return enabled_param_names

    @Property('QVariantList', notify=layersChange)
    def dependentParameterNames(self) -> list[str]:
        dep_param_names = []
        for parameter in self._parameters_logic.parameters:
            if not parameter['independent']:
                continue
            if hasattr(parameter['object'], 'enabled') and not parameter['object'].enabled:
                continue
            dep_param_names.append(parameter['name'])
        return dep_param_names

    @Property('QVariantList', notify=layersChange)
    def constraintParametersMetadata(self) -> list[dict[str, Any]]:
        return self._parameters_logic.constraint_metadata()

    @Property('QVariantList', notify=layersChange)
    def relationOperators(self) -> list[dict[str, str]]:
        return self._parameters_logic.constraint_relations()

    @Property('QVariantList', notify=layersChange)
    def arithmicOperators(self) -> list[str]:
        return self._parameters_logic.constraint_arithmetic()

    @Property('QVariantList', notify=constraintsChanged)
    def constraintsList(self) -> list[dict[str, str]]:
        """Get the list of active constraints with display metadata."""
        constraints: list[dict[str, str]] = []
        context, _, display_lookup = self._build_constraint_context()
        owned = self._physics_constraints_logic.owned_parameters()
        recipe_rows: dict[tuple, dict[str, Any]] = {}

        for entry in context:
            parameter_obj = entry['object']
            if entry.get('kind') == 'derived':
                # Model-owned calculations (total thickness) are not user constraints.
                continue
            group = owned.get(getattr(parameter_obj, 'unique_name', None))
            if group is not None:
                # One row per active physics recipe instead of N cryptic ties.
                key = (group['recipeId'], group['assemblyIndex'])
                if key not in recipe_rows:
                    recipe_rows[key] = {
                        'dependentName': group['assemblyName'],
                        'uniqueName': f"recipe:{group['recipeId']}:{group['assemblyIndex']}",
                        'recipeId': group['recipeId'],
                        'assemblyIndex': group['assemblyIndex'],
                        'expression': group['title'],
                        'rawExpression': f"{group['title']} ({group['count']} tied parameter(s))",
                        'relation': '',
                        'type': 'recipe',
                        'enabled': True,
                        # Recipe ties are identities and hold by construction;
                        # this is not a feasibility check like the inequality
                        # rows' flag — do not repurpose it as one.
                        'satisfied': True,
                        'count': group['count'],
                        'members': [],
                    }
                recipe_rows[key]['members'].append(entry['display_name'])
                continue
            state = self._resolve_constraint_state(parameter_obj, display_lookup)
            if state is None:
                continue

            relation = state.get('relation', '=')
            mode = state.get('mode', 'static')

            if mode == 'dynamic':
                expression_display = state.get('pretty_expression', state.get('expression', ''))
                raw_expression = state.get('expression', expression_display)
            else:
                value = state.get('value', float(parameter_obj.value))
                expression_display = state.get('pretty_expression', self._format_numeric(float(value)))
                raw_expression = state.get('raw_expression', expression_display)

            # Use model-prefixed display name if available (from constrainModelsParameters)
            dependent_display = state.get('dependent_display', entry['display_name'])

            constraints.append(
                {
                    'dependentName': dependent_display,
                    # Carry the unique_name so removal keys off identity, not the
                    # (possibly duplicated) display name (issue #328).
                    'uniqueName': getattr(parameter_obj, 'unique_name', '') or '',
                    'expression': expression_display,
                    'rawExpression': raw_expression,
                    'relation': relation,
                    'type': mode,
                    'enabled': True,
                    'satisfied': True,
                }
            )

        constraints.extend(recipe_rows.values())
        constraints.extend(self._inequality_constraint_rows(display_lookup))
        return constraints

    # ----- physics-constraint recipes -----

    @Property('QVariantList', notify=constraintsChanged)
    def physicsConstraintRecipes(self) -> list[dict[str, Any]]:
        """Declarative recipe list (per assembly of the current model) for the GUI."""
        try:
            return self._physics_constraints_logic.recipes()
        except Exception:  # noqa: BLE001
            logger.exception('Failed to build the physics-constraint recipes')
            return []

    @Slot(int, str, result='QVariant')
    def applyPhysicsConstraint(self, assembly_index: int, recipe_id: str):
        try:
            changed = self._physics_constraints_logic.apply(int(assembly_index), recipe_id)
        except Exception as error:  # noqa: BLE001
            return {'success': False, 'message': str(error)}
        if changed:
            self._emit_constraints_changed()
        return {'success': True, 'message': ''}

    @Slot(int, str, result='QVariant')
    def removePhysicsConstraint(self, assembly_index: int, recipe_id: str):
        try:
            changed = self._physics_constraints_logic.remove(int(assembly_index), recipe_id)
        except Exception as error:  # noqa: BLE001
            return {'success': False, 'message': str(error)}
        if changed:
            self._emit_constraints_changed()
        return {'success': True, 'message': ''}

    def _emit_constraints_changed(self) -> None:
        """Constraints move parameter values, so the curves and tables change too.

        `layersChange` already forwards (coalesced) to `constraintsChanged`, so
        it is not emitted here as well — that would evaluate the expensive
        constraints list twice per change.
        """
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()
        self.layersChange.emit()

    @Property(int, notify=constraintsChanged)
    def inequalityConstraintsCount(self) -> int:
        return len([spec for spec in self._project_lib.inequality_constraints if spec.enabled])

    @Property('QVariantList', notify=constraintsChanged)
    def violatedInequalityConstraints(self) -> list[str]:
        """Names of enabled inequality constraints the current values violate."""
        try:
            return [spec.name or str(spec) for spec in self._project_lib.violated_inequality_constraints()]
        except Exception:  # noqa: BLE001
            return []

    @Slot(int, bool)
    def setInequalityConstraintEnabled(self, index: int, enabled: bool) -> None:
        specs = self._project_lib.inequality_constraints
        if 0 <= index < len(specs):
            specs[index].enabled = bool(enabled)
            self.constraintsChanged.emit()

    @Slot(int)
    def removeConstraintByIndex(self, index: int) -> None:
        """Remove constraint by index by making the parameter independent."""
        if not isinstance(index, int):
            try:
                index = int(index)
            except (TypeError, ValueError):
                return

        constraints_list = self.constraintsList
        if index >= len(constraints_list):
            return

        row = constraints_list[index]
        if row.get('type') == 'inequality':
            self._project_lib.remove_inequality_constraint(int(row['inequalityIndex']))
            self.constraintsChanged.emit()
            return
        if row.get('type') == 'recipe':
            result = self.removePhysicsConstraint(int(row['assemblyIndex']), str(row['recipeId']))
            if isinstance(result, dict) and not result.get('success', True):
                logger.warning(
                    'Removing physics constraint %s failed: %s', row.get('recipeId'), result.get('message', '')
                )
            return

        # Resolve by unique_name (parameter identity), not display name, so two
        # parameters sharing a display name don't collide (issue #328).
        unique_name = constraints_list[index].get('uniqueName')
        if not unique_name:
            return
        param_obj = self._find_parameter_object_by_unique_name(unique_name)

        if param_obj is None:
            return

        state = self._constraint_states.pop(unique_name, None)

        if state and 'previous' in state:
            self._restore_parameter_state(param_obj, state['previous'])
        else:
            self._make_parameter_independent(param_obj)
        self._emit_constraints_changed()

    def _find_parameter_object_by_unique_name(self, unique_name: str):
        """Find a parameter object by its unique_name (stable identity)."""
        for param in self._parameters_logic.parameters:
            if param.get('unique_name') == unique_name:
                return param['object']
        return None

    def _make_parameter_independent(self, param_obj) -> None:
        """Make a parameter independent, handling different parameter types."""
        try:
            param_obj.make_independent()
        except AttributeError:
            param_obj._independent = True  # Fallback for custom ERL constraints

    @Slot(int, str, str, result='QVariant')
    def validateConstraintExpression(self, dependent_index: int, relation: str, expression: str):
        try:
            instruction = self._prepare_constraint_instruction(dependent_index, relation, expression)
        except Exception as error:  # noqa: BLE001
            return {'valid': False, 'message': str(error)}

        return {
            'valid': True,
            'message': '',
            'preview': instruction.get('pretty_expression', ''),
            'relation': instruction.get('relation', '='),
            'type': instruction.get('mode', ''),
            'warning': instruction.get('warning', ''),
        }

    @Slot(int, str, str, result='QVariant')
    def addConstraint(self, dependent_index: int, relation: str, expression: str):
        try:
            instruction = self._prepare_constraint_instruction(dependent_index, relation, expression)
        except Exception as error:  # noqa: BLE001
            return {'success': False, 'message': str(error)}

        mode = instruction['mode']
        if mode == 'inequality':
            try:
                self._project_lib.add_inequality_constraint(instruction['spec'], validate=False)
            except Exception as error:  # noqa: BLE001
                return {'success': False, 'message': str(error)}
            self.constraintsChanged.emit()
            return {
                'success': True,
                'message': '',
                'preview': instruction.get('pretty_expression', ''),
                'relation': instruction.get('relation', '='),
                'type': mode,
                'warning': instruction.get('warning', ''),
            }

        dependent = self._get_independent_parameter_entries()[dependent_index]['object']
        previous_state = self._capture_parameter_state(dependent)
        self._ensure_parameter_independent(dependent)

        try:
            if mode == 'dynamic':
                dependent.make_dependent_on(
                    dependency_expression=instruction['expression'],
                    dependency_map=instruction['dependency_map'],
                )
            elif mode == 'static':
                dependent.value = instruction['value']
                dependent.free = False
                dependent._independent = False
            elif mode == 'lower_bound':
                dependent.min = instruction['value']
                dependent.free = True
            elif mode == 'upper_bound':
                dependent.max = instruction['value']
                dependent.free = True
            else:
                raise ValueError(f'Unsupported constraint mode: {mode}')
        except Exception as error:  # noqa: BLE001
            return {'success': False, 'message': str(error)}

        unique_name = getattr(dependent, 'unique_name', None)
        if unique_name is not None:
            state: dict[str, Any] = {
                'mode': mode,
                'relation': instruction.get('relation', '='),
                'previous': previous_state,
            }
            if mode == 'dynamic':
                state.update(
                    {
                        'expression': instruction.get('expression', ''),
                        'raw_expression': instruction.get('expression', ''),
                        'pretty_expression': instruction.get('pretty_expression', ''),
                        'dependency_map': instruction.get('dependency_map', {}),
                    }
                )
            else:
                value = instruction.get('value')
                numeric = self._format_numeric(float(value)) if value is not None else ''
                state.update(
                    {
                        'value': value,
                        'pretty_expression': instruction.get('pretty_expression', numeric),
                        'raw_expression': numeric,
                    }
                )
            self._constraint_states[unique_name] = state

        self._emit_constraints_changed()

        return {
            'success': True,
            'message': '',
            'preview': instruction.get('pretty_expression', ''),
            'relation': instruction.get('relation', '='),
            'type': mode,
        }

    @Slot('QVariantList')
    def constrainModelsParameters(self, model_indices: list) -> None:
        """Constrain matching parameters across selected models.

        For each parameter in the models (except the first one), find the corresponding
        parameter in the first model and create a constraint to make them equal.

        :param model_indices: List of model indices to constrain together.
        """
        if len(model_indices) < 2:
            return

        # Sort indices to ensure consistent ordering - first model becomes the reference
        model_indices = sorted([int(idx) for idx in model_indices])

        # Validate indices
        num_models = len(self._project_lib._models)
        for idx in model_indices:
            if idx < 0 or idx >= num_models:
                logger.warning('Invalid model index: %s', idx)
                return

        # Get the reference model (first in the sorted list)
        reference_model_idx = model_indices[0]
        reference_model = self._project_lib._models[reference_model_idx]

        # Build a map of parameter paths to parameters for the reference model
        # The path is relative to the model (sample/assembly/layer structure)
        reference_params_map = self._build_model_parameters_map(reference_model)

        # For each other model, find matching parameters and constrain them
        constraints_added = 0
        for model_idx in model_indices[1:]:
            model = self._project_lib._models[model_idx]
            model_params_map = self._build_model_parameters_map(model)

            for param_path, dependent_param in model_params_map.items():
                if param_path in reference_params_map:
                    reference_param = reference_params_map[param_path]

                    # Skip if already constrained
                    if not getattr(dependent_param, 'independent', True):
                        continue

                    # Skip if it's the same parameter object
                    if dependent_param.unique_name == reference_param.unique_name:
                        continue

                    try:
                        # Capture previous state for undo capability
                        previous_state = self._capture_parameter_state(dependent_param)

                        # Create a constraint: dependent = reference
                        dependent_param.make_dependent_on(
                            dependency_expression='a',
                            dependency_map={'a': reference_param},
                        )

                        # Store constraint state for display
                        unique_name = getattr(dependent_param, 'unique_name', None)
                        if unique_name is not None:
                            # Get display names with model prefix for clarity
                            # e.g., "M2 SiO2 sld = M1 SiO2 sld"
                            ref_display = self._get_parameter_display_name(reference_param, reference_model_idx)
                            dep_display = self._get_parameter_display_name(dependent_param, model_idx)

                            self._constraint_states[unique_name] = {
                                'mode': 'dynamic',
                                'relation': '=',
                                'previous': previous_state,
                                'expression': 'a',
                                'raw_expression': 'a',
                                'pretty_expression': ref_display,
                                'dependency_map': {'a': reference_param},
                                'dependent_display': dep_display,
                            }

                        constraints_added += 1
                    except Exception as e:  # noqa: BLE001
                        logger.warning('Failed to constrain parameter %s: %s', param_path, e)
                        continue

        if constraints_added > 0:
            self._emit_constraints_changed()

    def _build_model_parameters_map(self, model) -> Dict[str, DescriptorNumber]:
        """Build a map of relative parameter paths to parameter objects for a model.

        The path structure is: assembly_name/layer_name/param_name
        This allows matching parameters across models with the same structure.
        """
        params_map: Dict[str, DescriptorNumber] = {}

        # Get parameters from model structure
        for assembly_idx, assembly in enumerate(model.sample):
            # assembly_name = assembly.name
            for layer_idx, layer in enumerate(assembly.layers):
                # layer_name = layer.name
                # Get layer parameters
                for param in layer.get_all_parameters():
                    param_name = param.name
                    # Create a structural path that's independent of model name
                    path_key = f'{assembly_idx}/{layer_idx}/{param_name}'
                    params_map[path_key] = param

        return params_map

    def _get_parameter_display_name(self, param: DescriptorNumber, model_index: int | None = None) -> str:
        """Get a display name for a parameter.

        :param param: The parameter to get the display name for.
        :param model_index: Optional model index to prefix the display name with (e.g., 'M1').
        :return: Display name, optionally prefixed with model identifier.
        """
        display_name = param.name  # Fallback
        try:
            from easyscience import global_object

            # Try to find the parameter's path in the global object map
            for model in self._project_lib._models:
                path = global_object.map.find_path(model.unique_name, param.unique_name)
                if path and len(path) >= 2:
                    parent_name = global_object.map.get_item_by_key(path[-2]).name
                    param_name = global_object.map.get_item_by_key(path[-1]).name
                    display_name = f'{parent_name} {param_name}'
                    break
        except Exception:  # noqa: S110
            pass

        if model_index is not None:
            return f'M{model_index + 1} {display_name}'
        return display_name

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
