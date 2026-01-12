from typing import Optional

from easyreflectometry import Project as ProjectLib
from easyscience.fitting import FitResults


class Fitting:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._running = False
        self._finished = True
        self._result: Optional[FitResults] = None
        self._show_results_dialog = False

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

    @property
    def show_results_dialog(self) -> bool:
        return self._show_results_dialog

    @show_results_dialog.setter
    def show_results_dialog(self, value: bool) -> None:
        self._show_results_dialog = value

    @property
    def fit_success(self) -> bool:
        if self._result is None:
            return False
        return self._result.success

    @property
    def fit_n_pars(self) -> int:
        if self._result is None:
            return 0
        return self._result.n_pars

    @property
    def fit_chi2(self) -> float:
        if self._result is None:
            return 0.0
        try:
            return float(self._result.chi2)
        except (ValueError, TypeError):
            return 0.0

    def start_stop(self) -> None:
        if self._running:
            # Stop running the fitting
            self._running = False
        else:
            # Start running the fitting
            self._running = True
            self._finished = False
            self._show_results_dialog = False
            exp_data = self._project_lib.experimental_data_for_model_at_index(0)
            self._result = self._project_lib.fitter.fit_single_data_set_1d(exp_data)
            self._running = False
            self._finished = True
            self._show_results_dialog = True
