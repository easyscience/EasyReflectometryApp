import copy
from typing import Any

from easyreflectometry import Project as ProjectLib
from easyreflectometry.fit_settings import OBJECTIVES
from easyreflectometry.fit_settings import FitSettings
from easyreflectometry.fit_settings import option_schema
from easyreflectometry.fit_settings import requires_finite_bounds
from easyscience import AvailableMinimizers

BAYESIAN_LABEL = 'BUMPS-DREAM (Bayesian)'
#: The minimizer the app gives a new project (#319: a classical default, and
#: BUMPS is the engine that honours inequality constraints). The library's
#: own default stays LMFit for notebooks; a loaded project keeps its own.
APP_DEFAULT_MINIMIZER = AvailableMinimizers.Bumps_simplex


def apply_app_defaults(project_lib: ProjectLib) -> None:
    """Give a new or reset project the app's minimizer."""
    project_lib.fit_settings.minimizer = APP_DEFAULT_MINIMIZER
    project_lib.fit_settings.mode = 'minimize'


class Minimizers:
    """The GUI view of ``project_lib.fit_settings``; it stores no state of its own."""

    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        # Aliases of a listed member (same engine and method) are not offered.
        aliases = [AvailableMinimizers.__members__.get(name) for name in ('LMFit', 'Bumps', 'DFO')]
        # Index 0 is the Bayesian sentinel (None), which requires an explicit user choice.
        self._list_available_minimizers = [None] + [m for m in AvailableMinimizers if not any(m is alias for alias in aliases)]

    @property
    def _settings(self) -> FitSettings:
        # Read each time: a reset or a load replaces the project's settings object.
        return self._project_lib.fit_settings

    def minimizers_available(self) -> list[str]:
        return [BAYESIAN_LABEL if m is None else m.name for m in self._list_available_minimizers]

    def minimizer_current_index(self) -> int:
        if self._settings.mode == 'sample':
            return 0
        selected = self._settings.minimizer
        for index, entry in enumerate(self._list_available_minimizers):
            if entry is selected:
                return index
        # An alias set directly on the project: the listed member with the same engine and method.
        for index, entry in enumerate(self._list_available_minimizers):
            if entry is not None and (entry.package, entry.method) == (selected.package, selected.method):
                return index
        return 1

    def is_bayesian_selected(self) -> bool:
        return self._settings.mode == 'sample'

    def _selected_package(self) -> str:
        return getattr(self.selected_minimizer_enum(), 'package', '')

    def supports_inequalities(self) -> bool:
        """Whether the engine that will actually run the fit can enforce inequality constraints.

        Inequalities are BUMPS penalties: every ``Bumps*`` method and the DREAM
        sampler (the Bayesian sentinel resolves to ``Bumps_simplex``) qualify;
        LMFit and DFO-LS do not.
        """
        if self.is_bayesian_selected():
            return True
        return self._selected_package() == 'bumps'

    def enforces_inequalities_weakly(self) -> bool:
        """``Bumps_lm`` spreads the penalty over the residuals instead of skipping the model."""
        if self.is_bayesian_selected():
            return False
        return self._selected_package() == 'bumps' and getattr(self.selected_minimizer_enum(), 'method', '') == 'lm'

    def selected_minimizer_enum(self):
        """The ``AvailableMinimizers`` member that will run (``Bumps_simplex`` when sampling)."""
        return self._settings.minimizer

    def requires_finite_bounds(self) -> bool:
        return not self.is_bayesian_selected() and requires_finite_bounds(self._settings.minimizer)

    def set_minimizer_current_index(self, new_value: int) -> bool:
        if not 0 <= new_value < len(self._list_available_minimizers) or new_value == self.minimizer_current_index():
            return False
        entry = self._list_available_minimizers[new_value]
        if entry is None:
            # Bayesian mode: the sampler needs a BUMPS engine.
            self._settings.minimizer = AvailableMinimizers.Bumps_simplex
            self._settings.mode = 'sample'
        else:
            self._settings.minimizer = entry
            self._settings.mode = 'minimize'
        return True

    def settings_error(self) -> str | None:
        """Why the settings would refuse a fit, or None.

        A switch is never refused, but the tolerance it keeps, or the options
        stored for the new minimizer, may not suit it (DFO-LS caps the
        tolerance at 0.1 and needs ``rhobeg`` above it).
        """
        try:
            self._settings.validate()
        except ValueError as error:
            return str(error)
        return None

    # Generic settings: None means "engine default".

    @property
    def tolerance(self) -> float | None:
        return self._settings.tolerance

    @property
    def max_iterations(self) -> int | None:
        return self._settings.max_evaluations

    def set_tolerance(self, new_value: float | None) -> bool:
        """Set (None: reset) the tolerance. Raises ValueError, changing nothing, if it is invalid."""
        return self._set('tolerance', new_value)

    def set_max_iterations(self, new_value: int | None) -> bool:
        """Set (None: reset) the budget. Raises ValueError, changing nothing, if it is invalid."""
        if isinstance(new_value, float) and new_value.is_integer():
            new_value = int(new_value)
        return self._set('max_evaluations', new_value)

    @property
    def objective(self) -> str:
        return self._settings.objective

    @property
    def objectives(self) -> list[str]:
        return list(OBJECTIVES)

    def set_objective(self, new_value: str) -> bool:
        return self._set('objective', new_value)

    def _set(self, field: str, new_value: Any) -> bool:
        old_value = getattr(self._settings, field)
        if new_value == old_value:
            return False
        setattr(self._settings, field, new_value)
        try:
            self._settings.validate()
        except ValueError:
            setattr(self._settings, field, old_value)
            raise
        return True

    # Method-specific options of the selected minimizer.

    def options(self) -> list[dict]:
        """One entry per option the selected minimizer declares (none when sampling)."""
        if self.is_bayesian_selected():
            return []
        values = self._settings.active_options()
        return [
            {
                'name': option.name,
                'kind': option.kind,
                'doc': option.doc,
                'choices': list(option.choices),
                'isSet': option.name in values,
                'value': values.get(option.name, ''),
            }
            for option in option_schema(self._settings.minimizer)
        ]

    def set_option(self, name: str, value: Any) -> bool:
        """Set (None: clear) an option. Raises ValueError, changing nothing, if it is invalid.

        Validated with the whole settings, as :meth:`_set` does: an option can
        conflict with another field (DFO-LS ``rhobeg`` must exceed the
        tolerance), and ``FitSettings.set_option`` checks the option alone.
        """
        if self._settings.active_options().get(name) == value:
            return False
        old_options = copy.deepcopy(self._settings.engine_options)
        self._settings.set_option(name, value)
        try:
            self._settings.validate()
        except ValueError:
            self._settings.engine_options = old_options
            raise
        return True
