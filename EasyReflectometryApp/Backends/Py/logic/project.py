from copy import copy
from pathlib import Path

from easyreflectometry import Project as ProjectLib


class Project:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib

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

    def load_experiment(self, path: str) -> None:
        self._project_lib.load_experiment_for_model_at_index(path, self._project_lib._current_model_index)

    def load_new_experiment(self, path: str) -> None:
        self._project_lib.load_new_experiment(path)

    def reset(self) -> None:
        self._project_lib.reset()
        self._project_lib.default_model()
