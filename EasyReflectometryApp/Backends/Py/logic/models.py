from typing import Union

import numpy as np

from easyreflectometry import Project as ProjectLib
from easyreflectometry.model import Model
from easyreflectometry.model import ModelCollection
from easyreflectometry.model.resolution_functions import DEFAULT_RESOLUTION_FWHM_PERCENTAGE
from easyreflectometry.model.resolution_functions import LinearSpline
from easyreflectometry.model.resolution_functions import PercentageFwhm
from easyreflectometry.model.resolution_functions import Pointwise

from .helpers import get_original_name


RESOLUTION_FUNCTION_TYPES = ('PercentageFwhm', 'LinearSpline', 'Pointwise')


class Models:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._models = project_lib._models

    @property
    def index(self) -> int:
        return self._project_lib.current_model_index

    @index.setter
    def index(self, new_value: Union[int, str]) -> None:
        self._project_lib.current_model_index = int(new_value)

    @property
    def name_at_current_index(self) -> str:
        return get_original_name(self._models[self.index])

    @property
    def scaling_at_current_index(self) -> float:
        return self._models[self.index].scale.value

    @property
    def background_at_current_index(self) -> float:
        return self._models[self.index].background.value

    @property
    def resolution_at_current_index(self) -> str:
        if isinstance(self._models[self.index].resolution_function, PercentageFwhm):
            return str(self._models[self.index].resolution_function.constant)
        else:
            return '-'

    @property
    def resolution_type_names(self) -> list[str]:
        return list(RESOLUTION_FUNCTION_TYPES)

    @property
    def resolution_type_at_current_index(self) -> str:
        resolution_function = self._models[self.index].resolution_function
        if isinstance(resolution_function, PercentageFwhm):
            return 'PercentageFwhm'
        if isinstance(resolution_function, LinearSpline):
            return 'LinearSpline'
        if isinstance(resolution_function, Pointwise):
            return 'Pointwise'
        raise ValueError(f'Unsupported resolution function type: {type(resolution_function)!r}')

    @property
    def resolution_type_index_at_current_index(self) -> int:
        return RESOLUTION_FUNCTION_TYPES.index(self.resolution_type_at_current_index)

    @property
    def models(self) -> list[dict[str, str]]:
        return _from_models_collection_to_list_of_dicts(self._models)

    @property
    def models_names(self) -> list[str]:
        return [element['label'] for element in self.models]

    def set_name_at_current_index(self, new_value: str) -> bool:
        if self._models[self.index].name != new_value:
            self._models[self.index].name = new_value
            return True
        return False

    def set_scaling_at_current_index(self, new_value: str) -> bool:
        if self._models[self.index].scale.value != float(new_value):
            self._models[self.index].scale.value = float(new_value)
            return True
        return False

    def set_background_at_current_index(self, new_value: str) -> bool:
        if self._models[self.index].background.value != float(new_value):
            self._models[self.index].background.value = float(new_value)
            return True
        return False

    def set_resolution_at_current_index(self, new_value: str) -> bool:
        if isinstance(self._models[self.index].resolution_function, PercentageFwhm):
            if self._models[self.index].resolution_function.constant != float(new_value):
                self._models[self.index].resolution_function.constant = float(new_value)
                return True
        return False

    def set_resolution_type_at_current_index(self, new_value: Union[int, str]) -> bool:
        try:
            if isinstance(new_value, int):
                resolution_type = RESOLUTION_FUNCTION_TYPES[new_value]
            else:
                resolution_type = new_value
        except IndexError:
            return False

        if self.resolution_type_at_current_index == resolution_type:
            return False

        try:
            self._models[self.index].resolution_function = self._resolution_function_for_type(resolution_type)
        except ValueError:
            return False
        return True

    def _resolution_function_for_type(self, resolution_type: str):
        current_resolution = self._models[self.index].resolution_function
        if resolution_type == 'PercentageFwhm':
            constant = DEFAULT_RESOLUTION_FWHM_PERCENTAGE
            if isinstance(current_resolution, PercentageFwhm):
                constant = current_resolution.constant
            return PercentageFwhm(constant)

        experiment = self._current_experiment()
        if experiment is None or len(experiment.x) == 0:
            raise ValueError(f'Cannot set resolution type {resolution_type} without experimental data')

        q_data_points = np.asarray(experiment.x)
        resolution_variances = np.asarray(experiment.xe)

        if resolution_type == 'LinearSpline':
            return LinearSpline(q_data_points=q_data_points, fwhm_values=np.sqrt(resolution_variances))

        if resolution_type == 'Pointwise':
            return Pointwise([q_data_points, np.asarray(experiment.y), resolution_variances])

        raise ValueError(f'Unsupported resolution type: {resolution_type}')

    def _current_experiment(self):
        try:
            return self._project_lib.experimental_data_for_model_at_index(self.index)
        except IndexError:
            return None

    def remove_at_index(self, value: str) -> None:
        self._models.pop(int(value))

    def default_model_content(self, model: Model) -> None:
        """Set the default content for a model."""
        model.add_assemblies()
        # Superphase (Air layer)
        air_material = self._project_lib._materials[self._project_lib.get_index_air()]
        model.sample.data[0].layers.data[0].material = air_material
        model.sample.data[0].layers.data[0].thickness = 0.0
        model.sample.data[0].layers.data[0].roughness = 0.0
        model.sample.data[0].layers.data[0].name = air_material.name + ' Layer'
        model.sample.data[0].name = 'Superphase'

        # Middle layer (SiO2)
        sio2_material = self._project_lib._materials[self._project_lib.get_index_sio2()]
        model.sample.data[1].layers.data[0].material = sio2_material
        model.sample.data[1].layers.data[0].thickness = 100.0
        model.sample.data[1].layers.data[0].roughness = 3.0
        model.sample.data[1].layers.data[0].name = sio2_material.name + ' Layer'
        model.sample.data[1].name = 'SiO2'

        # Subphase (Si substrate)
        si_material = self._project_lib._materials[self._project_lib.get_index_si()]
        model.sample.data[2].layers.data[0].material = si_material
        model.sample.data[2].name = 'Substrate'
        model.sample.data[2].layers.data[0].name = si_material.name + ' Layer'
        model.sample.data[2].layers.data[0].thickness = 0.0
        model.sample.data[2].layers.data[0].roughness = 1.2

    def add_new(self) -> None:
        self._models.add_model()
        self.default_model_content(self._models[-1])
        # Update index to point to the new model
        self.index = len(self._models) - 1

    def duplicate_selected_model(self) -> None:
        self._models.duplicate_model(self.index)
        # Update index to point to the duplicated model
        self.index = len(self._models) - 1

    def move_selected_up(self) -> None:
        if self.index > 0:
            self._models.move_up(self.index)
            self.index = self.index - 1

    def move_selected_down(self) -> None:
        if self.index < len(self._models) - 1:
            self._models.move_down(self.index)
            self.index = self.index + 1


def _from_models_collection_to_list_of_dicts(models_collection: ModelCollection) -> list[dict[str, str]]:
    models_list = []
    for model in models_collection:
        models_list.append(
            {
                'label': get_original_name(model),
                'color': str(model.color),
            }
        )
    return models_list
