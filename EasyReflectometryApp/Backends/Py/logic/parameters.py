from typing import List

from easyreflectometry import Project as ProjectLib
from easyreflectometry.utils import count_fixed_parameters
from easyreflectometry.utils import count_free_parameters
from easyscience import global_object
from easyscience.variable import Parameter


class Parameters:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._current_index = 0

    @property
    def as_status_string(self) -> str:
        return f'{self.count_free_parameters() + self.count_fixed_parameters()} ({self.count_free_parameters()} free, {self.count_fixed_parameters()} fixed)'  # noqa: E501

    @property
    def parameters(self) -> List[str]:
        return _from_parameters_to_list_of_dicts(
            self._project_lib.parameters, self._project_lib._models[self._project_lib.current_model_index].unique_name
        )

    def current_index(self) -> int:
        return self._current_index

    def set_current_index(self, new_value: int) -> None:
        if new_value != self._current_index:
            self._current_index = new_value
            return True
        return False

    def count_free_parameters(self) -> int:
        return count_free_parameters(self._project_lib)

    def count_fixed_parameters(self) -> int:
        return count_fixed_parameters(self._project_lib)

    def set_current_parameter_value(self, new_value: str) -> bool:
        parameters = self._project_lib.enabled_parameters
        if float(new_value) != parameters[self._current_index].value:
            try:
                parameters[self._current_index].value = float(new_value)
            except ValueError:
                pass
            return True
        return False

    def set_current_parameter_min(self, new_value: str) -> bool:
        parameters = self._project_lib.enabled_parameters
        if float(new_value) != parameters[self._current_index].min:
            try:
                parameters[self._current_index].min = float(new_value)
            except ValueError:
                pass
            return True
        return False

    def set_current_parameter_max(self, new_value: str) -> bool:
        parameters = self._project_lib.enabled_parameters
        if float(new_value) != parameters[self._current_index].max:
            try:
                parameters[self._current_index].max = float(new_value)
            except ValueError:
                pass
            return True
        return False

    def set_current_parameter_fit(self, new_value: str) -> bool:
        parameters = self._project_lib.enabled_parameters
        if bool(new_value) != parameters[self._current_index].free:
            parameters[self._current_index].free = bool(new_value)
            return True
        return False

    ### Constraints
    def constraint_relations(self) -> List[str]:
        return ['=', '&lt', '&gt']

    def constraint_arithmetic(self) -> List[str]:
        return ['', '*', '/', '+', '-']

    def add_constraint(
        self, dependent_idx: int, relational_operator: str, value: float, arithmetic_operator: str, independent_idx: int
    ) -> None:
        independent = self._project_lib.enabled_parameters[independent_idx]
        dependent = self._project_lib.enabled_parameters[dependent_idx]

        if arithmetic_operator != '' and independent_idx > -1:
            dependent.make_dependent_on(
                dependency_expression='a' + arithmetic_operator + 'b', dependency_map={'a': independent, 'b': float(value)})
        elif arithmetic_operator == '' and independent_idx == -1:
            relational_operator = relational_operator.replace('=', '==')
            relational_operator = relational_operator.replace('&lt', '>')
            relational_operator = relational_operator.replace('&gt', '<')

            dependent.make_dependent_on(dependency_expression='a', dependency_map={'a': float(value)})
        else:
            print('Failed to add constraint: Unsupported type')
            return

        print(f'{dependent_idx}, {relational_operator}, {value}, {arithmetic_operator}, {independent_idx}')

def _from_parameters_to_list_of_dicts(parameters: List[Parameter], model_unique_name: str) -> list[dict[str, str]]:
    """Convert parameters to list of dictionaries with simplified logic."""

    def _get_parameter_display_name(param: Parameter) -> str:
        """Extract display name from parameter path."""
        path = global_object.map.find_path(model_unique_name, param.unique_name)
        if len(path) >= 2:
            parent_name = global_object.map.get_item_by_key(path[-2]).name
            param_name = global_object.map.get_item_by_key(path[-1]).name
            return f'{parent_name} {param_name}'
        return param.name  # Fallback to parameter name

    def _get_dependency_expression(param: Parameter) -> str:
        """Get simplified dependency expression."""
        if param.independent:
            return ''

        # Check if parameter has dependency map with 'a' key (parameter dependency)
        if hasattr(param, 'dependency_map') and 'a' in param.dependency_map:
            dependent_param = param.dependency_map['a']
            dep_name = _get_parameter_display_name(dependent_param)
            return param.dependency_expression.replace('a', dep_name)

        # Simple numerical dependency
        return f'= {param.value}'

    parameter_list = []
    for parameter in parameters:
        # Skip parameters not in the current model path
        if not global_object.map.find_path(model_unique_name, parameter.unique_name):
            continue

        parameter_list.append({
            'name': _get_parameter_display_name(parameter),
            'value': float(parameter.value),
            'error': float(parameter.variance),
            'max': float(parameter.max),
            'min': float(parameter.min),
            'units': parameter.unit,
            'fit': parameter.free,
            'independent': parameter.independent,
            'dependency': _get_dependency_expression(parameter),
            'object': parameter,  # Direct reference to the Parameter object
        })

    return parameter_list
