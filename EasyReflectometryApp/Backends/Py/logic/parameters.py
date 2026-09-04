import logging
import re
from collections.abc import MutableSequence
from typing import Any
from typing import List
from typing import Tuple

from easyreflectometry import Project as ProjectLib
from easyreflectometry.utils import count_fixed_parameters
from easyreflectometry.utils import count_free_parameters
from easyscience.base_classes import ModelBase
from easyscience.variable import Parameter

from .helpers import get_original_name

logger = logging.getLogger(__name__)

RESERVED_ALIAS_NAMES = {'np', 'numpy', 'math', 'pi', 'e'}


class Parameters:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._current_index = 0
        self._name_filter_criteria = ''
        self._variability_filter_criteria = 'all'

    @property
    def as_status_string(self) -> str:
        return f'{self.count_free_parameters() + self.count_fixed_parameters()} ({self.count_free_parameters()} free, {self.count_fixed_parameters()} fixed)'  # noqa: E501

    @property
    def parameters(self) -> list[dict[str, Any]]:
        parameters = self.all_parameters()
        return [parameter for parameter in parameters if self._parameter_matches_filters(parameter)]

    def all_parameters(self) -> list[dict[str, Any]]:
        return _from_parameters_to_list_of_dicts(self._project_lib.parameters, self._project_lib._models)

    @property
    def name_filter_criteria(self) -> str:
        return self._name_filter_criteria

    @property
    def variability_filter_criteria(self) -> str:
        return self._variability_filter_criteria

    def set_name_filter_criteria(self, criteria: str) -> bool:
        normalized = (criteria or '').strip()
        if normalized == self._name_filter_criteria:
            return False
        self._name_filter_criteria = normalized
        self._current_index = 0
        return True

    def set_variability_filter_criteria(self, criteria: str) -> bool:
        normalized = (criteria or 'all').strip().lower()
        if normalized not in {'all', 'free', 'fixed'}:
            normalized = 'all'
        if normalized == self._variability_filter_criteria:
            return False
        self._variability_filter_criteria = normalized
        self._current_index = 0
        return True

    def is_experiment_parameter(self, parameter: dict[str, Any]) -> bool:
        return _is_experiment_parameter(parameter)

    def _parameter_matches_filters(self, parameter: dict[str, Any]) -> bool:
        if not parameter.get('enabled', True):
            return False

        if self._variability_filter_criteria == 'free' and not parameter.get('fit', False):
            return False
        if self._variability_filter_criteria == 'fixed' and parameter.get('fit', False):
            return False

        criteria = self._name_filter_criteria
        if not criteria:
            return True

        normalized = criteria.lower()
        searchable_text = ' '.join(
            str(parameter.get(key, '')) for key in ('name', 'display_name', 'group', 'unique_name')
        ).lower()

        if normalized == 'model':
            return not _is_experiment_parameter(parameter)
        if normalized == 'experiment':
            return _is_experiment_parameter(parameter)
        if normalized in {'magnetic', 'magnetism'}:
            # The magnetic parameters are named after the physics (rho_m/theta_m),
            # so neither word appears in their text; match them explicitly.
            return 'rho_m' in searchable_text or 'theta_m' in searchable_text
        if normalized in {'cell', 'atom_site'}:
            return normalized in searchable_text
        if normalized == 'b_iso':
            return 'b_iso' in searchable_text or 'adp' in searchable_text

        return normalized in searchable_text

    def constraint_context(self) -> list[dict[str, Any]]:
        parameter_snapshot = self.all_parameters()
        context: list[dict[str, Any]] = []
        for parameter in parameter_snapshot:
            context.append(
                {
                    'alias': parameter['alias'],
                    'display_name': parameter['display_name'],
                    'group': parameter.get('group', ''),
                    'independent': parameter['independent'],
                    'kind': parameter.get('kind', 'parameter'),
                    'object': parameter['object'],
                }
            )
        return context

    def constraint_metadata(self) -> list[dict[str, Any]]:
        context = self.constraint_context()
        metadata: list[dict[str, Any]] = []
        for entry in context:
            # Include ALL parameters (both independent and dependent) for constraint expressions
            # if not entry['independent']:
            #     continue
            metadata.append(
                {
                    'alias': entry['alias'],
                    'displayName': entry['display_name'],
                    'group': entry.get('group', ''),
                    'independent': entry['independent'],
                    'kind': entry.get('kind', 'parameter'),
                }
            )
        metadata.sort(key=lambda item: item['displayName'])
        return metadata

    def current_index(self) -> int:
        return self._current_index

    def set_current_index(self, new_value: int) -> bool:
        if new_value != self._current_index:
            self._current_index = new_value
            return True
        return False

    def count_free_parameters(self) -> int:
        return count_free_parameters(self._project_lib)

    def count_fixed_parameters(self) -> int:
        return count_fixed_parameters(self._project_lib)

    def _get_enabled_parameters(self) -> List[Parameter]:
        """Return only enabled parameters from the project, filtered the same way as the parameters property."""
        # Use the parameters property which already filters by model path, then filter by enabled
        return [p['object'] for p in self.parameters if p.get('enabled', True)]

    def _get_current_parameter(self) -> Parameter:
        """Get the current parameter from enabled parameters list."""
        enabled_params = self._get_enabled_parameters()
        if 0 <= self._current_index < len(enabled_params):
            return enabled_params[self._current_index]
        return None

    def _get_current_parameter_entry(self) -> dict[str, Any] | None:
        """Get the current row (with 'kind'/'object') from the enabled rows."""
        enabled_entries = [p for p in self.parameters if p.get('enabled', True)]
        if 0 <= self._current_index < len(enabled_entries):
            return enabled_entries[self._current_index]
        return None

    def set_current_parameter_value(self, new_value: str) -> bool:
        parameter = self._get_current_parameter()
        if parameter is None:
            return False
        try:
            float_value = float(new_value)
        except ValueError:
            return False
        if float_value != parameter.value:
            try:
                parameter.value = float_value
            except (ValueError, TypeError):
                logger.exception('Failed to set parameter value to %s', float_value)
                return False
            return True
        return False

    def set_current_parameter_min(self, new_value: str) -> bool:
        parameter = self._get_current_parameter()
        if parameter is None:
            return False
        try:
            float_value = float(new_value)
        except ValueError:
            return False
        if float_value != parameter.min:
            try:
                parameter.min = float_value
            except (ValueError, TypeError):
                logger.exception('Failed to set parameter min to %s', float_value)
                return False
            return True
        return False

    def set_current_parameter_max(self, new_value: str) -> bool:
        parameter = self._get_current_parameter()
        if parameter is None:
            return False
        try:
            float_value = float(new_value)
        except ValueError:
            return False
        if float_value != parameter.max:
            try:
                parameter.max = float_value
            except (ValueError, TypeError):
                logger.exception('Failed to set parameter max to %s', float_value)
                return False
            return True
        return False

    def set_current_parameter_fit(self, new_value: bool) -> bool:
        entry = self._get_current_parameter_entry()
        if entry is None:
            return False
        if entry.get('kind') == 'inactive':
            # Same class of bug the Select-All skip fixed: an inactive
            # density knob no longer affects the reflectivity and must not
            # be tickable into the fit through any caller, QML or not.
            return False
        parameter = entry['object']
        if bool(new_value) != parameter.free:
            parameter.free = bool(new_value)
            return True
        return False

    ### Constraints
    def constraint_relations(self) -> List[dict[str, str]]:
        return [
            {'value': '=', 'text': '='},
            {'value': '>', 'text': '≥'},
            {'value': '<', 'text': '≤'},
        ]

    def constraint_arithmetic(self) -> List[str]:
        return ['', '*', '/', '+', '-']

    def add_constraint(
        self, dependent_idx: int, relational_operator: str, value: float, arithmetic_operator: str, independent_idx: int
    ) -> None:
        independent = self._project_lib.parameters[independent_idx]
        dependent = self._project_lib.parameters[dependent_idx]

        if arithmetic_operator != '' and independent_idx > -1:
            dependent.make_dependent_on(
                dependency_expression='a' + arithmetic_operator + 'b', dependency_map={'a': independent, 'b': float(value)}
            )
        elif arithmetic_operator == '' and independent_idx == -1:
            relational_operator = relational_operator.replace('=', '==')
            relational_operator = relational_operator.replace('&lt', '>')
            relational_operator = relational_operator.replace('&gt', '<')

            dependent.make_dependent_on(dependency_expression='a', dependency_map={'a': float(value)})
        else:
            logger.warning('Failed to add constraint: Unsupported type')
            return

        logger.debug(
            'Added constraint: %s, %s, %s, %s, %s',
            dependent_idx, relational_operator, value, arithmetic_operator, independent_idx,
        )


