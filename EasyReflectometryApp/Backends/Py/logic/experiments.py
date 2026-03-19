from easyreflectometry import Project as ProjectLib


class Experiments:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib

    def _ordered_experiment_items(self) -> list[tuple[object, object]]:
        """Return experiments as ordered ``(key, experiment)`` pairs.

        Supports mapping-like storage without assuming contiguous integer keys.
        """
        experiments = self._project_lib._experiments
        if not experiments:
            return []

        if hasattr(experiments, 'items'):
            items = list(experiments.items())
            try:
                items.sort(key=lambda item: item[0])
            except TypeError:
                pass
            return items

        return list(enumerate(experiments))

    def _experiment_at_index(self, index: int):
        items = self._ordered_experiment_items()
        if 0 <= index < len(items):
            return items[index][1]
        return None

    def _experiment_key_at_index(self, index: int):
        items = self._ordered_experiment_items()
        if 0 <= index < len(items):
            return items[index][0]
        return None

    def available(self) -> list[str]:
        experiments_name = []
        try:
            for _, exp in self._ordered_experiment_items():
                experiments_name.append(exp.name)
        except IndexError:
            pass
        return experiments_name

    def current_index(self) -> int:
        return self._project_lib._current_experiment_index

    def set_current_index(self, new_value: int) -> None:
        if new_value != self._project_lib._current_experiment_index:
            self._project_lib._current_experiment_index = new_value
            # experiment = self._experiment_at_index(new_value)
            # if experiment and experiment.model in self._project_lib._models:
            #     self._project_lib.current_model_index = self._project_lib._models.index(experiment.model)
            return True
        return False

    def set_experiment_name(self, new_name: str) -> None:
        exp = self._experiment_at_index(self._project_lib._current_experiment_index)
        if exp:
            exp.name = new_name

    def set_experiment_name_at_index(self, index: int, new_name: str) -> None:
        exp = self._experiment_at_index(index)
        if exp:
            exp.name = new_name

    def model_on_experiment(self, experiment_index: int = -1) -> dict:
        if experiment_index == -1:
            experiment_index = self._project_lib._current_experiment_index
        exp = self._experiment_at_index(experiment_index)
        if exp:
            return exp.model
        return {}

    def model_index_on_experiment(self) -> int:
        model = self.model_on_experiment()
        if model:
            return self._project_lib._models.index(model)
        return -1

    def set_model_on_experiment(self, new_value: int) -> None:
        exp = self._experiment_at_index(self._project_lib._current_experiment_index)
        models = self._project_lib._models
        if exp and models:
            try:
                model = models[new_value]
                exp.model = model
                # self._project_lib.current_model_index = new_value
            except IndexError:
                print(f'Model index {new_value} is out of range for the current experiment.')
        else:
            print('No experiment or models available to set on the experiment.')
        pass

    def remove_experiment(self, index: int) -> None:
        """
        Remove the experiment at the given index.
        """
        total = len(self.available())
        if not (0 <= index < total):
            print(f'Experiment index {index} is out of range.')
            return

        experiments = self._project_lib._experiments
        exp_key = self._experiment_key_at_index(index)
        if exp_key is None:
            print(f'Experiment index {index} is out of range.')
            return

        if hasattr(experiments, 'items'):
            del experiments[exp_key]
        else:
            experiments.pop(index)

        current = self._project_lib._current_experiment_index
        new_total = max(0, total - 1)
        if new_total == 0:
            self._project_lib._current_experiment_index = 0
        elif current > index:
            self._project_lib._current_experiment_index = current - 1
        elif current >= new_total:
            self._project_lib._current_experiment_index = new_total - 1
