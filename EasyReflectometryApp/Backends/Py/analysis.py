import logging
import math
import time
from pathlib import Path
from typing import List
from typing import Optional

from easyreflectometry import Project as ProjectLib
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import QUrl
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .logic.bayesian import Bayesian as BayesianLogic
from .logic.calculators import Calculators as CalculatorsLogic
from .logic.experiment_selection import ExperimentSelection
from .logic.experiments import Experiments as ExperimentLogic
from .logic.fitting import Fitting as FittingLogic
from .logic.helpers import get_original_name
from .logic.minimizers import Minimizers as MinimizersLogic
from .logic.parameters import Parameters as ParametersLogic
from .workers import FitterWorker

logger = logging.getLogger(__name__)


def _lacks_finite_bounds(param: dict) -> bool:
    """The library's rule for minimizers that need bounds (differential evolution)."""
    return not (math.isfinite(param['min']) and math.isfinite(param['max']))


class Analysis(QObject):
    minimizerChanged = Signal()
    # The inequality-constraint notices depend on the selected minimizer *and*
    # on which inequality constraints are enabled; this fires for both events
    # (minimizerChanged is forwarded in __init__, the sample backend's
    # constraintsChanged is forwarded by PyBackend). A dedicated signal keeps
    # constraint edits from re-notifying every minimizer-bound property, which
    # would reset e.g. the minimizer combo box model on every layer change.
    inequalityContextChanged = Signal()
    calculatorChanged = Signal()
    # Emitted with the reason when a calculator cannot be selected.
    calculatorChangeRejected = Signal(str)
    experimentsChanged = Signal()
    parametersChanged = Signal()
    parametersIndexChanged = Signal()
    fittingChanged = Signal()
    fitFailed = Signal(str)  # Emitted with error message when fitting fails
    prefitCheckFailed = Signal(str, str)  # Emitted with (title, message) when a fit is refused before starting
    stopFit = Signal()  # Signal to request fitting stop
    # Posterior predictive curves for the charts, as numpy arrays: (q, median, lower, upper) and
    # (z, median, lower, upper). PyBackend connects them to Plotting1d.
    posteriorPredictiveReady = Signal(object, object, object, object)
    posteriorPredictiveSldReady = Signal(object, object, object, object)
    posteriorPredictiveCleared = Signal()

    externalMinimizerChanged = Signal()
    # Tolerance, budget, objective or a method option edited by the user; all
    # are saved with the project.
    externalFitSettingsChanged = Signal()
    externalParametersChanged = Signal()
    externalCalculatorChanged = Signal()
    externalFittingChanged = Signal()
    externalExperimentChanged = Signal()

    def __init__(self, project_lib: ProjectLib, parent=None, selection: ExperimentSelection | None = None):
        super().__init__(parent)
        self._project_lib = project_lib
        self._parameters_logic = ParametersLogic(project_lib)
        self._fitting_logic = FittingLogic(project_lib)
        self._calculators_logic = CalculatorsLogic(project_lib)
        self._experiments_logic = ExperimentLogic(project_lib)
        self._minimizers_logic = MinimizersLogic(project_lib)
        self._bayesian_logic = BayesianLogic()
        self._chached_parameters = None
        self._chached_enabled_parameters = None
        # Thread management for background fitting
        self._fitter_thread = None
        # Connect stopFit signal to slot
        self.stopFit.connect(self._onStopFit)
        # A minimizer switch changes the inequality-constraint notices too.
        self.minimizerChanged.connect(self.inequalityContextChanged)
        # The selected experiments, shared with Plotting1d (PyBackend passes the same instance).
        self._selection = selection if selection is not None else ExperimentSelection()
        self._selection.set_indices([0], len(self._experiments_logic.available()))

    def _ordered_experiments(self) -> list:
        """Return experiments as an ordered list of experiment objects.

        Handles mapping-like storage without assuming contiguous integer keys.
        """
        experiments = self._experiments_logic._project_lib._experiments
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

    ########################
    ## Fitting
    @Property(str, notify=fittingChanged)
    def fittingStatus(self) -> str:
        return self._fitting_logic.status

    @Property(bool, notify=fittingChanged)
    def fittingRunning(self) -> bool:
        return self._fitting_logic.running

    @Property(bool, notify=fittingChanged)
    def isFitFinished(self) -> bool:
        return self._fitting_logic.fit_finished

    @Property(bool, notify=fittingChanged)
    def showFitResultsDialog(self) -> bool:
        return self._fitting_logic.show_results_dialog

    @Slot(bool)
    def setShowFitResultsDialog(self, value: bool) -> None:
        self._fitting_logic.show_results_dialog = value
        self.fittingChanged.emit()

    @Property(bool, notify=fittingChanged)
    def fitSuccess(self) -> bool:
        return self._fitting_logic.fit_success

    @Property(str, notify=fittingChanged)
    def fitErrorMessage(self) -> str:
        return self._fitting_logic.fit_error_message

    @Property(int, notify=fittingChanged)
    def fitNumRefinedParams(self) -> int:
        return self._fitting_logic.fit_n_pars

    @Property(float, notify=fittingChanged)
    def fitChi2(self) -> float:
        return self._fitting_logic.fit_chi2

    @Property(int, notify=fittingChanged)
    def fitIteration(self) -> int:
        return self._fitting_logic.fit_iteration

    @Property(float, notify=fittingChanged)
    def fitInterimChi2(self) -> float:
        return self._fitting_logic.fit_interim_chi2

    @Property(float, notify=fittingChanged)
    def fitInterimReducedChi2(self) -> float:
        return self._fitting_logic.fit_interim_reduced_chi2

    @Property(str, notify=fittingChanged)
    def fitProgressMessage(self) -> str:
        return self._fitting_logic.fit_progress_message

    @Property(bool, notify=fittingChanged)
    def fitHasInterimUpdate(self) -> bool:
        return self._fitting_logic.fit_has_interim_update

    @Property(bool, notify=fittingChanged)
    def fitHasPreviewUpdate(self) -> bool:
        return self._fitting_logic.fit_has_preview_update

    @Property('QVariant', notify=fittingChanged)
    def fitPreviewParameterValues(self) -> dict:
        return self._fitting_logic.fit_preview_parameter_values

    @Property('QVariant', notify=fittingChanged)
    def fitResults(self) -> dict:
        """Return fit results as a dict for QML consumption."""
        return {
            'success': self._fitting_logic.fit_success,
            'nvarys': self._fitting_logic.fit_n_pars,
            'chi2': self._fitting_logic.fit_chi2,
            'classicalChi2': self._fitting_logic.fit_classical_reduced_chi2,
            'evaluations': self._fitting_logic.fit_evaluations,
            'message': self._fitting_logic.fit_message,
            'notes': self._fitting_logic.fit_notes,
        }

    # ------------------------------------------------------------------
    # Bayesian sampling properties
    # ------------------------------------------------------------------

    @Property(bool, notify=minimizerChanged)
    def isBayesianSelected(self) -> bool:
        return self._minimizers_logic.is_bayesian_selected()

    # ------------------------------------------------------------------
    # Inequality constraints (BUMPS-only fit penalties)
    # ------------------------------------------------------------------

    @Property(bool, notify=inequalityContextChanged)
    def minimizerSupportsInequalities(self) -> bool:
        """True when the selected engine (or Bayesian sampling) enforces inequality constraints."""
        return self._minimizers_logic.supports_inequalities()

    @Property(str, notify=inequalityContextChanged)
    def inequalityConstraintsWarning(self) -> str:
        """Notice shown next to the minimizer / constraints when inequalities are active."""
        return self._fitting_logic.inequality_constraints_warning(self._minimizers_logic)

    @Property(bool, notify=fittingChanged)
    def fitInfeasible(self) -> bool:
        """Whether the last progress report came from the BUMPS penalty plateau."""
        return self._fitting_logic.fit_infeasible

    # ------------------------------------------------------------------
    # Bayesian sampling progress properties
    # ------------------------------------------------------------------

    @Property(int, notify=fittingChanged)
    def sampleProgressStep(self) -> int:
        return self._fitting_logic.sample_step

    @Property(str, notify=fittingChanged)
    def sampleProgressMessage(self) -> str:
        return self._fitting_logic.sample_progress_message

    @Property(bool, notify=fittingChanged)
    def sampleProgressHasUpdate(self) -> bool:
        return self._fitting_logic.sample_has_update

    # ------------------------------------------------------------------
    # Bayesian sampling parameter properties
    # ------------------------------------------------------------------

    @Property(int, notify=minimizerChanged)
    def bayesianSamples(self) -> int:
        return self._bayesian_logic.samples

    def _set_bayesian_attr(self, attr: str, value) -> None:
        """Assign a Bayesian hyper-parameter, tolerating invalid input.

        The ``Bayesian`` setters raise ``ValueError`` on invalid values. Letting
        that propagate out of a Qt slot prints a stderr traceback and leaves the
        UI without feedback. Instead we log the rejection and always re-emit
        ``minimizerChanged`` so QML re-reads the property and the input reverts
        to the last valid value.
        """
        try:
            setattr(self._bayesian_logic, attr, value)
        except ValueError as exc:
            logger.warning('Rejected invalid Bayesian %s value %r: %s', attr, value, exc)
        self.minimizerChanged.emit()

    @Slot(int)
    def setBayesianSamples(self, value: int) -> None:
        self._set_bayesian_attr('samples', value)

    @Property(int, notify=minimizerChanged)
    def bayesianBurnIn(self) -> int:
        return self._bayesian_logic.burn

    @Slot(int)
    def setBayesianBurnIn(self, value: int) -> None:
        self._set_bayesian_attr('burn', value)

    @Property(int, notify=minimizerChanged)
    def bayesianPopulation(self) -> int:
        return self._bayesian_logic.population

    @Slot(int)
    def setBayesianPopulation(self, value: int) -> None:
        self._set_bayesian_attr('population', value)

    @Property(int, notify=minimizerChanged)
    def bayesianThinning(self) -> int:
        return self._bayesian_logic.thin

    @Slot(int)
    def setBayesianThinning(self, value: int) -> None:
        self._set_bayesian_attr('thin', value)

    @Property(str, notify=minimizerChanged)
    def bayesianInitializer(self) -> str:
        return self._bayesian_logic.initializer

    @Slot(str)
    def setBayesianInitializer(self, value: str) -> None:
        self._set_bayesian_attr('initializer', value)

    @Property('QVariantList', notify=minimizerChanged)
    def bayesianInitializerOptions(self) -> list:
        return ['eps', 'cov', 'lhs', 'random']

    @Property(bool, notify=fittingChanged)
    def bayesianResultAvailable(self) -> bool:
        return self._bayesian_logic.has_result

    @Property('QVariant', notify=fittingChanged)
    def bayesianPosterior(self) -> dict | None:
        p = self._bayesian_logic.posterior
        if p is None:
            return None
        return {
            'paramNames': self._bayesian_display_name_list(),
            'nDraws': int(p['draws'].shape[0]),
        }

    @Property('QVariant', notify=fittingChanged)
    def bayesianMarginals(self) -> list:
        if not self._bayesian_logic.has_result:
            return []
        import numpy as np

        p = self._bayesian_logic.posterior
        display_names = self._bayesian_display_name_list()
        out = []
        for k, name in enumerate(display_names):
            col = p['draws'][:, k]
            counts, edges = np.histogram(col, bins=40, density=True)
            centers = 0.5 * (edges[:-1] + edges[1:])
            out.append(
                dict(
                    name=name,
                    mean=float(col.mean()),
                    std=float(col.std()),
                    ci_low=float(np.quantile(col, 0.025)),
                    ci_high=float(np.quantile(col, 0.975)),
                    binCenters=centers.tolist(),
                    counts=counts.tolist(),
                )
            )
        return out

    # Phase 2: corner/trace plot PNGs, diagnostics, heatmap

    def _bayesian_display_names(self) -> dict[str, str]:
        """Build mapping from unique_name to human-readable display name.

        Uses the unfiltered parameter list (``all_parameters()``) so that every
        sampled parameter can be resolved, independent of the current table
        filter state.
        """
        mapping: dict[str, str] = {}
        try:
            for p in self._parameters_logic.all_parameters():
                unique = p.get('unique_name', '')
                display = p.get('name', unique)
                if unique:
                    mapping[unique] = display
        except Exception:
            logger.exception('Failed to build Bayesian parameter display-name mapping')
        return mapping

    def _bayesian_display_name_list(self) -> list[str]:
        """Return the posterior parameter names translated to display names."""
        posterior = self._bayesian_logic.posterior
        if posterior is None:
            return []
        mapping = self._bayesian_display_names()
        result: list[str] = []
        for name in posterior['param_names']:
            result.append(mapping.get(name) or name)
        return result

    @Property(str, notify=fittingChanged)
    def bayesianCornerPlotUrl(self) -> str:
        """Return a file URL for the corner plot PNG, or empty string."""
        if not self._bayesian_logic.has_result:
            return ''
        if not self._bayesian_logic.corner_plot_url:
            self._render_corner_plot()
        return self._bayesian_logic.corner_plot_url

    @Property(str, notify=fittingChanged)
    def bayesianTracePlotUrl(self) -> str:
        """Return a file URL for the trace plot PNG, or empty string."""
        if not self._bayesian_logic.has_result:
            return ''
        if not self._bayesian_logic.trace_plot_url:
            self._render_trace_plot()
        return self._bayesian_logic.trace_plot_url

    @Property(str, notify=fittingChanged)
    def bayesianDistributionPlotUrl(self) -> str:
        """Return a file URL for the interactive distribution HTML, or empty string."""
        if not self._bayesian_logic.has_result:
            return ''
        if not self._bayesian_logic.distribution_plot_url:
            self._render_distribution_plot()
        return self._bayesian_logic.distribution_plot_url

    @Property('QVariant', notify=fittingChanged)
    def bayesianDiagnostics(self) -> dict:
        """Return convergence diagnostics dict."""
        if self._bayesian_logic.has_result and not self._bayesian_logic.diagnostics:
            self._compute_diagnostics()
        return self._bayesian_logic.diagnostics

    @Property('QVariantList', notify=fittingChanged)
    def bayesianParamNames(self) -> list:
        """Return parameter names for heatmap axis dropdowns (display names)."""
        return self._bayesian_display_name_list()

    heatmapChanged = Signal()

    @Property('QVariant', notify=heatmapChanged)
    def bayesianHeatmapData(self) -> dict | None:
        """Return 2D histogram data for the heatmap view."""
        return self._bayesian_logic.heatmap_data

    @Property(str, notify=heatmapChanged)
    def bayesianHeatmapPlotUrl(self) -> str:
        """Return a file URL for the rendered 2D heatmap PNG, or empty string."""
        return self._bayesian_logic.heatmap_plot_url

    @Slot(int, int)
    def computeBayesianHeatmap(self, paramX: int, paramY: int) -> None:
        """Compute 2D histogram for the selected parameter pair."""
        import numpy as np

        posterior = self._bayesian_logic.posterior
        if posterior is None:
            return
        draws = np.asarray(posterior['draws'])
        if draws.ndim == 3:
            draws = draws.reshape(-1, draws.shape[-1])
        x = draws[:, paramX]
        y = draws[:, paramY]
        display_names = self._bayesian_display_name_list()
        H, xedges, yedges = np.histogram2d(x, y, bins=50, density=True)
        self._bayesian_logic.heatmap_data = {
            'xLabel': display_names[paramX] if paramX < len(display_names) else posterior['param_names'][paramX],
            'yLabel': display_names[paramY] if paramY < len(display_names) else posterior['param_names'][paramY],
            'xCenters': (0.5 * (xedges[:-1] + xedges[1:])).tolist(),
            'yCenters': (0.5 * (yedges[:-1] + yedges[1:])).tolist(),
            'zValues': H.T.tolist(),
        }
        self._render_heatmap_plot(paramX, paramY)
        self.heatmapChanged.emit()

    # ------------------------------------------------------------------
    # Fitting start / stop (classical + Bayesian dispatch)
    # ------------------------------------------------------------------

    @Slot(None)
    def fittingStartStop(self) -> None:
        # If already running, stop the fit
        if self._fitting_logic.running:
            self.stopFit.emit()
            return

        # Make sure we can run the fitting; QML shows the reason to the user
        errors = self._prefit_errors()
        if errors:
            self.prefitCheckFailed.emit('Invalid Parameter Bounds', '\n\n'.join(errors))
            return

        # Use threaded fitting for non-blocking UI
        self._start_threaded_fit()

    def _start_threaded_fit(self) -> None:
        """Start fitting in a background thread, dispatching to sampling when Bayesian is selected."""
        if self._minimizers_logic.is_bayesian_selected():
            self._start_threaded_sample()
            return

        # Classical fitting path
        # Discard any previous Bayesian posterior so the results dialog and the
        # posterior-predictive chart overlays reflect this fit, not a stale run.
        self._clear_bayesian_results()
        # Reset flags and prepare for fit using proper encapsulation
        self._fitting_logic.reset_stop_flag()
        self._fitting_logic.prepare_for_threaded_fit()
        self.fittingChanged.emit()

        # TODO: Thread-safety: prevent model/parameter edits during fitting or snapshot state before starting the worker.

        # Prepare the run over all experiments, from a snapshot of the fit settings
        prepared = self._fitting_logic.prepare_threaded_fit(self._minimizers_logic)

        if prepared is None:
            # Error already set in fitting logic
            self.fittingChanged.emit()
            if self._fitting_logic.fit_error_message:
                self.fitFailed.emit(self._fitting_logic.fit_error_message)
            return

        # Create and configure worker. The inequality constraints are snapshotted
        # here so edits made while the fit runs cannot change what it enforces.
        self._fitter_thread = FitterWorker(
            fitter=prepared.core_fitter,
            method_name='fit',
            args=(prepared.x, prepared.y),
            kwargs={'weights': prepared.weights, **prepared.call_kwargs(**self._constraints_kwargs())},
            parent=self,
        )
        self._fitter_thread.finished.connect(self._on_fit_finished)
        self._fitter_thread.failed.connect(self._on_fit_failed)
        self._fitter_thread.progressDetail.connect(self._on_fit_progress)
        self._fitter_thread.finished.connect(self._fitter_thread.deleteLater)
        self._fitter_thread.failed.connect(self._fitter_thread.deleteLater)
        self._fitter_thread.start()

    def _constraints_kwargs(self) -> dict:
        """``{'constraints_factory': ...}`` for the worker when inequality constraints are active, else ``{}``.

        The factory is built *now* (a snapshot of the enabled constraints) so
        that edits made while the fit runs cannot change what it enforces.
        """
        factory = self._fitting_logic.snapshot_constraints_factory()
        return {'constraints_factory': factory} if factory is not None else {}

    def _is_stale_worker_signal(self) -> bool:
        """Return True when a worker signal comes from a superseded worker.

        A cancelled fit's thread may outlive the cancellation (lmfit/DFO cannot
        abort mid-run); its late signals must not clobber the state of a newer
        run. Signals from the current worker — and direct calls, where
        ``sender()`` is None — are processed normally.
        """
        sender = self.sender()
        if sender is not None and sender is not self._fitter_thread:
            logger.info('Ignoring signal from a superseded fit worker')
            return True
        return False

    @Slot(dict)
    def _on_fit_progress(self, payload: dict) -> None:
        """Handle in-flight progress payloads emitted from the worker thread."""
        if self._is_stale_worker_signal():
            return
        if payload.get('sampling'):
            self._fitting_logic.on_sample_progress(payload)
        else:
            self._fitting_logic.on_fit_progress(payload)
        self.fittingChanged.emit()

    @Slot(list)
    def _on_fit_finished(self, results: list) -> None:
        """Handle successful completion of threaded fit."""
        if self._is_stale_worker_signal():
            return
        self._fitting_logic.on_fit_finished(results)
        self._project_lib._last_fit_results = self._fitting_logic.last_fit_results
        # The worker executed a prepared run, so the project's fitter (which the
        # HTML summary reads) never saw it: hand it the results and metrics.
        try:
            self._fitting_logic.record_on_project(self._fitting_logic.last_fit_results)
        except Exception:
            logger.exception('Failed to record fit results on project fitter')
        self._fitter_thread = None
        self.fittingChanged.emit()
        self._clearCacheAndEmitParametersChanged()
        self.externalFittingChanged.emit()

    @Slot(str)
    def _on_fit_failed(self, error_message: str) -> None:
        """Handle failed threaded fit."""
        if self._is_stale_worker_signal():
            return
        is_user_cancel = self._fitting_logic.fit_cancelled and 'cancel' in error_message.lower()
        if is_user_cancel:
            error_message = 'Fitting cancelled by user'
        self._fitting_logic.on_fit_failed(error_message)
        self._fitter_thread = None
        self.fittingChanged.emit()
        self._clearCacheAndEmitParametersChanged()
        self.externalFittingChanged.emit()
        if not is_user_cancel:
            self.fitFailed.emit(error_message)

    @Slot()
    def _onStopFit(self) -> None:
        """Stop fitting and clean up."""
        self._fitting_logic.stop_fit()
        if self._fitter_thread is not None:
            self._fitter_thread.stop()
        self.fittingChanged.emit()
        self.externalFittingChanged.emit()

    # ------------------------------------------------------------------
    # Bayesian sampling dispatch and result handling
    # ------------------------------------------------------------------

    def _clear_bayesian_results(self) -> None:
        """Discard the stored posterior, rendered assets and chart overlays.

        Without this, a previous run's posterior keeps the "Bayesian Sampling
        Results" dialog branch, the credible-interval chart overlays and the
        posterior tab alive after the model, minimizer or project has changed.
        """
        had_result = self._bayesian_logic.has_result
        self._bayesian_logic.clear()
        self.posteriorPredictiveCleared.emit()
        if had_result:
            self.fittingChanged.emit()
            self.heatmapChanged.emit()

    @Slot()
    def clearBayesianResults(self) -> None:
        """Public entry point for discarding Bayesian results.

        Connected by PyBackend to project create/load/reset signals so results
        from one project can never be displayed against another.
        """
        self._clear_bayesian_results()

    def _start_threaded_sample(self) -> None:
        """Start Bayesian MCMC sampling in a background thread."""
        # A fresh run invalidates the previous posterior immediately; if the
        # run fails, the UI must not keep presenting the old result as current.
        self._clear_bayesian_results()
        self._fitting_logic.prepare_for_threaded_sample()
        self.fittingChanged.emit()

        multi_fitter, data_group = self._fitting_logic.prepare_threaded_sample(self._minimizers_logic)

        if multi_fitter is None:
            self.fittingChanged.emit()
            if self._fitting_logic.fit_error_message:
                self.fitFailed.emit(self._fitting_logic.fit_error_message)
            return

        logger.info(
            'Bayesian DREAM: samples=%d burn=%d thin=%d population=%d initializer=%s',
            self._bayesian_logic.samples,
            self._bayesian_logic.burn,
            self._bayesian_logic.thin,
            self._bayesian_logic.population,
            self._bayesian_logic.initializer,
        )

        self._fitter_thread = FitterWorker(
            fitter=multi_fitter,  # the high-level reflectometry MultiFitter
            method_name='mcmc_sample',
            args=(data_group,),  # sc.DataGroup
            kwargs={
                'samples': self._bayesian_logic.samples,
                'burn': self._bayesian_logic.burn,
                'thin': self._bayesian_logic.thin,
                'population': self._bayesian_logic.population,
                'initializer': self._bayesian_logic.initializer,
                **self._constraints_kwargs(),
            },
            parent=self,
        )
        self._fitter_thread.finished.connect(self._on_sample_finished)
        self._fitter_thread.failed.connect(self._on_fit_failed)
        self._fitter_thread.progressDetail.connect(self._on_fit_progress)
        self._fitter_thread.finished.connect(self._fitter_thread.deleteLater)
        self._fitter_thread.failed.connect(self._fitter_thread.deleteLater)
        self._fitter_thread.start()

    @Slot(list)
    def _on_sample_finished(self, results: list) -> None:
        """Handle successful completion of Bayesian sampling."""
        if self._is_stale_worker_signal():
            return
        # {'draws', 'param_names', 'internal_bumps_object', 'logp'}
        posterior = results[0] if results else None
        if not isinstance(posterior, dict) or 'draws' not in posterior:
            # A malformed worker result is a failed run, not a finished one with no posterior.
            logger.error('Bayesian sampling returned no usable posterior: %r', results)
            self._on_fit_failed('Bayesian sampling returned no posterior')
            return
        self._bayesian_logic.posterior = posterior
        self._fitting_logic.on_sample_finished()
        self._fitter_thread = None
        # Each post-processing step runs on its own, so one failing does not skip the others.
        for step in (
            self._compute_and_publish_posterior_predictive,
            self._compute_diagnostics,
            self._render_corner_plot,
            self._render_trace_plot,
        ):
            try:
                step()
            except Exception:
                logger.exception('Bayesian post-processing step %s failed', getattr(step, '__name__', step))
        self.fittingChanged.emit()
        self.externalFittingChanged.emit()

    def _compute_and_publish_posterior_predictive(self) -> None:
        """Compute posterior predictive reflectivity and SLD, publish to plotting."""
        import numpy as np
        from easyreflectometry.analysis.bayesian import posterior_predictive_reflectivity
        from easyreflectometry.analysis.bayesian import posterior_predictive_sld_profile

        posterior = self._bayesian_logic.posterior
        if posterior is None:
            logger.warning('_compute_and_publish_posterior_predictive: no posterior available')
            return

        experiments = self._ordered_experiments()
        if not experiments:
            logger.warning('_compute_and_publish_posterior_predictive: no experiments available')
            return

        # Compute posterior predictive reflectivity for all experiments
        q_all = []
        median_all = []
        lo_all = []
        hi_all = []

        total_q_points = sum(len(np.asarray(experiment.x)) for experiment in experiments)
        logger.info(
            '_compute_and_publish_posterior_predictive: draws shape=%s, n_params=%d, '
            'n_experiments=%d, total_q_points=%d',
            posterior['draws'].shape,
            len(posterior['param_names']),
            len(experiments),
            total_q_points,
        )

        try:

            for i, experiment in enumerate(experiments):
                q_i = np.asarray(experiment.x)
                model_i = experiment.model

                median_i, lo_i, hi_i = posterior_predictive_reflectivity(
                    posterior['draws'],
                    posterior['param_names'],
                    model=model_i,
                    q_values=q_i,
                    n_samples=200,
                )
                logger.info(
                    'Posterior predictive for experiment %d: q=%d, median shape=%s',
                    i, len(q_i), median_i.shape,
                )

                q_all.append(q_i)
                median_all.append(median_i)
                lo_all.append(lo_i)
                hi_all.append(hi_i)

            q_concat = np.concatenate(q_all)
            median_concat = np.concatenate(median_all)
            lo_concat = np.concatenate(lo_all)
            hi_concat = np.concatenate(hi_all)
            self.posteriorPredictiveReady.emit(q_concat, median_concat, lo_concat, hi_concat)
        except Exception:
            logger.exception('Failed to compute or publish posterior predictive reflectivity')
            return

        # SLD profile: use the first experiment's model (SLD is shared across experiments)
        try:
            z, sld_median, sld_lo, sld_hi = posterior_predictive_sld_profile(
                posterior['draws'],
                posterior['param_names'],
                model=experiments[0].model,
                n_samples=200,
            )
            self.posteriorPredictiveSldReady.emit(z, sld_median, sld_lo, sld_hi)
        except Exception:
            logger.exception('Failed to compute or publish posterior predictive SLD profile')

    def _compute_diagnostics(self) -> None:
        """Compute convergence diagnostics from the posterior and state."""
        posterior = self._bayesian_logic.posterior
        if posterior is None:
            self._bayesian_logic.diagnostics = {}
            return

        diagnostics = {
            'nDraws': int(posterior['draws'].shape[0]),
            'nParams': int(posterior['draws'].shape[1]),
            'burnIn': self._bayesian_logic.burn,
            'thin': self._bayesian_logic.thin,
            'population': self._bayesian_logic.population,
            'samples': self._bayesian_logic.samples,
        }

        # Extract acceptance rate from BUMPS state if available.
        # The sampler result dict exposes the BUMPS MCMCDraw under
        # 'internal_bumps_object' (easyscience core); fall back to the legacy
        # 'state' key for robustness against future core renames.
        state = posterior.get('internal_bumps_object') or posterior.get('state')
        acceptance_rate = getattr(state, 'acceptance_rate', None)
        if acceptance_rate is not None:
            try:
                if callable(acceptance_rate):
                    import numpy as np

                    # BUMPS MCMCDraw.acceptance_rate() returns (generation ids, rate in percent)
                    # for the kept portion of the run.
                    _generations, rates = acceptance_rate()
                    acceptance_rate = float(np.mean(rates)) / 100.0
                diagnostics['acceptanceRate'] = float(acceptance_rate)
            except (TypeError, ValueError):
                pass

        draws = posterior['draws']

        # Try to obtain 3D draws (chains × draws × params) needed by arviz R-hat.
        # The BUMPS MCMCDraw.chains() returns (n_generations, n_chains, n_params).
        draws_3d = None
        if getattr(draws, 'ndim', 0) == 3 and draws.shape[0] >= 2:
            draws_3d = draws
        elif state is not None and hasattr(state, 'chains'):
            try:
                import numpy as np

                _draw_counts, chains_3d, _logp_3d = state.chains()
                # chains_3d: (n_generations, n_chains, n_params)
                if chains_3d.shape[1] >= 2:  # at least 2 chains
                    # Transpose to arviz convention: (n_chains, n_draws, n_params)
                    draws_3d = np.moveaxis(chains_3d, 0, 1)
                else:
                    diagnostics['rhatStatus'] = 'Unavailable: only one chain was sampled (increase Population).'
            except Exception:
                draws_3d = None

        if draws_3d is not None:
            try:
                import arviz as _arviz

                # Build arviz InferenceData from 3D draws (n_chains, n_draws, n_params)
                import numpy as np

                posterior_dict = {}
                for i, name in enumerate(posterior['param_names']):
                    posterior_dict[name] = draws_3d[:, :, i]
                idata = _arviz.from_dict({'posterior': posterior_dict})
                rhat = _arviz.rhat(idata)
                if rhat is not None:
                    # arviz.rhat returns an xarray Dataset; extract scalar values
                    mapping = self._bayesian_display_names()
                    mapped_rhat = {}
                    for name in posterior['param_names']:
                        val = float(rhat[name].values)
                        display = mapping.get(name, name)
                        mapped_rhat[display] = val
                    finite_rhat = {name: value for name, value in mapped_rhat.items() if np.isfinite(value)}
                    if finite_rhat:
                        diagnostics['rhat'] = finite_rhat
                    else:
                        diagnostics['rhatStatus'] = 'Unavailable: all R-hat values are NaN/Inf.'
                else:
                    diagnostics['rhatStatus'] = 'Unavailable: arviz.rhat returned None.'
            except ImportError:
                diagnostics['rhatStatus'] = 'Unavailable: arviz is not installed.'
            except Exception as exc:
                diagnostics['rhatStatus'] = f'Unavailable: R-hat computation failed ({exc}).'
        else:
            if 'rhatStatus' not in diagnostics:
                diagnostics['rhatStatus'] = 'Unavailable: the sampler returned flattened draws without chain identities.'

        self._bayesian_logic.diagnostics = diagnostics

    @Property(int, notify=fittingChanged)
    def sampleProgressTotalSteps(self) -> int:
        return self._fitting_logic.sample_total_steps

    def _plot_file_path(self, stem: str, ext: str = 'png'):
        """Return a stable temporary file path for a rendered Bayesian plot."""
        import tempfile

        out_dir = Path(tempfile.gettempdir()) / 'EasyReflectometryApp' / 'bayesian'
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / f'{stem}.{ext}'

    def _plot_file_url(self, stem: str) -> str:
        """Return a stable temporary file URL for a rendered Bayesian plot."""
        return self._plot_file_path(stem).as_uri()

    def _render_corner_plot(self) -> None:
        """Render corner plot to interactive HTML and expose it as a file URL."""
        posterior = self._bayesian_logic.posterior
        if posterior is None:
            self._bayesian_logic.corner_plot_url = ''
            return
        try:
            from easyreflectometry.analysis.bayesian import plot_corner

            display_names = self._bayesian_display_name_list()
            import numpy as np
            draws = np.asarray(posterior['draws'])
            if draws.ndim == 3:
                draws = draws.reshape(-1, draws.shape[-1])

            fig = plot_corner(draws, display_names)
            if fig is None:
                self._bayesian_logic.corner_plot_url = ''
                logger.info('Plotly unavailable — corner plot not rendered')
                return

            html = fig.to_html(
                include_plotlyjs=True,
                full_html=True,
                config={'responsive': True},
            )
            path = self._plot_file_path('corner', 'html')
            path.write_text(html, encoding='utf-8')
            self._bayesian_logic.corner_plot_url = path.as_uri() + f'?t={time.time_ns()}'
        except ImportError:
            self._bayesian_logic.corner_plot_url = ''
            logger.info('Plotly not installed — corner plot unavailable')
        except Exception:
            self._bayesian_logic.corner_plot_url = ''
            logger.exception('Failed to render corner plot')

    def _render_distribution_plot(self) -> None:
        """Render marginal distribution plot to interactive HTML and expose it as a file URL."""
        posterior = self._bayesian_logic.posterior
        if posterior is None:
            self._bayesian_logic.distribution_plot_url = ''
            return
        try:
            from easyreflectometry.analysis.bayesian import plot_distribution

            display_names = self._bayesian_display_name_list()
            import numpy as np
            draws = np.asarray(posterior['draws'])
            if draws.ndim == 3:
                draws = draws.reshape(-1, draws.shape[-1])

            fig = plot_distribution(draws, display_names, return_figure=True)
            if fig is None:
                self._bayesian_logic.distribution_plot_url = ''
                logger.info('Plotly unavailable — distribution plot not rendered')
                return

            html = fig.to_html(
                include_plotlyjs=True,
                full_html=True,
                config={'responsive': True},
            )
            path = self._plot_file_path('distribution', 'html')
            path.write_text(html, encoding='utf-8')
            self._bayesian_logic.distribution_plot_url = path.as_uri() + f'?t={time.time_ns()}'
        except ImportError:
            self._bayesian_logic.distribution_plot_url = ''
            logger.info('Plotly not installed — distribution plot unavailable')
        except Exception:
            self._bayesian_logic.distribution_plot_url = ''
            logger.exception('Failed to render distribution plot')

    def _render_trace_plot(self) -> None:
        """Render MCMC trace plot to interactive HTML and expose it as a file URL."""
        posterior = self._bayesian_logic.posterior
        if posterior is None:
            self._bayesian_logic.trace_plot_url = ''
            return
        try:
            import numpy as np
            from easyreflectometry.analysis.bayesian import plot_trace
            draws = np.asarray(posterior['draws'])
            if draws.ndim == 2:
                draws = draws[np.newaxis, ...]  # (1, n_draws, n_params)

            display_names = self._bayesian_display_name_list()

            fig = plot_trace(draws, display_names, return_figure=True)
            if fig is None or not hasattr(fig, 'to_html'):
                self._bayesian_logic.trace_plot_url = ''
                logger.info('Plotly unavailable — trace plot not rendered')
                return

            html = fig.to_html(  # type: ignore[union-attr]
                include_plotlyjs=True,
                full_html=True,
                config={'responsive': True},
            )
            path = self._plot_file_path('trace', 'html')
            path.write_text(html, encoding='utf-8')
            self._bayesian_logic.trace_plot_url = path.as_uri() + f'?t={time.time_ns()}'
        except ImportError:
            self._bayesian_logic.trace_plot_url = ''
            logger.info('Plotly not installed — trace plot unavailable')
        except Exception:
            self._bayesian_logic.trace_plot_url = ''
            logger.exception('Failed to render trace plot')

    def _render_heatmap_plot(self, paramX: int, paramY: int) -> None:
        """Render selected 2D posterior density heatmap to PNG and expose it as a file URL."""
        posterior = self._bayesian_logic.posterior
        if posterior is None:
            self._bayesian_logic.heatmap_plot_url = ''
            return
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np

            draws = np.asarray(posterior['draws'])
            if draws.ndim == 3:
                draws = draws.reshape(-1, draws.shape[-1])

            x = draws[:, paramX]
            y = draws[:, paramY]
            display_names = self._bayesian_display_name_list()
            x_label = display_names[paramX] if paramX < len(display_names) else posterior['param_names'][paramX]
            y_label = display_names[paramY] if paramY < len(display_names) else posterior['param_names'][paramY]

            fig, axis = plt.subplots(figsize=(8, 6))
            heatmap = axis.hist2d(x, y, bins=60, density=True, cmap='viridis')
            fig.colorbar(heatmap[3], ax=axis, label='Posterior density')
            axis.set_xlabel(x_label)
            axis.set_ylabel(y_label)
            axis.set_title(f'Joint posterior: {x_label} vs {y_label}')
            axis.grid(False)
            fig.tight_layout()

            path = self._plot_file_path(f'heatmap_{paramX}_{paramY}')
            fig.savefig(path, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            self._bayesian_logic.heatmap_plot_url = path.as_uri() + f'?t={time.time_ns()}'
        except Exception:
            self._bayesian_logic.heatmap_plot_url = ''
            logger.exception('Failed to render Bayesian heatmap')

    def _prefit_errors(self) -> List[str]:
        """
        Check that the free parameters can be fitted with the current minimizer.
        Returns one message per problem found; an empty list means the fit can start.
        """
        errors = []
        fit_params = self._free_parameters()

        # 1. wrong bounds on parameters
        for param in fit_params:
            if param['min'] >= param['max']:
                errors.append(
                    f"Parameter '{param['name']}' has invalid bounds: "
                    f'min ({param["min"]}) must be less than max ({param["max"]}).'
                )

        # 2. some minimizers (differential evolution) need finite bounds on all parameters
        if self._minimizers_logic.requires_finite_bounds():
            bad_params = [param['name'] for param in fit_params if _lacks_finite_bounds(param)]
            if bad_params:
                joined = '\n' + ',\n'.join(bad_params) + '\n'
                errors.append(
                    f'Parameters {joined} have infinite bounds, which '
                    f'{self._minimizers_logic.selected_minimizer_enum().name} does not allow.'
                )

        return errors

    def _free_parameters(self) -> List[dict]:
        """The parameters a fit varies, each once.

        Read from the unfiltered list: the table's name and free/fixed filters
        must not change what the fit-wide checks see. A parameter shared by
        several models is listed once per model, hence the identity check.
        """
        unique = {}
        for param in self._parameters_logic.all_parameters():
            if param['fit'] and param.get('enabled', True):
                unique.setdefault(id(param['object']), param)
        return list(unique.values())

    ########################
    ## Calculators
    @Property('QVariantList', notify=calculatorChanged)
    def calculatorsAvailable(self) -> List[str]:
        return self._calculators_logic.available()

    @Property(int, notify=calculatorChanged)
    def calculatorCurrentIndex(self) -> int:
        return self._calculators_logic.current_index()

    @Slot(int)
    def setCalculatorCurrentIndex(self, new_value: int) -> None:
        try:
            changed = self._calculators_logic.set_current_index(new_value)
        except NotImplementedError as exception:
            # A calculator that cannot model the sample's magnetism would raise
            # deep inside the library; report it and keep the current engine.
            logger.warning('Cannot change the calculator: %s', exception)
            self.calculatorChangeRejected.emit(str(exception))
            self.calculatorChanged.emit()
            return
        if changed:
            self.calculatorChanged.emit()
            self.externalCalculatorChanged.emit()

    ########################
    ## Experiments
    @Property('QVariantList', notify=experimentsChanged)
    def experimentsAvailable(self) -> List[str]:
        return self._experiments_logic.available()

    @Property('QVariantList', notify=experimentsChanged)
    def experimentsPolarized(self) -> List[bool]:
        """Per-experiment flag: True for polarized (per-channel) experiments."""
        return self._experiments_logic.polarized_flags()

    @Property('QVariantList', notify=experimentsChanged)
    def experimentsChannelCount(self) -> List[int]:
        """Per-experiment number of measured spin channels (0 when unpolarized)."""
        return self._experiments_logic.channel_counts()

    @Property(int, notify=experimentsChanged)
    def experimentCurrentIndex(self) -> int:
        return self._experiments_logic.current_index()

    @Slot(int)
    def setExperimentCurrentIndex(self, new_value: int) -> None:
        if self._experiments_logic.set_current_index(new_value):
            self.experimentsChanged.emit()
            self.externalExperimentChanged.emit()

    @Slot(int)
    def setModelOnExperiment(self, new_value: int) -> None:
        self._experiments_logic.set_model_on_experiment(new_value)
        self.experimentsChanged.emit()
        self.externalExperimentChanged.emit()

    @Slot(str)
    def setExperimentName(self, new_name: str) -> None:
        self._experiments_logic.set_experiment_name(new_name)
        self.experimentsChanged.emit()
        self.externalExperimentChanged.emit()

    @Slot(int, str)
    def setExperimentNameAtIndex(self, index: int, new_name: str) -> None:
        self._experiments_logic.set_experiment_name_at_index(index, new_name)
        self.experimentsChanged.emit()
        self.externalExperimentChanged.emit()

    @Property(int, notify=experimentsChanged)
    def modelIndexForExperiment(self) -> int:
        # return the model index for the current experiment
        models = self._experiments_logic._project_lib._models
        experiments = self._ordered_experiments()
        index = self.experimentCurrentIndex
        current_experiment = experiments[index] if 0 <= index < len(experiments) else None
        if current_experiment is None:
            return -1
        try:
            return models.index(current_experiment.model)
        except ValueError:
            # The experiment is unpaired or paired with a model no longer in the project.
            return -1

    @Property('QVariantList', notify=experimentsChanged)
    def modelNamesForExperiment(self) -> list:
        # return a list of model names for each experiment
        mapped_models = []
        experiments = self._ordered_experiments()
        for experiment in experiments:
            name = get_original_name(experiment.model)
            mapped_models.append(name)
        return mapped_models

    @Property('QVariantList', notify=experimentsChanged)
    def modelColorsForExperiment(self) -> list:
        # return a list of model colors for each experiment
        mapped_models = []
        experiments = self._ordered_experiments()
        for experiment in experiments:
            mapped_models.append(experiment.model.color)
        return mapped_models

    @Slot(int)
    def removeExperiment(self, index: int) -> None:
        """
        Remove the experiment at the given index.
        """
        if 0 <= index < len(self._experiments_logic.available()):
            self._experiments_logic.remove_experiment(index)
            # The selection follows: the removed experiment leaves it, later ones shift down.
            if self._selection.remove_index(index, len(self._experiments_logic.available())):
                self._sync_current_experiment_to_selection()
            self.experimentsChanged.emit()
            self.externalExperimentChanged.emit()
        else:
            logger.warning('Experiment index %s is out of range.', index)

    ########################
    ## Multi-experiment selection support

    @property
    def selection(self) -> ExperimentSelection:
        return self._selection

    @Property(int, notify=experimentsChanged)
    def experimentsSelectedCount(self) -> int:
        """Return the count of currently selected experiments."""
        return len(self._selection.indices)

    @Property('QVariantList', notify=experimentsChanged)
    def selectedExperimentIndices(self) -> List[int]:
        """Return the list of selected experiment indices."""
        return self._selection.indices

    @Slot(int)
    def selectExperimentAtIndex(self, index: int) -> None:
        """Make one experiment the current and only selected one.

        Used after an import so the charts show the experiment that was just
        loaded instead of staying on the previously selected one.
        """
        self.setSelectedExperimentIndices([index])

    @Slot('QVariantList')
    def setSelectedExperimentIndices(self, indices: List[int]) -> None:
        """Set multiple selected experiment indices."""
        if self._selection.set_indices(list(indices), len(self._experiments_logic.available())):
            self._sync_current_experiment_to_selection()
            self.experimentsChanged.emit()
            self.externalExperimentChanged.emit()

    def prune_selected_experiments(self) -> bool:
        """Drop selected experiments that no longer exist, e.g. after a model and its
        experiment were removed. Returns whether the selection changed; the caller notifies."""
        changed = self._selection.prune(len(self._experiments_logic.available()))
        if changed:
            self._sync_current_experiment_to_selection()
        return changed

    def reset_selected_experiments(self) -> bool:
        """Select only the current experiment, after a project was loaded, created or reset.
        Returns whether the selection changed; the caller notifies."""
        return self._selection.reset(self._experiments_logic.current_index(), len(self._experiments_logic.available()))

    def _sync_current_experiment_to_selection(self) -> None:
        """The current experiment is the first selected one."""
        indices = self._selection.indices
        if indices:
            self._experiments_logic.set_current_index(indices[0])
            self._project_lib.current_experiment_index = indices[0]

    ########################
    ## Minimizers
    @Property('QVariantList', notify=minimizerChanged)
    def minimizersAvailable(self) -> List[str]:
        return self._minimizers_logic.minimizers_available()

    @Property(int, notify=minimizerChanged)
    def minimizerCurrentIndex(self) -> int:
        return self._minimizers_logic.minimizer_current_index()

    @Slot(int)
    def setMinimizerCurrentIndex(self, new_value: int) -> None:
        if self._minimizers_logic.set_minimizer_current_index(new_value):
            self.minimizerChanged.emit()
            self.externalMinimizerChanged.emit()
            # The switch stands; a setting that does not suit the new minimizer is
            # reported now rather than when the fit is refused.
            error = self._minimizers_logic.settings_error()
            if error:
                logger.warning('Minimizer settings invalid after switch: %s', error)
                self.prefitCheckFailed.emit(
                    'Invalid Minimizer Setting',
                    f'{self._minimizers_logic.selected_minimizer_enum().name} is selected, but its settings '
                    f'are not valid for it:\n\n{error}\n\nCorrect them before fitting.',
                )

    @Property('QVariant', notify=minimizerChanged)
    def minimizerTolerance(self) -> Optional[float]:
        """The tolerance, or None (QML: undefined) for the engine default."""
        return self._minimizers_logic.tolerance

    @Property('QVariant', notify=minimizerChanged)
    def minimizerMaxIterations(self) -> Optional[int]:
        """The budget, or None (QML: undefined) for the engine default."""
        return self._minimizers_logic.max_iterations

    def _apply_fit_setting(self, setter, *args) -> None:
        """Apply a fit-settings edit; an invalid one is reported and the field reverts."""
        try:
            changed = setter(*args)
        except ValueError as error:
            logger.warning('Rejected fit setting: %s', error)
            self.prefitCheckFailed.emit('Invalid Minimizer Setting', str(error))
            changed = False
        # Always re-read: a rejected or unchanged edit must show the stored value again.
        self.minimizerChanged.emit()
        if changed:
            self.externalFitSettingsChanged.emit()

    @Slot(float)
    def setMinimizerTolerance(self, new_value: float) -> None:
        self._apply_fit_setting(self._minimizers_logic.set_tolerance, new_value)

    @Slot()
    def resetMinimizerTolerance(self) -> None:
        self._apply_fit_setting(self._minimizers_logic.set_tolerance, None)

    @Slot(float)
    def setMinimizerMaxIterations(self, new_value: float) -> None:
        self._apply_fit_setting(self._minimizers_logic.set_max_iterations, new_value)

    @Slot()
    def resetMinimizerMaxIterations(self) -> None:
        self._apply_fit_setting(self._minimizers_logic.set_max_iterations, None)

    @Property('QVariantList', notify=minimizerChanged)
    def fitObjectives(self) -> List[str]:
        return self._minimizers_logic.objectives

    @Property(str, notify=minimizerChanged)
    def fitObjective(self) -> str:
        return self._minimizers_logic.objective

    @Slot(str)
    def setFitObjective(self, new_value: str) -> None:
        self._apply_fit_setting(self._minimizers_logic.set_objective, new_value)

    @Property('QVariantList', notify=minimizerChanged)
    def minimizerOptions(self) -> list:
        """Method-specific options of the selected minimizer, for a generic editor."""
        return self._minimizers_logic.options()

    @Slot(str, str)
    def setMinimizerOption(self, name: str, text: str) -> None:
        """Set an option from its text; empty text clears it (engine default)."""
        self._apply_fit_setting(self._set_option_from_text, name, text)

    def _set_option_from_text(self, name: str, text: str) -> bool:
        kind = next((option['kind'] for option in self._minimizers_logic.options() if option['name'] == name), None)
        text = text.strip()
        if text == '':
            value = None
        elif kind in ('int', 'float'):
            try:
                value = int(text) if kind == 'int' else float(text)
            except ValueError:
                raise ValueError(f'{name} must be a number, got {text!r}.') from None
        else:
            value = text
        return self._minimizers_logic.set_option(name, value)

    @Property(bool, notify=minimizerChanged)
    def minimizerRequiresFiniteBounds(self) -> bool:
        return self._minimizers_logic.requires_finite_bounds()

    @Property(int, notify=parametersChanged)
    def unboundedFreeParametersCount(self) -> int:
        """Free parameters lacking a finite min or max (relevant when the minimizer needs them)."""
        return sum(1 for param in self._free_parameters() if _lacks_finite_bounds(param))

    @Slot()
    def showFreeParameters(self) -> None:
        """Show only the free parameters, e.g. to correct the bounds a fit was refused for."""
        self._parameters_logic.set_name_filter_criteria('')
        self._parameters_logic.set_variability_filter_criteria('free')
        self._clearCacheAndEmitParametersChanged()

    @Slot()
    def onProjectLoaded(self) -> None:
        """A loaded or reset project brings its own fit settings: re-read every bound control."""
        self.minimizerChanged.emit()

    #############
    ## Parameters
    @Property('QVariantList', notify=parametersChanged)
    def fitableParameters(self) -> List[dict[str]]:
        if self._chached_parameters is None:
            self._chached_parameters = self._parameters_logic.parameters
        return self._chached_parameters

    @Property('QVariantList', notify=parametersChanged)
    def enabledParameters(self) -> list[dict[str]]:
        if self._chached_enabled_parameters is not None:
            return self._chached_enabled_parameters
        self._chached_enabled_parameters = self._parameters_logic.parameters
        return self._chached_enabled_parameters

    @Property(str, notify=parametersChanged)
    def nameFilterCriteria(self) -> str:
        return self._parameters_logic.name_filter_criteria

    @Property(str, notify=parametersChanged)
    def variabilityFilterCriteria(self) -> str:
        return self._parameters_logic.variability_filter_criteria

    @Slot(str)
    def setNameFilterCriteria(self, new_value: str) -> None:
        if self._parameters_logic.set_name_filter_criteria(new_value):
            self._clearCacheAndEmitParametersChanged()

    @Slot(str)
    def setVariabilityFilterCriteria(self, new_value: str) -> None:
        if self._parameters_logic.set_variability_filter_criteria(new_value):
            self._clearCacheAndEmitParametersChanged()

    @Property(int, notify=parametersIndexChanged)
    def currentParameterIndex(self) -> int:
        return self._parameters_logic.current_index()

    @Slot(int)
    def setCurrentParameterIndex(self, new_value: int) -> None:
        if self._parameters_logic.set_current_index(new_value):
            self.parametersIndexChanged.emit()

    @Property(int, notify=parametersChanged)
    def freeParametersCount(self) -> int:
        result = self._parameters_logic.count_free_parameters()
        return result

    @Property(int, notify=parametersChanged)
    def fixedParametersCount(self) -> int:
        result = self._parameters_logic.count_fixed_parameters()
        return result

    @Property(int, notify=parametersChanged)
    def modelParametersCount(self) -> int:
        return len(
            [
                parameter
                for parameter in self._parameters_logic.all_parameters()
                if parameter.get('enabled', True) and not self._parameters_logic.is_experiment_parameter(parameter)
            ]
        )

    @Property(int, notify=parametersChanged)
    def experimentParametersCount(self) -> int:
        return len(
            [
                parameter
                for parameter in self._parameters_logic.all_parameters()
                if parameter.get('enabled', True) and self._parameters_logic.is_experiment_parameter(parameter)
            ]
        )

    @Slot(float)
    def setCurrentParameterValue(self, new_value: float) -> None:
        if self._parameters_logic.set_current_parameter_value(new_value):
            self._clearCacheAndEmitParametersChanged()
            self.externalParametersChanged.emit()

    @Slot(float)
    def setCurrentParameterMin(self, new_value: float) -> None:
        if self._parameters_logic.set_current_parameter_min(new_value):
            self._clearCacheAndEmitParametersChanged()

    @Slot(float)
    def setCurrentParameterMax(self, new_value: float) -> None:
        if self._parameters_logic.set_current_parameter_max(new_value):
            self._clearCacheAndEmitParametersChanged()

    @Slot(bool)
    def setCurrentParameterFit(self, new_value: bool) -> None:
        if self._parameters_logic.set_current_parameter_fit(new_value):
            self._clearCacheAndEmitParametersChanged()

    def _clearCacheAndEmitParametersChanged(self):
        self._chached_parameters = None
        self._chached_enabled_parameters = None
        parameters_length = len(self.enabledParameters)
        current_index = self._parameters_logic.current_index()
        if parameters_length == 0 and current_index != 0:
            self._parameters_logic.set_current_index(0)
            self.parametersIndexChanged.emit()
        elif parameters_length > 0 and current_index >= parameters_length:
            self._parameters_logic.set_current_index(parameters_length - 1)
            self.parametersIndexChanged.emit()
        self.parametersChanged.emit()

    # ------------------------------------------------------------------
    # Bayesian plot saving
    # ------------------------------------------------------------------

    @staticmethod
    def _local_path_from_url(url: str) -> Optional[Path]:
        """Return the local path of a ``file://`` URL, ignoring any query string."""
        if not url or not url.startswith('file://'):
            return None
        # Strip query string (e.g. ?t=<timestamp> used for cache-busting)
        # QUrl handles both file:///C:/... (Windows) and file:///tmp/... (POSIX)
        local_file = QUrl(url.split('?')[0]).toLocalFile()
        return Path(local_file) if local_file else None

    @Slot(str, result=str)
    def bayesianPlotSuggestedFileUrl(self, source_url: str) -> str:
        """Suggested ``file://`` URL in the home folder for saving a rendered Bayesian plot."""
        source_path = self._local_path_from_url(source_url)
        suggested = source_path.name if source_path is not None and source_path.name else 'bayesian_plot.png'
        return QUrl.fromLocalFile(str(Path.home() / suggested)).toString()

    @Slot(str, str, result=bool)
    def saveBayesianPlot(self, source_url: str, destination_url: str) -> bool:
        """Copy a rendered Bayesian plot to a destination chosen by the user in QML.

        :param source_url: ``file://`` URL of the rendered plot (e.g. from
            ``bayesianCornerPlotUrl``, ``bayesianTracePlotUrl``,
            ``bayesianHeatmapPlotUrl``).
        :param destination_url: ``file://`` URL to save the plot to.
        :returns: ``True`` if the file was saved successfully.
        """
        import shutil

        source_path = self._local_path_from_url(source_url)
        if source_path is None:
            logger.warning('Invalid Bayesian plot URL for saving: %s', source_url)
            return False

        if not source_path.exists():
            logger.warning('Bayesian plot file not found: %s', source_path)
            return False

        save_path = self._local_path_from_url(destination_url)
        if save_path is None:
            logger.warning('Invalid destination URL for saving Bayesian plot: %s', destination_url)
            return False

        try:
            shutil.copy2(str(source_path), save_path)
            logger.info('Bayesian plot saved to %s', save_path)
            return True
        except OSError:
            logger.exception('Failed to save Bayesian plot to %s', save_path)
            return False