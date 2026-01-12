from easyreflectometry import Project as ProjectLib
from easyscience.fitting import FitResults


class Fitting:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._running = False
        self._finished = True
        self._result: FitResults = None

    @property
    def status(self) -> str:
        if self._result is None:
            return False
        else:
            return self._result.success

    @property
    def running(self) -> bool:
        return self._running

    @property
    def fit_finished(self) -> bool:
        return self._finished

    def start_stop(self) -> None:
        if self._running:
            # Stop running the fitting
            self._running = False
        else:
            # Start running the fitting
            self._running = True
            self._finished = False
            exp_data = self._project_lib.experimental_data_for_model_at_index(0)
            self._result = self._project_lib.fitter.fit_single_data_set_1d(exp_data)
            self._running = False
            self._finished = True
