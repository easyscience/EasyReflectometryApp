from easyreflectometry import Project as ProjectLib
from easyscience import AvailableMinimizers


class Minimizers:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._minimizer_current_index = 0
        self._cached_tolerance = None
        self._cached_max_iterations = None
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

    def selected_minimizer_enum(self):
        """Return the AvailableMinimizers enum for the currently selected minimizer."""
        if 0 <= self._minimizer_current_index < len(self._list_available_minimizers):
            return self._list_available_minimizers[self._minimizer_current_index]
        return None

    def set_minimizer_current_index(self, new_value: int) -> bool:
        if new_value != self._minimizer_current_index:
            self._minimizer_current_index = new_value
            enum_new_minimizer = self._list_available_minimizers[new_value]
            self._project_lib.minimizer = enum_new_minimizer
            self._apply_cached_values()
            return True
        return False

    @property
    def _multi_fitter(self):
        """Get the multi fitter, or None if not available."""
        fitter = self._project_lib.fitter
        if fitter is None:
            return None
        return fitter.easy_science_multi_fitter

    def _apply_cached_values(self):
        """Apply any cached tolerance/max_iterations to the fitter."""
        mf = self._multi_fitter
        if mf is None:
            return
        if self._cached_tolerance is not None:
            mf.tolerance = self._cached_tolerance
        if self._cached_max_iterations is not None:
            mf.max_evaluations = self._cached_max_iterations

    @property
    def tolerance(self) -> float:
        if self._cached_tolerance is not None:
            return self._cached_tolerance
        mf = self._multi_fitter
        if mf is not None and mf.tolerance is not None:
            return mf.tolerance
        return 1e-6  # Default tolerance

    @property
    def max_iterations(self) -> int:
        if self._cached_max_iterations is not None:
            return self._cached_max_iterations
        mf = self._multi_fitter
        if mf is not None and mf.max_evaluations is not None:
            return mf.max_evaluations
        return 5000  # Default max iterations

    def set_tolerance(self, new_value: float) -> bool:
        self._cached_tolerance = new_value
        mf = self._multi_fitter
        if mf is not None:
            mf.tolerance = new_value
        return True

    def set_max_iterations(self, new_value: float) -> bool:
        self._cached_max_iterations = int(new_value)
        mf = self._multi_fitter
        if mf is not None:
            mf.max_evaluations = int(new_value)
        return True
