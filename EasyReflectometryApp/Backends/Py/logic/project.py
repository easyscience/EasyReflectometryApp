from copy import copy
from pathlib import Path

import numpy as np
from easyreflectometry import Project as ProjectLib


class Project:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._last_q_range_changed = False
        self._project_lib.default_model()
        self._update_enablement_of_fixed_layers_for_model(0)

    @property
    def created(self) -> bool:
        return self._project_lib.created

    @property
    def path(self) -> str:
        return str(self._project_lib.path)

    @property
    def root_path(self) -> str:
        return str(self._project_lib.path.parent)

    @root_path.setter
    def root_path(self, new_value: str) -> None:
        self._project_lib.set_path_project_parent(Path(new_value).parent)

    @property
    def name(self) -> str:
        return self._project_lib._info['name']

    @name.setter
    def name(self, new_value: str) -> None:
        self._project_lib._info['name'] = new_value

    @property
    def description(self) -> str:
        return self._project_lib._info['short_description']

    @description.setter
    def description(self, new_value: str) -> None:
        self._project_lib._info['short_description'] = new_value

    @property
    def creation_date(self) -> str:
        return self._project_lib._info['modified']

    @property
    def q_min(self) -> float:
        return self._project_lib.q_min

    def set_q_min(self, new_value: str) -> None:
        if float(new_value) != self._project_lib.q_min:
            self._project_lib.q_min = float(new_value)
            return True
        return False

    @property
    def q_max(self) -> float:
        return self._project_lib.q_max

    def set_q_max(self, new_value: str) -> None:
        if float(new_value) != self._project_lib.q_max:
            self._project_lib.q_max = float(new_value)
            return True
        return False

    @property
    def q_resolution(self) -> int:
        return self._project_lib.q_resolution

    def set_q_resolution(self, new_value: str) -> None:
        if float(new_value) != self._project_lib.q_resolution:
            self._project_lib.q_resolution = int(new_value)
            return True
        return False

    @property
    def experimental_data_at_current_index(self) -> bool:
        experimental_data = False
        try:
            self._project_lib.experimental_data_for_model_at_index(self._project_lib._current_model_index)
            experimental_data = True
        except IndexError:
            pass
        return experimental_data

    def _update_enablement_of_fixed_layers_for_model(self, index: int) -> None:
        sample = self._project_lib.models[index].sample
        sample[0].layers[0].thickness.enabled = False
        sample[0].layers[0].roughness.enabled = False
        sample[-1].layers[-1].thickness.enabled = False

    def info(self) -> dict:
        info = copy(self._project_lib._info)
        info['location'] = self._project_lib.path
        return info

    def create(self) -> None:
        self._project_lib.create()
        self._project_lib.save_as_json()

    def save(self) -> None:
        self._project_lib.save_as_json(overwrite=True)

    def load(self, path: str) -> None:
        self._project_lib.load_from_json(path)

    def load_experiment(self, path: str) -> bool:
        self._project_lib.load_experiment_for_model_at_index(path, self._project_lib._current_model_index)
        return self._sync_q_max_with_loaded_experiments()

    def load_new_experiment(self, path: str) -> bool:
        self._project_lib.load_new_experiment(path)
        return self._sync_q_max_with_loaded_experiments()

    def count_datasets_in_file(self, path: str) -> int:
        return self._project_lib.count_datasets_in_file(path)

    def load_all_experiments_from_file(self, path: str) -> tuple[int, bool]:
        loaded_count = self._project_lib.load_all_experiments_from_file(path)
        q_max_changed = self._sync_q_max_with_loaded_experiments()
        return loaded_count, q_max_changed

    def _sync_q_max_with_loaded_experiments(self) -> bool:
        """Set model q_max to the largest q value found in loaded experiments.

        :return: True if q_max was changed, False otherwise.
        :rtype: bool
        """
        experiments = self._project_lib._experiments
        if not experiments:
            return False

        if hasattr(experiments, 'values'):
            experiment_iterable = experiments.values()
        else:
            experiment_iterable = experiments

        q_max_candidates = []
        for experiment in experiment_iterable:
            x_values = getattr(experiment, 'x', None)
            if x_values is None:
                continue

            q_values = np.asarray(x_values, dtype=float)
            if q_values.size == 0:
                continue

            finite_q_values = q_values[np.isfinite(q_values)]
            if finite_q_values.size == 0:
                continue

            q_max_candidates.append(float(np.max(finite_q_values)))

        if not q_max_candidates:
            return False

        new_q_max = max(q_max_candidates)
        if new_q_max != self._project_lib.q_max:
            self._project_lib.q_max = new_q_max
            return True
        return False

    def set_sample_from_orso(self, sample) -> None:
        self._project_lib.set_sample_from_orso(sample)

    def add_sample_from_orso(self, sample) -> None:
        """Add a new model with the given sample to the existing model collection."""
        self._project_lib.add_sample_from_orso(sample)
        new_model_index = len(self._project_lib.models) - 1
        self._update_enablement_of_fixed_layers_for_model(new_model_index)

    def replace_models_from_orso(self, sample) -> None:
        """Replace all existing models with a single model built from the loaded sample."""
        self._project_lib.replace_models_from_orso(sample)
        self._update_enablement_of_fixed_layers_for_model(0)

    def reset(self) -> None:
        self._project_lib.reset()
        self._project_lib.default_model()