def _from_parameters_to_list_of_dicts(parameters: List[Parameter], models) -> list[dict[str, Any]]:
    """Convert parameters to list of dictionaries with simplified logic.

    Layer parameters (thickness, roughness) are prefixed with model identifier (e.g., M1, M2).
    Material parameters and model parameters (scale, background) are not prefixed to avoid duplication.
    """

    alias_registry: set[str] = set()
    processed_unique_names: set[str] = set()  # Track processed parameters to avoid duplicates

    # Layer parameter names that need model prefix
    LAYER_PARAMS = {'thickness', 'roughness'}
    # Magnetism sits one level below the layer (Layer -> LayerMagnetism -> param),
    # but belongs to the layer just as much, so it is named the same way.
    MAGNETISM_PARAMS = {'rho_m', 'theta_m'}

    def _make_alias(name: str) -> str:
        base = re.sub(r'[^0-9A-Za-z]+', '_', name).strip('_').lower()
        if not base:
            base = 'param'
        if base[0].isdigit():
            base = f'p_{base}'
        alias = base
        counter = 1
        while alias in alias_registry or alias in RESERVED_ALIAS_NAMES:
            alias = f'{base}_{counter}'
            counter += 1
        alias_registry.add(alias)
        return alias

    def _get_parameter_display_data(param: Parameter, path: list) -> Tuple[str, str]:
        """Extract display name and group from the object path.

        For layer parameters (thickness, roughness), uses the assembly name
        from the path instead of the layer name, so that renaming an assembly
        in the Model Editor is reflected in the Analysis parameters table.
        """
        if path is not None and len(path) >= 2:
            param_name = path[-1].name
            # For layer parameters the path is:
            # Model -> Sample -> Assembly -> LayerCollection -> Layer -> param
            # Use the assembly name (path[-4]) instead of the layer name (path[-2])
            if _is_layer_parameter(param) and len(path) >= 4:
                parent_name = path[-4].name
            elif _is_magnetism_parameter(param) and len(path) >= 5:
                # ... -> Assembly -> LayerCollection -> Layer -> LayerMagnetism -> param:
                # one level deeper, so the assembly is path[-5]. Without this the
                # group would read 'EasyLayerMagnetism', which names nothing.
                parent_name = path[-5].name
            else:
                parent_name = path[-2].name
            return f'{parent_name} {param_name}', parent_name
        return param.name, ''  # Fallback to parameter name without group

    def _get_dependency_expression(param: Parameter, paths: dict) -> str:
        """Get simplified dependency expression."""
        if param.independent:
            return ''

        # Check if parameter has dependency map with 'a' key (parameter dependency)
        if hasattr(param, 'dependency_map') and 'a' in param.dependency_map:
            dependent_param = param.dependency_map['a']
            if isinstance(dependent_param, Parameter):
                dep_name, _ = _get_parameter_display_data(dependent_param, paths.get(dependent_param.unique_name))
            else:
                dep_name = str(dependent_param)
            return param.dependency_expression.replace('a', dep_name)

        # Simple numerical dependency
        return f'= {param.value}'

    def _is_layer_parameter(param: Parameter) -> bool:
        """Check if parameter is a layer parameter (thickness or roughness)."""
        return param.name.lower() in LAYER_PARAMS

    def _is_magnetism_parameter(param: Parameter) -> bool:
        """Check if parameter is a layer magnetism parameter (rho_m or theta_m)."""
        return param.name.lower() in MAGNETISM_PARAMS

    def _is_per_layer_parameter(param: Parameter) -> bool:
        """Per-layer parameters exist once per model and carry the model prefix."""
        return _is_layer_parameter(param) or _is_magnetism_parameter(param)

    parameter_list = []

    # Process parameters for each model
    for model_idx, model in enumerate(models):
        model_prefix = get_original_name(model)
        # Object paths replace the global_object.map graph, which the new
        # easyscience core no longer populates with parent->child edges.
        paths = _build_param_object_paths(model)

        for parameter in parameters:
            # Skip parameters not in this model's tree
            path = paths.get(parameter.unique_name)
            if path is None:
                continue

            # For non-layer parameters, skip if already processed (they're shared across models)
            is_layer_param = _is_per_layer_parameter(parameter)
            if not is_layer_param:
                if parameter.unique_name in processed_unique_names:
                    continue
                processed_unique_names.add(parameter.unique_name)

            display_name, group_name = _get_parameter_display_data(parameter, path)

            # Add model prefix only to layer parameters (thickness, roughness)
            if is_layer_param:
                prefixed_display_name = f'{model_prefix} {display_name}'
            else:
                prefixed_display_name = display_name

            alias = _make_alias(prefixed_display_name or parameter.name)
            param_value = float(parameter.value)
            is_derived = _is_derived_parameter(parameter, model)
            # A density material's input knobs (density, mw, scattering
            # lengths) stop affecting the reflectivity once the material's
            # sld/isld are decoupled — shown greyed with a note, never hidden
            # (enabled must stay True: _parameter_matches_filters drops
            # enabled=False rows from the list entirely).
            is_inactive = _is_inactive_density_knob(parameter, path)
            parameter_list.append(
                {
                    'name': prefixed_display_name,
                    'display_name': prefixed_display_name,
                    'group': group_name,
                    'alias': alias,
                    'unique_name': parameter.unique_name,
                    'value': param_value,
                    # None means the minimizer produced no error bars (e.g. lmfit's
                    # gradient-free methods); the GUI renders it as 'n/a', distinct
                    # from a numeric zero which is shown as an empty cell.
                    'error': float(parameter.error) if parameter.error is not None else None,
                    'max': float(parameter.max),
                    'min': float(parameter.min),
                    'units': parameter.unit,
                    'fit': False if (is_derived or is_inactive) else parameter.free,
                    'independent': parameter.independent,
                    'dependency': (
                        _INACTIVE_KNOB_NOTE
                        if is_inactive
                        else _DERIVED_DESCRIPTIONS.get(parameter.name, 'derived')
                        if is_derived
                        else _get_dependency_expression(parameter, paths)
                    ),
                    # Derived "calculation" parameters (e.g. the model's total film
                    # thickness) are computed from the layers: shown read-only, never
                    # fitted, but usable as aliases in constraint expressions.
                    'kind': 'derived' if is_derived else 'inactive' if is_inactive else 'parameter',
                    'readOnly': is_derived or is_inactive,
                    'enabled': parameter.enabled if hasattr(parameter, 'enabled') else True,
                    'object': parameter,  # Direct reference to the Parameter object
                }
            )

    return parameter_list


