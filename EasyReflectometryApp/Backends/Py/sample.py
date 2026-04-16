import math
import numbers
import re
from typing import Any
from typing import Dict
from typing import Tuple

import numpy as np
from asteval import Interpreter
from easyreflectometry import Project as ProjectLib
from easyscience.variable.descriptor_number import DescriptorNumber
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

    qRangeChanged = Signal()
    constraintsChanged = Signal()

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
        self._constraint_states: Dict[str, dict[str, Any]] = {}

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
        self._assemblies_logic.set_type_at_current_index(new_value)
        self._clearCacheAndEmitLayersChanged()
        self.assembliesTableChanged.emit()
        self.assembliesIndexChanged.emit()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot(int, str)
    def setAssemblyTypeAtIndex(self, index: int, new_value: str) -> None:
        if self._assemblies_logic.set_type_at_index(index, new_value):
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
        self._clearCacheAndEmitLayersChanged()
        self.assembliesTableChanged.emit()
        self.assembliesIndexChanged.emit()
        self.externalRefreshPlot.emit()
        self.externalSampleChanged.emit()

    @Slot()
    def duplicateSelectedAssembly(self) -> None:
        self._assemblies_logic.duplicate_selected()
        self._clearCacheAndEmitLayersChanged()
        self.assembliesTableChanged.emit()
        self.assembliesIndexChanged.emit()
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

    def _evaluate_constraint_expression(
        self,
        expression: str,
        dependency_map: Dict[str, DescriptorNumber],
        all_aliases: Dict[str, DescriptorNumber] | None = None,
    ) -> DescriptorNumber | numbers.Number:
        """Evaluate constraint expression with all available parameter aliases in scope."""
        interpreter = Interpreter(config=_ASTEVAL_CONFIG)

        # Add global symbols (numpy, etc.)
        for name, value in _GLOBAL_SYMBOLS.items():
            interpreter.symtable[name] = value
            if isinstance(value, numbers.Number):
                interpreter.readonly_symbols.add(name)

        # Add ALL parameter aliases to the symbol table (not just dependencies)
        # This allows validation to work even if we haven't detected the parameter yet
        aliases_to_add = all_aliases if all_aliases is not None else dependency_map
        for alias, dependency in aliases_to_add.items():
            interpreter.symtable[alias] = dependency
            interpreter.readonly_symbols.add(alias)

        try:
            result = interpreter.eval(expression, raise_errors=True)
        except Exception as e:
            # Provide helpful error message showing available aliases
            if 'not defined' in str(e):
                available = ', '.join(sorted(aliases_to_add.keys())[:10])  # Show first 10
                raise NameError(f'{str(e)}\nAvailable aliases: {available}...') from None
            raise
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
            raise ValueError('Inequality constraints cannot reference other parameters.')

        numeric_value = self._to_float(evaluation_result)
        mode = 'lower_bound' if relation == '>' else 'upper_bound'
        return {
            'mode': mode,
            'value': numeric_value,
            'pretty_expression': self._format_numeric(numeric_value),
            'relation': relation,
        }

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

        for entry in context:
            parameter_obj = entry['object']
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
                    'expression': expression_display,
                    'rawExpression': raw_expression,
                    'relation': relation,
                    'type': mode,
                }
            )

        return constraints

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

        param_name = constraints_list[index]['dependentName']
        param_obj = self._find_parameter_object_by_name(param_name)

        if param_obj is None:
            return

        unique_name = getattr(param_obj, 'unique_name', None)
        state = self._constraint_states.pop(unique_name, None) if unique_name is not None else None

        if state and 'previous' in state:
            self._restore_parameter_state(param_obj, state['previous'])
        else:
            self._make_parameter_independent(param_obj)
        self.constraintsChanged.emit()
        self.externalSampleChanged.emit()
        self.layersChange.emit()

    def _find_parameter_object_by_name(self, param_name: str):
        """Find parameter object by name.

        Handles both regular names ('SiO2 sld') and model-prefixed names ('M2 SiO2 sld').
        """
        parameters = self._parameters_logic.parameters

        # Direct match by display name
        for param in parameters:
            if param['name'] == param_name:
                return param['object']

        # Check constraint states for model-prefixed dependent_display
        for unique_name, state in self._constraint_states.items():
            if state.get('dependent_display') == param_name:
                # Find the parameter by unique_name
                for param in parameters:
                    if param.get('unique_name') == unique_name:
                        return param['object']

        # Try stripping model prefix (e.g., 'M2 SiO2 sld' -> 'SiO2 sld')
        import re

        prefix_match = re.match(r'^M\d+\s+(.+)$', param_name)
        if prefix_match:
            stripped_name = prefix_match.group(1)
            for param in parameters:
                if param['name'] == stripped_name:
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
        }

    @Slot(int, str, str, result='QVariant')
    def addConstraint(self, dependent_index: int, relation: str, expression: str):
        try:
            instruction = self._prepare_constraint_instruction(dependent_index, relation, expression)
        except Exception as error:  # noqa: BLE001
            return {'success': False, 'message': str(error)}

        dependent = self._get_independent_parameter_entries()[dependent_index]['object']
        previous_state = self._capture_parameter_state(dependent)
        self._ensure_parameter_independent(dependent)

        mode = instruction['mode']

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

        self.constraintsChanged.emit()
        self.externalSampleChanged.emit()
        self.layersChange.emit()

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
                print(f'Invalid model index: {idx}')
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
                        print(f'Failed to constrain parameter {param_path}: {e}')
                        continue

        if constraints_added > 0:
            self.constraintsChanged.emit()
            self.externalSampleChanged.emit()
            self.layersChange.emit()

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
                for param in layer.get_parameters():
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
