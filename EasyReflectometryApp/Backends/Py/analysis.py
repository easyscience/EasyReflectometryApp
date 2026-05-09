import logging

from typing import List
from typing import Optional

from easyreflectometry import Project as ProjectLib
from PySide6 import QtWidgets
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .logic.bayesian import Bayesian as BayesianLogic
from .logic.calculators import Calculators as CalculatorsLogic
from .logic.experiments import Experiments as ExperimentLogic
from .logic.fitting import Fitting as FittingLogic
from .logic.helpers import get_original_name
from .logic.minimizers import Minimizers as MinimizersLogic
from .logic.parameters import Parameters as ParametersLogic
from .workers import FitterWorker

logger = logging.getLogger(__name__)


class Analysis(QObject):
    minimizerChanged = Signal()
    calculatorChanged = Signal()
    experimentsChanged = Signal()
    parametersChanged = Signal()
    parametersIndexChanged = Signal()
    fittingChanged = Signal()
    fitFailed = Signal(str)  # Emitted with error message when fitting fails
    stopFit = Signal()  # Signal to request fitting stop

    externalMinimizerChanged = Signal()
    externalParametersChanged = Signal()
    externalCalculatorChanged = Signal()
    externalFittingChanged = Signal()
    externalExperimentChanged = Signal()

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._project_lib = project_lib
        self._parameters_logic = ParametersLogic(project_lib)
        self._fitting_logic = FittingLogic(project_lib)
        self._calculators_logic = CalculatorsLogic(project_lib)
        self._experiments_logic = ExperimentLogic(project_lib)
        self._minimizers_logic = MinimizersLogic(project_lib)
        self._bayesian_logic = BayesianLogic()
        self._plotting = None  # Set by PyBackend after construction
        self._chached_parameters = None
        self._chached_enabled_parameters = None
        # Thread management for background fitting
        self._fitter_thread = None
        # Connect stopFit signal to slot
        self.stopFit.connect(self._onStopFit)
        # Add support for multiple selected experiments - initialize to empty first to avoid binding loops
        self._selected_experiment_indices = []
        # Initialize selected experiments after construction to avoid binding loops
        self._initialize_selected_experiments()

    def _initialize_selected_experiments(self) -> None:
        """Initialize selected experiment indices after object construction to avoid binding loops."""
        available_experiments = self._experiments_logic.available()
        if len(available_experiments) > 0:
            self._selected_experiment_indices = [0]
        else:
            self._selected_experiment_indices = []

    def set_plotting(self, plotting) -> None:
        """Store a reference to the Plotting1d instance for posterior predictive publishing.

        Called by PyBackend after construction.
        """
        self._plotting = plotting

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
        }

    # ------------------------------------------------------------------
    # Bayesian sampling properties
    # ------------------------------------------------------------------

    @Property(bool, notify=minimizerChanged)
    def isBayesianSelected(self) -> bool:
        return self._minimizers_logic.is_bayesian_selected()

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

    @Slot(int)
    def setBayesianSamples(self, value: int) -> None:
        self._bayesian_logic.samples = value
        self.minimizerChanged.emit()

    @Property(int, notify=minimizerChanged)
    def bayesianBurnIn(self) -> int:
        return self._bayesian_logic.burn

    @Slot(int)
    def setBayesianBurnIn(self, value: int) -> None:
        self._bayesian_logic.burn = value
        self.minimizerChanged.emit()

    @Property(int, notify=minimizerChanged)
    def bayesianPopulation(self) -> int:
        return self._bayesian_logic.population

    @Slot(int)
    def setBayesianPopulation(self, value: int) -> None:
        self._bayesian_logic.population = value
        self.minimizerChanged.emit()

    @Property(int, notify=minimizerChanged)
    def bayesianThinning(self) -> int:
        return self._bayesian_logic.thin

    @Slot(int)
    def setBayesianThinning(self, value: int) -> None:
        self._bayesian_logic.thin = value
        self.minimizerChanged.emit()

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

        # Make sure we can run the fitting
        if not self.prefitCheck():
            return

        # Use threaded fitting for non-blocking UI
        self._start_threaded_fit()

    def _start_threaded_fit(self) -> None:
        """Start fitting in a background thread, dispatching to sampling when Bayesian is selected."""
        if self._minimizers_logic.is_bayesian_selected():
            self._start_threaded_sample()
            return

        # Classical fitting path
        # Reset flags and prepare for fit using proper encapsulation
        self._fitting_logic.reset_stop_flag()
        self._fitting_logic.prepare_for_threaded_fit()
        self.fittingChanged.emit()

        # TODO: Thread-safety: prevent model/parameter edits during fitting or snapshot state before starting the worker.

        # Prepare fit data for all experiments
        fitter, x_data, y_data, weights, method = self._fitting_logic.prepare_threaded_fit(self._minimizers_logic)

        if fitter is None:
            # Error already set in fitting logic
            self.fittingChanged.emit()
            if self._fitting_logic.fit_error_message:
                self.fitFailed.emit(self._fitting_logic.fit_error_message)
            return

        # Create and configure worker
        self._fitter_thread = FitterWorker(
            fitter=fitter,
            method_name='fit',
            args=(x_data, y_data),
            kwargs={'weights': weights, 'method': method},
            parent=self,
        )
        self._fitter_thread.setTerminationEnabled(True)
        self._fitter_thread.finished.connect(self._on_fit_finished)
        self._fitter_thread.failed.connect(self._on_fit_failed)
        self._fitter_thread.progressDetail.connect(self._on_fit_progress)
        self._fitter_thread.finished.connect(self._fitter_thread.deleteLater)
        self._fitter_thread.failed.connect(self._fitter_thread.deleteLater)
        self._fitter_thread.start()

    @Slot(dict)
    def _on_fit_progress(self, payload: dict) -> None:
        """Handle in-flight progress payloads emitted from the worker thread."""
        if payload.get('sampling'):
            self._fitting_logic.on_sample_progress(payload)
        else:
            self._fitting_logic.on_fit_progress(payload)
        self.fittingChanged.emit()

    @Slot(list)
    def _on_fit_finished(self, results: list) -> None:
        """Handle successful completion of threaded fit."""
        self._fitting_logic.on_fit_finished(results)
        self._fitter_thread = None
        self.fittingChanged.emit()
        self._clearCacheAndEmitParametersChanged()
        self.externalFittingChanged.emit()

    @Slot(str)
    def _on_fit_failed(self, error_message: str) -> None:
        """Handle failed threaded fit."""
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

    def _start_threaded_sample(self) -> None:
        """Start Bayesian MCMC sampling in a background thread."""
        self._fitting_logic.prepare_for_threaded_sample()
        self.fittingChanged.emit()

        multi_fitter, data_group = self._fitting_logic.prepare_threaded_sample(self._minimizers_logic)

        if multi_fitter is None:
            self.fittingChanged.emit()
            if self._fitting_logic.fit_error_message:
                self.fitFailed.emit(self._fitting_logic.fit_error_message)
            return

        logger.info(
            'Bayesian DREAM: samples=%d burn=%d thin=%d population=%d',
            self._bayesian_logic.samples,
            self._bayesian_logic.burn,
            self._bayesian_logic.thin,
            self._bayesian_logic.population,
        )

        self._fitter_thread = FitterWorker(
            fitter=multi_fitter,  # the high-level reflectometry MultiFitter
            method_name='sample',
            args=(data_group,),  # sc.DataGroup
            kwargs={
                'samples': self._bayesian_logic.samples,
                'burn': self._bayesian_logic.burn,
                'thin': self._bayesian_logic.thin,
                'population': self._bayesian_logic.population,
            },
            parent=self,
        )
        self._fitter_thread.setTerminationEnabled(True)
        self._fitter_thread.finished.connect(self._on_sample_finished)
        self._fitter_thread.failed.connect(self._on_fit_failed)
        self._fitter_thread.progressDetail.connect(self._on_fit_progress)
        self._fitter_thread.finished.connect(self._fitter_thread.deleteLater)
        self._fitter_thread.failed.connect(self._fitter_thread.deleteLater)
        self._fitter_thread.start()

    @Slot(list)
    def _on_sample_finished(self, results: list) -> None:
        """Handle successful completion of Bayesian sampling."""
        posterior = results[0]  # {'draws', 'param_names', 'state', 'logp'}
        self._bayesian_logic._posterior = posterior
        self._fitting_logic.on_sample_finished()
        self._fitter_thread = None
        # Phase 2: compute posterior predictive, diagnostics, and rendered plots
        self._compute_and_publish_posterior_predictive()
        self._compute_diagnostics()
        self._render_corner_plot()
        self._render_trace_plot()
        self.fittingChanged.emit()
        self.externalFittingChanged.emit()

    def _compute_and_publish_posterior_predictive(self) -> None:
        """Compute posterior predictive reflectivity and SLD, publish to plotting."""
        if self._plotting is None:
            return
        from easyreflectometry.analysis.bayesian import (
            posterior_predictive_reflectivity,
            posterior_predictive_sld_profile,
        )

        posterior = self._bayesian_logic.posterior
        if posterior is None:
            return

        experiments = self._ordered_experiments()
        if not experiments:
            return

        # Use the first selected experiment for the overlay
        experiment = experiments[0]
        q = experiment.x
        model = experiment.model

        median, lo, hi = posterior_predictive_reflectivity(
            posterior['draws'],
            posterior['param_names'],
            model=model,
            q_values=q,
            n_samples=200,
        )
        self._plotting.set_posterior_predictive(q, median, lo, hi)

        z, sld_median, sld_lo, sld_hi = posterior_predictive_sld_profile(
            posterior['draws'],
            posterior['param_names'],
            model=model,
            n_samples=200,
        )
        self._plotting.set_posterior_predictive_sld(z, sld_median, sld_lo, sld_hi)

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

        # Extract acceptance rate from BUMPS state if available
        state = posterior.get('state')
        if state is not None:
            try:
                diagnostics['acceptanceRate'] = float(getattr(state, 'acceptance_rate', None) or 0.0)
            except (AttributeError, TypeError, ValueError):
                pass

        draws = posterior['draws']
        if getattr(draws, 'ndim', 0) == 3 and draws.shape[0] >= 2:
            try:
                from easyreflectometry.analysis.bayesian import PosteriorResults

                pr = PosteriorResults(draws, posterior['param_names'])
                rhat = pr.gelman_rubin()
                if rhat is not None:
                    # Translate unique_name keys to display names
                    mapping = self._bayesian_display_names()
                    mapped_rhat = {mapping.get(name) or name: value for name, value in rhat.items()}
                    finite_rhat = {name: value for name, value in mapped_rhat.items() if value == value}
                    if finite_rhat:
                        diagnostics['rhat'] = finite_rhat
                    else:
                        diagnostics['rhatStatus'] = 'Unavailable: R-hat requires at least two finite chains.'
            except ImportError:
                diagnostics['rhatStatus'] = 'Unavailable: arviz is not installed.'
        else:
            diagnostics['rhatStatus'] = 'Unavailable: the sampler returned flattened draws without chain identities.'

        self._bayesian_logic.diagnostics = diagnostics

    @Property(int, notify=fittingChanged)
    def sampleProgressTotalSteps(self) -> int:
        return self._fitting_logic.sample_total_steps

    def _plot_file_path(self, stem: str):
        """Return a stable temporary file path for a rendered Bayesian plot."""
        from pathlib import Path
        import tempfile

        out_dir = Path(tempfile.gettempdir()) / 'EasyReflectometryApp' / 'bayesian'
        out_dir.mkdir(parents=True, exist_ok=True)
        return out_dir / f'{stem}.png'

    def _plot_file_url(self, stem: str) -> str:
        """Return a stable temporary file URL for a rendered Bayesian plot."""
        return self._plot_file_path(stem).as_uri()

    def _render_corner_plot(self) -> None:
        """Render corner plot to PNG and expose it as a file URL."""
        posterior = self._bayesian_logic.posterior
        if posterior is None:
            self._bayesian_logic.corner_plot_url = ''
            return
        try:
            from easyreflectometry.analysis.bayesian import plot_corner
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            display_names = self._bayesian_display_name_list()
            n_params = len(display_names)
            size = max(6, n_params * 1.8)
            plt.figure(figsize=(size, size))
            plot_corner(posterior['draws'], display_names, fig=plt.gcf())
            fig = plt.gcf()
            plt.tight_layout()

            path = self._plot_file_path('corner')
            fig.savefig(path, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            self._bayesian_logic.corner_plot_url = path.as_uri()
        except ImportError:
            self._bayesian_logic.corner_plot_url = ''
            logger.info('corner library not installed — corner plot unavailable')
        except Exception:
            self._bayesian_logic.corner_plot_url = ''
            logger.exception('Failed to render corner plot')

    def _render_trace_plot(self) -> None:
        """Render MCMC trace plot to PNG and expose it as a file URL."""
        posterior = self._bayesian_logic.posterior
        if posterior is None:
            self._bayesian_logic.trace_plot_url = ''
            return
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt

            import numpy as np

            draws = np.asarray(posterior['draws'])
            if draws.ndim == 3:
                chains, n_draws, n_params = draws.shape
            else:
                chains, n_draws, n_params = 1, draws.shape[0], draws.shape[1]
                draws = draws.reshape(1, n_draws, n_params)

            display_names = self._bayesian_display_name_list()
            n_params = len(display_names)
            fig, axes = plt.subplots(n_params, 1, figsize=(10, 2.2 * max(n_params, 1)), squeeze=False)
            x = np.arange(n_draws)
            for index, name in enumerate(display_names):
                axis = axes[index, 0]
                for chain in range(chains):
                    axis.plot(x, draws[chain, :, index], linewidth=0.8, alpha=0.8)
                axis.set_ylabel(name)
                axis.grid(True, alpha=0.25)
            axes[-1, 0].set_xlabel('Draw')
            fig.tight_layout()

            path = self._plot_file_path('trace')
            fig.savefig(path, format='png', dpi=100, bbox_inches='tight')
            plt.close(fig)
            self._bayesian_logic.trace_plot_url = path.as_uri()
        except ImportError:
            self._bayesian_logic.trace_plot_url = ''
            logger.info('arviz library not installed — trace plot unavailable')
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
            self._bayesian_logic.heatmap_plot_url = path.as_uri()
        except Exception:
            self._bayesian_logic.heatmap_plot_url = ''
            logger.exception('Failed to render Bayesian heatmap')

    def prefitCheck(self) -> bool:
        """
        Perform a pre-fit check to ensure that all parameters are set correctly.
        Returns True if the check passes, False otherwise.
        """
        # 1. wrong bounds on parameters
        for param in self.fitableParameters:
            if not param['fit']:
                continue
            if param['min'] >= param['max']:
                QtWidgets.QMessageBox.warning(
                    None,
                    'Invalid Parameter Bounds',
                    f"Parameter '{param['name']}' has invalid bounds: "
                    f'min ({param["min"]}) must be less than max ({param["max"]}).',
                )
                return False

        # 2. differential evolution needs finite bounds on all parameters
        if 'differential_evolution' in self.minimizersAvailable[self.minimizerCurrentIndex]:
            bad_params = []
            for param in self.fitableParameters:
                if not param['fit']:
                    continue
                if param['min'] == float('-inf') or param['max'] == float('inf'):
                    bad_params.append(param['name'])
            if bad_params:
                joined = '\n' + ',\n'.join(bad_params) + '\n'
                # Show a warning in a message box
                QtWidgets.QMessageBox.warning(
                    None,
                    'Invalid Parameter Bounds',
                    f'Parameters {joined} have infinite bounds, which is not allowed for differential evolution minimizer.',
                )

                return False

        return True

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
        if self._calculators_logic.set_current_index(new_value):
            self.calculatorChanged.emit()
            self.externalCalculatorChanged.emit()

    ########################
    ## Experiments
    @Property('QVariantList', notify=experimentsChanged)
    def experimentsAvailable(self) -> List[str]:
        return self._experiments_logic.available()

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
        if current_experiment is not None:
            t = models.index(current_experiment.model)
            return t
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
            self.experimentsChanged.emit()
            self.externalExperimentChanged.emit()
        else:
            print(f'Experiment index {index} is out of range.')

    ########################
    ## Multi-experiment selection support
    # (Initialize selected experiments in the existing __init__ method)

    @Property(int, notify=experimentsChanged)
    def experimentsSelectedCount(self) -> int:
        """Return the count of currently selected experiments."""
        return len(self._selected_experiment_indices)

    @Property('QVariantList', notify=experimentsChanged)
    def selectedExperimentIndices(self) -> List[int]:
        """Return the list of selected experiment indices."""
        return self._selected_experiment_indices

    @Slot('QVariantList')
    def setSelectedExperimentIndices(self, indices: List[int]) -> None:
        """Set multiple selected experiment indices."""
        # Validate indices
        available_count = len(self._experiments_logic.available())
        valid_indices = [i for i in indices if 0 <= i < available_count]

        if valid_indices != self._selected_experiment_indices:
            # previous_selection = self._selected_experiment_indices.copy()
            self._selected_experiment_indices = valid_indices
            # Update current experiment index to first selected (or 0 if no selection)
            if valid_indices:
                self._experiments_logic.set_current_index(valid_indices[0])
                self._project_lib.current_experiment_index = valid_indices[0]
            elif len(self._experiments_logic.available()) > 0:
                # If no selection but experiments available, default to first experiment
                self._experiments_logic.set_current_index(0)
                self._selected_experiment_indices = [0]  # Auto-select first experiment

            # Always trigger plotting refresh when selection changes
            self._refresh_plotting_system()

            self.experimentsChanged.emit()
            self.externalExperimentChanged.emit()

    def get_concatenated_experiment_data(self):
        """
        Concatenate data from all selected experiments.
        Returns a combined DataSet1D object.
        """
        import numpy as np
        from easyreflectometry.data import DataSet1D

        if not self._selected_experiment_indices:
            return DataSet1D(name='No experiments selected', x=np.empty(0), y=np.empty(0), ye=np.empty(0), xe=np.empty(0))

        all_x, all_y, all_ye, all_xe = [], [], [], []

        for exp_idx in self._selected_experiment_indices:
            try:
                data = self._experiments_logic._project_lib.experimental_data_for_model_at_index(exp_idx)
                if data.x.size > 0:  # Only include non-empty datasets
                    all_x.extend(data.x)
                    all_y.extend(data.y)
                    all_ye.extend(data.ye if hasattr(data, 'ye') and data.ye.size > 0 else np.zeros_like(data.y))
                    all_xe.extend(data.xe if hasattr(data, 'xe') and data.xe.size > 0 else np.zeros_like(data.x))
            except (IndexError, AttributeError) as e:
                print(f'Error accessing experiment {exp_idx}: {e}')
                continue

        if not all_x:
            return DataSet1D(name='No valid experiment data', x=np.empty(0), y=np.empty(0), ye=np.empty(0), xe=np.empty(0))

        # Sort by x values to maintain proper order
        combined_data = list(zip(all_x, all_y, all_ye, all_xe))
        combined_data.sort(key=lambda item: item[0])

        x_sorted, y_sorted, ye_sorted, xe_sorted = zip(*combined_data) if combined_data else ([], [], [], [])

        exp_names = [
            self._experiments_logic.available()[i]
            for i in self._selected_experiment_indices
            if i < len(self._experiments_logic.available())
        ]
        combined_name = f'Combined: {", ".join(exp_names)}'

        return DataSet1D(
            name=combined_name, x=np.array(x_sorted), y=np.array(y_sorted), ye=np.array(ye_sorted), xe=np.array(xe_sorted)
        )

    def get_individual_experiment_data_list(self):
        """
        Get individual experiment data for each selected experiment.
        Returns a list of dictionaries with data, name, and color for each experiment.
        """

        if not self._selected_experiment_indices:
            return []

        experiment_data_list = []

        # Define a color palette for experiments
        color_palette = [
            '#1f77b4',  # Blue
            '#ff7f0e',  # Orange
            '#2ca02c',  # Green
            '#d62728',  # Red
            '#9467bd',  # Purple
            '#8c564b',  # Brown
            '#e377c2',  # Pink
            '#7f7f7f',  # Gray
            '#bcbd22',  # Olive
            '#17becf',  # Cyan
        ]

        for idx, exp_idx in enumerate(self._selected_experiment_indices):
            try:
                data = self._experiments_logic._project_lib.experimental_data_for_model_at_index(exp_idx)
                if data.x.size > 0:  # Only include non-empty datasets
                    exp_name = (
                        self._experiments_logic.available()[exp_idx]
                        if exp_idx < len(self._experiments_logic.available())
                        else f'Experiment {exp_idx + 1}'
                    )
                    color = color_palette[exp_idx % len(color_palette)]

                    experiment_data_list.append({'data': data, 'name': exp_name, 'color': color, 'index': exp_idx})
            except (IndexError, AttributeError) as e:
                print(f'Error accessing experiment {exp_idx}: {e}')
                continue

        return experiment_data_list

    @Property('QVariantList', notify=experimentsChanged)
    def selectedExperimentDataList(self) -> List[dict]:
        """Return individual experiment data for plotting separate lines."""
        return self.get_individual_experiment_data_list()

    def _refresh_plotting_system(self) -> None:
        """Refresh the plotting system when experiment selection changes."""
        # Emit signal to notify parent/listeners that experiment selection changed
        # Parent (PyBackend) connects this signal to plotting refresh
        self.experimentsChanged.emit()

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

    @Property('QVariant', notify=minimizerChanged)
    def minimizerTolerance(self) -> Optional[float]:
        return self._minimizers_logic.tolerance

    @Property('QVariant', notify=minimizerChanged)
    def minimizerMaxIterations(self) -> Optional[int]:
        return self._minimizers_logic.max_iterations

    @Slot(float)
    def setMinimizerTolerance(self, new_value: float) -> None:
        if self._minimizers_logic.set_tolerance(new_value):
            self.minimizerChanged.emit()

    @Slot(int)
    def setMinimizerMaxIterations(self, new_value: int) -> None:
        if self._minimizers_logic.set_max_iterations(new_value):
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
