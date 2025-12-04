from easyreflectometry import Project as ProjectLib
from easyscience import AvailableMinimizers


class Minimizers:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._minimizer_current_index = 0
        self._list_available_minimizers = list(AvailableMinimizers)
        try:
            self._list_available_minimizers.remove(AvailableMinimizers.LMFit)
        except ValueError:
            pass
        try:
            self._list_available_minimizers.remove(AvailableMinimizers.Bumps)
        except ValueError:
            pass
        try:
            self._list_available_minimizers.remove(AvailableMinimizers.DFO)
        except ValueError:
            pass

    def minimizers_available(self) -> list[str]:
        return [minimizer.name for minimizer in self._list_available_minimizers]

    def minimizer_current_index(self) -> int:
        return self._minimizer_current_index

    def set_minimizer_current_index(self, new_value: int) -> bool:
        if new_value != self._minimizer_current_index:
            self._minimizer_current_index = new_value
            if self._project_lib._fitter is not None:
                enum_new_minimizer = self._list_available_minimizers[new_value]
                self._project_lib._fitter.switch_minimizer(enum_new_minimizer)
            return True
        return False

    @property
    def _multi_fitter(self):
        """Get the multi fitter, or None if not available."""
        if self._project_lib._fitter is None:
            return None
        return self._project_lib._fitter.easy_science_multi_fitter

    @property
    def tolerance(self) -> float:
        if self._multi_fitter is None:
            return 1e-6  # Default tolerance
        return self._multi_fitter.tolerance

    @property
    def max_iterations(self) -> int:
        if self._multi_fitter is None:
            return 100  # Default max iterations
        return self._multi_fitter.max_evaluations

    def set_tolerance(self, new_value: float) -> bool:
        if self._multi_fitter is None:
            return False
        if new_value != self._multi_fitter.tolerance:
            self._multi_fitter.tolerance = new_value
            print(new_value)
            return True
        return False

    def set_max_iterations(self, new_value: float) -> bool:
        if self._multi_fitter is None:
            return False
        if new_value != self._multi_fitter.max_evaluations:
            self._multi_fitter.max_evaluations = new_value
            print(new_value)
            return True
        return False
