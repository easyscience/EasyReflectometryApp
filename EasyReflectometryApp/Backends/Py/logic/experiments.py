from easyreflectometry import Project as ProjectLib


class Experiments:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib

    def available(self) -> list[str]:
        experiments_name = []
        try:
            # get .name from self._project_lib._experiments and append to experiments_name
            for ind in self._project_lib._experiments.keys():
                exp = self._project_lib._experiments[ind]
                experiments_name.append(exp.name)
        except IndexError:
            pass
        return experiments_name

    def current_index(self) -> int:
        return self._project_lib._current_experiment_index

    def set_current_index(self, new_value: int) -> None:
        if new_value != self._project_lib._current_experiment_index:
            self._project_lib._current_experiment_index = new_value
            return True
        return False

    def model_on_experiment(self, experiment_index: int = -1) -> dict:
        if experiment_index == -1:
            experiment_index = self._project_lib._current_experiment_index
        exp = self._project_lib._experiments.get(experiment_index)
        if exp:
            return exp.model
        return {}

    def model_index_on_experiment(self) -> int:
        model = self.model_on_experiment()
        if model:
            return self._project_lib._models.index(model)
        return -1

    def set_model_on_experiment(self, new_value: int) -> None:
        exp = self._project_lib._experiments.get(self._project_lib._current_experiment_index)
        models = self._project_lib._models
        if exp and models:
            try:
                model = models[new_value]
                exp.model = model
            except IndexError:
                print(f"Model index {new_value} is out of range for the current experiment.")
        else:
            print("No experiment or models available to set on the experiment.")
        pass

    def remove_experiment(self, index: int) -> None:
        """
        Remove the experiment at the given index.
        """
        if 0 <= index < len(self.available()):
            del self._project_lib._experiments[index]
            if self._project_lib._current_experiment_index >= index:
                self._project_lib._current_experiment_index = \
                max(0, self._project_lib._current_experiment_index - 1)
        else:
            print(f"Experiment index {index} is out of range.")
