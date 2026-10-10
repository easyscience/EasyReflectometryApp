import copy
import logging
import warnings
from typing import TYPE_CHECKING
from typing import List
from typing import Optional
from typing import cast

from easyreflectometry import Project as ProjectLib
from easyscience.fitting import FitResults

if TYPE_CHECKING:
    import scipp as sc
    from easyreflectometry.fitting import PreparedFit

    from .minimizers import Minimizers


logger = logging.getLogger(__name__)


class Fitting:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._running = False
        self._finished = True
        self._result: Optional[FitResults] = None
        self._results: List[FitResults] = []  # For multi-experiment fits
        self._show_results_dialog = False
        self._fit_error_message: Optional[str] = None
        self._fit_cancelled = False
        self._stop_requested = False
        self._fit_iteration = 0
        self._fit_interim_chi2 = 0.0
        self._fit_interim_reduced_chi2 = 0.0
        self._fit_infeasible = False
        self._fit_running_message = ''
        self._fit_preview_parameter_values: dict = {}
        self._fit_has_preview_update = False
        self._fit_has_interim_update = False
        self._sample_step = 0
        self._sample_total_steps = 0
        self._sample_running_message = ''
        self._sample_has_update = False
        # The run the worker executes, kept for its measured arrays at completion.
        self._prepared: 'PreparedFit | None' = None
        self._fit_notes: list[str] = []

    @property
    def status(self) -> str:
        if self._result is None:
            return ''
        else:
            return str(self._result.success)

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
        """Return True if all fits succeeded."""
        if self._results:
            return all(r.success for r in self._results)
        if self._result is None:
            return False
        return self._result.success

    @property
    def fit_error_message(self) -> str:
        return self._fit_error_message or ''

    @property
    def fit_cancelled(self) -> bool:
        """Return True if fit was cancelled by user."""
        return self._fit_cancelled

    @property
    def fit_iteration(self) -> int:
        return self._fit_iteration

    @property
    def fit_interim_chi2(self) -> float:
        return self._fit_interim_chi2

    @property
    def fit_interim_reduced_chi2(self) -> float:
        return self._fit_interim_reduced_chi2

    @property
    def fit_infeasible(self) -> bool:
        """True while the optimizer sits on the BUMPS inequality-penalty plateau."""
        return self._fit_infeasible

    @property
    def fit_progress_message(self) -> str:
        return self._fit_running_message

    @property
    def fit_preview_parameter_values(self) -> dict:
        return dict(self._fit_preview_parameter_values)

    @property
    def fit_has_preview_update(self) -> bool:
        return self._fit_has_preview_update

    @property
    def fit_has_interim_update(self) -> bool:
        return self._fit_has_interim_update

    # ------------------------------------------------------------------
    # Bayesian sampling progress
    # ------------------------------------------------------------------

    @property
    def sample_step(self) -> int:
        return self._sample_step

    @property
    def sample_progress_message(self) -> str:
        return self._sample_running_message

    @property
    def sample_has_update(self) -> bool:
        return self._sample_has_update

    @property
    def sample_total_steps(self) -> int:
        return self._sample_total_steps

    # ------------------------------------------------------------------
    # Progress handling
    # ------------------------------------------------------------------

    def on_fit_progress(self, payload: dict) -> None:
        """Update transient state from an in-flight fit progress payload."""
        self._fit_iteration = int(payload.get('iteration', 0) or 0)
        self._fit_interim_chi2 = float(payload.get('chi2', 0.0) or 0.0)
        self._fit_interim_reduced_chi2 = float(
            payload.get('reduced_chi2', self._fit_interim_chi2) or self._fit_interim_chi2
        )
        self._fit_preview_parameter_values = dict(payload.get('parameter_values', {}) or {})
        self._fit_has_preview_update = bool(payload.get('refresh_plots', False))
        self._fit_has_interim_update = True
        # While an inequality constraint is violated BUMPS skips the model and
        # reports the 1e12 penalty as chi2 — meaningless, so don't show it.
        self._fit_infeasible = bool(payload.get('infeasible', False))

        if self._fit_infeasible:
            self._fit_running_message = (
                f'Fitting... iter {self._fit_iteration}, outside the inequality constraints'
            )
        elif self._fit_iteration > 0:
            self._fit_running_message = (
                f'Fitting... iter {self._fit_iteration}, Chi2 = {self._fit_interim_chi2:.6g}'
            )
        else:
            self._fit_running_message = 'Fitting...'

    def clear_fit_progress(self) -> None:
        self._fit_iteration = 0
        self._fit_interim_chi2 = 0.0
        self._fit_interim_reduced_chi2 = 0.0
        self._fit_infeasible = False
        self._fit_running_message = ''
        self._fit_preview_parameter_values = {}
        self._fit_has_preview_update = False
        self._fit_has_interim_update = False
        self.clear_sample_progress()

    def on_fit_failed(self, error_message: str) -> None:
        """Handle fitting failure callback.

        :param error_message: The error message describing the failure.
        """
        self._result = None
        self._results = []
        self._fit_error_message = error_message
        self._running = False
        self._finished = True
        self._show_results_dialog = True
        self.clear_fit_progress()

    def stop_fit(self) -> None:
        """Request the running fit/sampling to stop.

        Only the stop/cancel flags are set here. The lifecycle state (running,
        finished, results, dialog) is finalised by ``on_fit_failed`` when the
        worker thread actually exits. Keeping ``running`` True until then keeps
        the UI locked, so a second fit cannot be started while a non-abortable
        minimizer (lmfit, DFO) is still mutating the shared parameters.
        """
        self._stop_requested = True
        self._fit_cancelled = True

    def reset_stop_flag(self) -> None:
        """Reset the stop request flag before starting a new fit."""
        self._stop_requested = False
        self._fit_cancelled = False

    def prepare_for_threaded_fit(self) -> None:
        """Prepare state for a new threaded fit.

        This method sets the internal state flags to indicate a fit is starting.
        Call this before launching the background thread.
        """
        self._running = True
        self._finished = False
        self._show_results_dialog = False
        self._fit_error_message = None
        self._result = None
        self._results = []
        self.clear_fit_progress()
        self._fit_running_message = 'Fitting...'

    def _ordered_experiments(self) -> list:
        """Return experiments as an ordered list of experiment objects.

        Handles mapping-like storage without assuming contiguous integer keys.
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
            return [experiment for _, experiment in items]

        return list(experiments)

    _POLARIZED_SAMPLE_MESSAGE = (
        'Bayesian sampling of polarized experiments is not supported yet.'
    )

    def _has_polarized_experiments(self) -> bool:
        """Whether any loaded experiment carries per-channel (polarized) data."""
        return any(
            getattr(experiment, 'available_channels', None) is not None for experiment in self._ordered_experiments()
        )

    # ------------------------------------------------------------------
    # Inequality constraints (BUMPS penalties)
    # ------------------------------------------------------------------

    def inequality_constraints_error(self, minimizers_logic: 'Minimizers') -> str | None:
        """Reason a fit must not start because of the project's inequality constraints.

        Returns ``None`` when the fit may proceed: no enabled inequality, or the
        selected engine enforces them and the current parameter values satisfy
        them (a fit started from an infeasible point would begin on the BUMPS
        penalty plateau where only the penalty slope guides the optimizer).
        """
        active = [spec for spec in self._project_lib.inequality_constraints if spec.enabled]
        if not active:
            return None
        if not minimizers_logic.supports_inequalities():
            return (
                'Inequality constraints are only supported by the BUMPS minimizers (and Bayesian sampling). '
                'Switch the minimizer or remove the inequality constraints.'
            )
        violated = self._project_lib.violated_inequality_constraints()
        if violated:
            names = ', '.join(spec.name or str(spec) for spec in violated)
            return (
                f'The current parameter values violate the inequality constraint(s): {names}. '
                'Adjust the values so every constraint holds before fitting.'
            )
        return None

    def inequality_constraints_warning(self, minimizers_logic: 'Minimizers') -> str:
        """Non-blocking notice about how inequalities will be enforced."""
        active = [spec for spec in self._project_lib.inequality_constraints if spec.enabled]
        if not active:
            return ''
        if not minimizers_logic.supports_inequalities():
            return 'Inequality constraints are not enforced by the selected minimizer; fits are refused.'
        if minimizers_logic.enforces_inequalities_weakly():
            return (
                'Bumps_lm enforces inequality constraints only weakly (the penalty is spread over the residuals); '
                'prefer Bumps (amoeba) or Bumps_newton.'
            )
        return ''

    def snapshot_constraints_factory(self):
        """Build the BUMPS ``constraints_factory`` from the enabled inequality constraints *now*.

        Taken when the fit worker starts so that constraints edited while the
        fit runs cannot change what the worker enforces. Returns ``None`` when
        no inequality constraint is enabled.
        """
        return self._project_lib.build_constraints_factory()

    def prepare_threaded_fit(self, minimizers_logic: 'Minimizers') -> 'PreparedFit | None':
        """Prepare a fit of the included experiments for a worker thread.

        The library prepares the run from a snapshot of the project's fit
        settings: minimizer, tolerance, budget, zero-variance objective and
        method options, each dataset smeared with its own resolution. Its
        warnings (masked points, a parameter starting on a bound, ...) are
        logged and shown with the results.

        :param minimizers_logic: The minimizers logic instance.
        :return: The prepared run, or None when the fit cannot start (the reason is set).
        """
        self._prepared = None
        self._fit_notes = []
        try:
            experiments = self._ordered_experiments()
            if not experiments:
                self._fail_before_start('No experiments to fit')
                return None

            constraints_error = self.inequality_constraints_error(minimizers_logic)
            if constraints_error:
                logger.warning('Fit refused: %s', constraints_error)
                self._fail_before_start(constraints_error)
                return None
            constraints_warning = self.inequality_constraints_warning(minimizers_logic)
            if constraints_warning:
                logger.warning(constraints_warning)

            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                prepared = self._project_lib.prepare_fit()
            self._fit_notes = list(dict.fromkeys(str(warning.message) for warning in caught))
            self._fit_notes.extend(self._scope_notes(prepared))
            for note in self._fit_notes:
                logger.warning(note)
            logger.info('Fitting: prepared %s with objective %s', prepared.core_fitter.minimizer.name, prepared.objective)
            self._prepared = prepared
            return prepared
        except Exception as e:
            self._fail_before_start(f'Error preparing fit: {e}')
            logger.exception('Error preparing threaded fit')
            return None

    def _scope_notes(self, prepared) -> list[str]:
        """What the fit covers beyond the included experiments' own models."""
        notes = []
        models = self._project_lib.models
        for parameter in getattr(prepared, 'added_roots', []):
            owners = ', '.join(f"'{models[index].name}'" for index in self._project_lib.parameter_models(parameter))
            notes.append(
                f"'{parameter.name}' of {owners} is fitted too: a parameter of a fitted model follows it, "
                'although no experiment of that model is included.'
            )
        excluded = [name for name, included in zip(self._experiment_names(), self._inclusion()) if not included]
        if excluded:
            notes.append(f'Not included in this fit: {", ".join(excluded)}.')
        return notes

    def _experiment_names(self) -> list[str]:
        return [experiment.name for experiment in self._ordered_experiments()]

    def _inclusion(self) -> list[bool]:
        return [experiment.include_in_fit for experiment in self._ordered_experiments()]

    def _fail_before_start(self, message: str) -> None:
        self._fit_error_message = message
        self._running = False
        self._finished = True
        self._show_results_dialog = True

    def record_on_project(self, results: Optional[list], status: str = 'completed') -> None:
        """Record the outcome of the worker's run on the project (``Project.last_fit``),
        which the results dialog and the summary read."""
        if self._prepared is not None:
            self._project_lib.record_fit(self._prepared, results, status)

    @property
    def _run(self):
        return getattr(self._project_lib, 'last_fit', None)

    @property
    def fit_dataset_rows(self) -> list[dict]:
        """Per fitted dataset of the last run: name, points, chi2, chi2 per point, share of the total."""
        run = self._run
        if run is None:
            return []
        rows = []
        for (_, name, channel), entry in zip(run.inputs, run.per_dataset):
            rows.append(
                {
                    'name': name if channel is None else f'{name} ({channel})',
                    'points': entry['objective_n_points'],
                    'chi2': entry['objective_chi2'],
                    'chi2PerPoint': entry['objective_chi2_per_point'],
                    'share': entry['share_of_objective'],
                }
            )
        return rows

    @property
    def fit_notes(self) -> str:
        """Warnings raised while preparing the last fit, one per paragraph."""
        return '\n\n'.join(self._fit_notes)

    @property
    def fit_message(self) -> str:
        """The minimizer's termination message for the last fit."""
        return str(getattr(self._result, 'message', '') or '') if self._result is not None else ''

    @property
    def fit_evaluations(self) -> int:
        value = getattr(self._result, 'n_evaluations', None) if self._result is not None else None
        return int(value) if isinstance(value, (int, float)) else 0

    @property
    def fit_classical_reduced_chi2(self) -> float | None:
        """Pooled reduced chi2 over the measured points with positive variance, when defined."""
        return self._run.pooled.get('classical_reduced_chi2') if self._run is not None else None

    # ------------------------------------------------------------------
    # Bayesian sampling helpers
    # ------------------------------------------------------------------

    def collect_all_experiments_datagroup(self) -> 'sc.DataGroup':
        """Build the scipp DataGroup required by reflectometry-lib ``MultiFitter.mcmc_sample()``.

        Scope decision (see issue #319): Bayesian sampling deliberately runs over
        **all** experiments, mirroring the classical fit path (``prepare_threaded_fit``)
        which also fits every experiment. The experiment selection currently affects
        only plotting, not the fit/sampling scope. If per-selection sampling is ever
        wanted, filter ``self._ordered_experiments()`` here and rename accordingly.

        :return: DataGroup with reflectivity coords and data.
        :rtype: sc.DataGroup
        """
        import numpy as np
        import scipp as sc

        if self._has_polarized_experiments():
            raise ValueError(self._POLARIZED_SAMPLE_MESSAGE)

        experiments = self._ordered_experiments()
        coords = {}
        data = {}
        for i, experiment in enumerate(experiments):
            x_vals = np.asarray(experiment.x, dtype=float)
            y_vals = np.asarray(experiment.y, dtype=float)

            # ye holds variances (σ²), same convention as prepare_threaded_fit.
            # Data files without an uncertainty column yield an empty/absent ye;
            # scipp requires variances to match the values' shape, so fall back
            # to zeros and let mcmc_sample's zero-variance handling report it.
            ye_raw = getattr(experiment, 'ye', None)
            ye_vals = np.asarray(ye_raw, dtype=float) if ye_raw is not None else np.zeros_like(y_vals)
            if ye_vals.shape != y_vals.shape:
                ye_vals = np.zeros_like(y_vals)

            # No variances on the Qz coordinate: mcmc_sample only reads its
            # values, and xe may be empty for 2/3-column data files.
            coords[f'Qz_{i}'] = sc.array(
                dims=[f'Qz_{i}'], values=x_vals, unit=sc.Unit('1/angstrom'),
            )
            data[f'R_{i}'] = sc.array(
                dims=[f'Qz_{i}'], values=y_vals, variances=ye_vals,
            )
        return sc.DataGroup(data=data, coords=coords, attrs={})

    def prepare_threaded_sample(self, minimizers_logic: 'Minimizers') -> tuple:
        """Prepare high-level MultiFitter + DataGroup for Bayesian sampling.

        :param minimizers_logic: The minimizers logic instance.
        :return: Tuple of (multi_fitter, data_group) or (None, None) on error.
        """
        try:
            from easyreflectometry.fitting import MultiFitter

            experiments = self._ordered_experiments()
            if not experiments:
                self._fail_before_start('No experiments to sample')
                return None, None

            constraints_error = self.inequality_constraints_error(minimizers_logic)
            if constraints_error:
                logger.warning('Sampling refused: %s', constraints_error)
                self._fail_before_start(constraints_error)
                return None, None

            models = [experiment.model for experiment in experiments]
            multi_fitter = MultiFitter(*models)
            # Sampled with a snapshot of the project's settings (a BUMPS minimizer
            # in sampling mode, and the zero-variance objective), taken here: the
            # library snapshots them only once the worker runs, and the minimizer
            # controls stay editable meanwhile.
            multi_fitter.settings = copy.deepcopy(self._project_lib.fit_settings)

            data_group = self.collect_all_experiments_datagroup()
            return multi_fitter, data_group
        except Exception as e:
            self._fail_before_start(f'Error preparing sampling: {e}')
            logger.exception('Error preparing threaded sample')
            return None, None

    def prepare_for_threaded_sample(self) -> None:
        """Set running flags and sampling progress message before launching the worker."""
        self.reset_stop_flag()
        self._running = True
        self._finished = False
        self._show_results_dialog = False
        self._fit_error_message = None
        self._result = None
        self._results = []
        self.clear_fit_progress()
        self.clear_sample_progress()
        self._sample_running_message = 'Sampling… (this may take several minutes)'

    def on_sample_finished(self) -> None:
        """Handle successful Bayesian sampling completion without FitResults.

        Clears classical fit result state (which is not applicable to sampling)
        while preserving the shared running / dialog lifecycle.
        """
        self._running = False
        self._finished = True
        self._show_results_dialog = True
        self._fit_error_message = None
        self._result = None
        self._results = []
        self.clear_fit_progress()

    def on_sample_progress(self, payload: dict) -> None:
        """Update transient state from an in-flight DREAM sampling progress payload."""
        self._sample_step = int(payload.get('iteration', 0) or 0)
        self._sample_total_steps = int(payload.get('total_steps', 0) or 0)
        self._sample_has_update = True
        self._fit_has_interim_update = True
        total = self._sample_total_steps
        if self._sample_step > 0:
            if total > 0:
                self._sample_running_message = f'DREAM step {self._sample_step} of {total}'
            else:
                self._sample_running_message = f'DREAM step {self._sample_step}'
        else:
            self._sample_running_message = 'Sampling…'

    def clear_sample_progress(self) -> None:
        self._sample_step = 0
        self._sample_total_steps = 0
        self._sample_running_message = ''
        self._sample_has_update = False

    def on_fit_finished(self, results: FitResults | List[FitResults]) -> None:
        """Handle successful completion of fitting.

        :param results: List of FitResults from the multi-fitter.
        """
        self._running = False
        self._finished = True
        self._show_results_dialog = True
        self._fit_error_message = None
        self.clear_fit_progress()

        # Store result(s) - handle both single and multiple results
        if isinstance(results, list) and len(results) > 0:
            # For multi-experiment fits, store the list; use first for single-result properties
            self._results = results
            self._result = results[0]
            engine_name = getattr(results[0], 'minimizer_engine', 'unknown')
            logger.info('Fit finished: engine=%s, success=%s', engine_name, results[0].success)
        else:
            single_result = cast(Optional[FitResults], results)
            self._result = single_result
            self._results = [single_result] if single_result is not None else []

    @property
    def last_fit_results(self):
        return self._results if self._results else None

    @property
    def fit_n_pars(self) -> int:
        """The number of parameters the last fit varied."""
        return self._run.n_free_parameters if self._run is not None else 0

    @property
    def fit_chi2(self) -> float:
        """The pooled reduced chi-squared of the last fit (0 when undefined)."""
        value = self._run.pooled.get('objective_reduced_chi2') if self._run is not None else None
        return float(value) if value is not None else 0.0

