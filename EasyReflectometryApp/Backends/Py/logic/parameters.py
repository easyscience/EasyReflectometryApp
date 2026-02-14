import re
from typing import Any
from typing import List
from typing import Tuple

from easyreflectometry import Project as ProjectLib
from easyreflectometry.utils import count_fixed_parameters
from easyreflectometry.utils import count_free_parameters
from easyscience import global_object
from easyscience.variable import Parameter

from .helpers import get_original_name

RESERVED_ALIAS_NAMES = {'np', 'numpy', 'math', 'pi', 'e'}


class Parameters:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._current_index = 0

    @property
    def as_status_string(self) -> str:
        return f'{self.count_free_parameters() + self.count_fixed_parameters()} ({self.count_free_parameters()} free, {self.count_fixed_parameters()} fixed)'  # noqa: E501

    @property
    def parameters(self) -> list[dict[str, Any]]:
        return _from_parameters_to_list_of_dicts(self._project_lib.parameters, self._project_lib._models)

    def constraint_context(self) -> list[dict[str, Any]]:
        parameter_snapshot = self.parameters
        context: list[dict[str, Any]] = []
        for parameter in parameter_snapshot:
            context.append(
                {
                    'alias': parameter['alias'],
                    'display_name': parameter['display_name'],
                    'group': parameter.get('group', ''),
                    'independent': parameter['independent'],
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

    def set_current_parameter_value(self, new_value: str) -> bool:
        parameter = self._get_current_parameter()
        if parameter is None:
            return False
        if float(new_value) != parameter.value:
            try:
                parameter.value = float(new_value)
            except ValueError:
                pass
            return True
        return False

    def set_current_parameter_min(self, new_value: str) -> bool:
        parameter = self._get_current_parameter()
        if parameter is None:
            return False
        if float(new_value) != parameter.min:
            try:
                parameter.min = float(new_value)
            except ValueError:
                pass
            return True
        return False

    def set_current_parameter_max(self, new_value: str) -> bool:
        parameter = self._get_current_parameter()
        if parameter is None:
            return False
        if float(new_value) != parameter.max:
            try:
                parameter.max = float(new_value)
            except ValueError:
                pass
            return True
        return False

    def set_current_parameter_fit(self, new_value: bool) -> bool:
        parameter = self._get_current_parameter()
        if parameter is None:
            return False
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
            print('Failed to add constraint: Unsupported type')
            return

        print(f'{dependent_idx}, {relational_operator}, {value}, {arithmetic_operator}, {independent_idx}')


def _from_parameters_to_list_of_dicts(parameters: List[Parameter], models) -> list[dict[str, Any]]:
    """Convert parameters to list of dictionaries with simplified logic.

    Layer parameters (thickness, roughness) are prefixed with model identifier (e.g., M1, M2).
    Material parameters and model parameters (scale, background) are not prefixed to avoid duplication.
    """

    alias_registry: set[str] = set()
    processed_unique_names: set[str] = set()  # Track processed parameters to avoid duplicates

    # Layer parameter names that need model prefix
    LAYER_PARAMS = {'thickness', 'roughness'}

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

    def _get_parameter_display_data(param: Parameter, model_unique_name: str) -> Tuple[str, str]:
        """Extract display name and group from parameter path."""
        path = global_object.map.find_path(model_unique_name, param.unique_name)
        if len(path) >= 2:
            parent_name = global_object.map.get_item_by_key(path[-2]).name
            param_name = global_object.map.get_item_by_key(path[-1]).name
            return f'{parent_name} {param_name}', parent_name
        return param.name, ''  # Fallback to parameter name without group

    def _get_dependency_expression(param: Parameter, model_unique_name: str) -> str:
        """Get simplified dependency expression."""
        if param.independent:
            return ''

        # Check if parameter has dependency map with 'a' key (parameter dependency)
        if hasattr(param, 'dependency_map') and 'a' in param.dependency_map:
            dependent_param = param.dependency_map['a']
            if isinstance(dependent_param, Parameter):
                dep_name, _ = _get_parameter_display_data(dependent_param, model_unique_name)
            else:
                dep_name = str(dependent_param)
            return param.dependency_expression.replace('a', dep_name)

        # Simple numerical dependency
        return f'= {param.value}'

    def _is_layer_parameter(param: Parameter) -> bool:
        """Check if parameter is a layer parameter (thickness or roughness)."""
        return param.name.lower() in LAYER_PARAMS

    parameter_list = []

    # Process parameters for each model
    for model_idx, model in enumerate(models):
        model_unique_name = model.unique_name
        model_prefix = get_original_name(model)

        for parameter in parameters:
            # Skip parameters not in this model's path
            if not global_object.map.find_path(model_unique_name, parameter.unique_name):
                continue

            # For non-layer parameters, skip if already processed (they're shared across models)
            is_layer_param = _is_layer_parameter(parameter)
            if not is_layer_param:
                if parameter.unique_name in processed_unique_names:
                    continue
                processed_unique_names.add(parameter.unique_name)

            display_name, group_name = _get_parameter_display_data(parameter, model_unique_name)

            # Add model prefix only to layer parameters (thickness, roughness)
            if is_layer_param:
                prefixed_display_name = f'{model_prefix} {display_name}'
            else:
                prefixed_display_name = display_name

            alias = _make_alias(prefixed_display_name or parameter.name)
            parameter_list.append(
                {
                    'name': prefixed_display_name,
                    'display_name': prefixed_display_name,
                    'group': group_name,
                    'alias': alias,
                    'unique_name': parameter.unique_name,
                    'value': float(parameter.value),
                    'error': float(parameter.variance),
                    'max': float(parameter.max),
                    'min': float(parameter.min),
                    'units': parameter.unit,
                    'fit': parameter.free,
                    'independent': parameter.independent,
                    'dependency': _get_dependency_expression(parameter, model_unique_name),
                    'enabled': parameter.enabled if hasattr(parameter, 'enabled') else True,
                    'object': parameter,  # Direct reference to the Parameter object
                }
            )

    return parameter_list
