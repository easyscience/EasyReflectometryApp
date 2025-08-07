from easyreflectometry import Project as ProjectLib


class Experiments:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._current_index = 0

    def available(self) -> list[str]:
        experiments_name = []
        try:
            # get .name from self._project_lib._experiments and append to experiments_name
            for ind in self._project_lib._experiments.keys():
                exp = self._project_lib._experiments[ind]
                experiments_name.append(exp.name)
            #experiments_name.append(self._project_lib.experimental_data_for_model_at_index().name)
        except IndexError:
            pass
        return experiments_name

    def current_index(self) -> int:
        return self._current_index

    def set_current_index(self, new_value: int) -> None:
        if new_value != self._current_index:
            new_value = self._current_index
            print(new_value)
            return True
        return False

    def set_model_on_experiment(self, new_value: int) -> None:
        exp = self._project_lib._experiments.get(self._current_index)
        models = self._project_lib._models
        if exp and models:
            try:
                model = models[new_value]
                exp.model = model
            except IndexError:
                print(f"Model index {new_value} is out of range for the current experiment.")
        else:
            print("No experiment or models available to set on the experiment.")
        # self._project_lib.set_model_on_experiment(new_value)