_DERIVED_DESCRIPTIONS = {
    'total_thickness': 'Σ film layer thicknesses',
}

# The input knobs of a density material (MaterialDensity); inactive when the
# material's sld/isld are decoupled from them.
_DENSITY_KNOB_NAMES = {'density', 'molecular_weight', 'scattering_length_real', 'scattering_length_imag'}
_INACTIVE_KNOB_NOTE = 'unused (SLD is fitted directly)'


def _is_inactive_density_knob(parameter: Parameter, path) -> bool:
    """True for a density-material knob whose material is decoupled.

    Duck-typed on the owner's ``sld_coupled`` (only ``MaterialDensity``
    carries it); the getattr default True keeps every other owner active.
    """
    if path is None or len(path) < 2:
        return False
    if parameter.name not in _DENSITY_KNOB_NAMES:
        return False
    return getattr(path[-2], 'sld_coupled', True) is False


def _is_derived_parameter(parameter: Parameter, model) -> bool:
    """True for the model-owned computed parameters (currently ``Model.total_thickness``)."""
    derived = getattr(type(model), 'total_thickness', None)
    if derived is None:
        return False
    try:
        return model.total_thickness is parameter
    except Exception:  # noqa: BLE001
        return False


def _build_param_object_paths(model) -> dict:
    """Map each parameter's ``unique_name`` to its object chain ``[model, ..., parameter]``.

    Replaces ``global_object.map.find_path``: the new easyscience core
    (``NewBase`` / ``ModelBase`` / ``EasyList``) registers vertices but no
    parent->child edges, so the map graph can no longer be walked. The chain
    mirrors the old map path, e.g.
    ``Model -> Sample -> Assembly -> LayerCollection -> Layer -> [Material ->] Parameter``,
    so the existing index logic (``path[-4]`` for the assembly, ``path[-2]``
    for the immediate parent) keeps working.
    """
    paths: dict[str, list] = {}
    visited: set[int] = {id(model)}

    def _children(obj) -> list:
        # Collections expose their members by iteration, not as attributes.
        if isinstance(obj, MutableSequence):
            return list(obj)
        collections = []
        others = []
        for attr_name in dir(obj):
            if attr_name.startswith('_'):
                continue
            try:
                value = getattr(obj, attr_name)
            except Exception:
                continue
            if isinstance(value, MutableSequence):
                collections.append(value)
            elif isinstance(value, (Parameter, ModelBase)):
                others.append(value)
        # Canonical containers first. Assemblies expose alias properties
        # (``front_layer``/``back_layer`` point into ``layers``) that sort
        # before 'layers' alphabetically; if an alias won the first-found
        # path, the chain would skip the LayerCollection level and the
        # positional lookups (``path[-4]`` = assembly) would resolve to the
        # wrong ancestor, mislabelling superphase/subphase parameters.
        return collections + others

    def _visit(obj, chain: list) -> None:
        for child in _children(obj):
            if isinstance(child, Parameter):
                paths.setdefault(child.unique_name, chain + [child])
            elif isinstance(child, (ModelBase, MutableSequence)) and id(child) not in visited:
                visited.add(id(child))
                _visit(child, chain + [child])

    _visit(model, [model])
    return paths


def _is_experiment_parameter(parameter: dict[str, Any]) -> bool:
    searchable_text = ' '.join(str(parameter.get(key, '')) for key in ('name', 'display_name', 'group', 'unique_name')).lower()
    experiment_markers = (
        'experiment',
        'dataset',
        'instrument',
        'resolution',
        'asymmetry',
        'background',
        'scale',
        'probe',
    )
    return any(marker in searchable_text for marker in experiment_markers)
