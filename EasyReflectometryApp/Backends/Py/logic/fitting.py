import logging
from typing import TYPE_CHECKING
from typing import List
from typing import Optional
from typing import cast

from easyreflectometry import Project as ProjectLib
from easyscience.fitting import FitResults
from easyscience.fitting.minimizers.utils import FitError

if TYPE_CHECKING:
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

    def stop_fit(self) -> None:
        """Request fitting to stop and clean up state."""
        self._stop_requested = True
        self._result = None
        self._results = []
        self._running = False
        self._finished = True
        self._fit_cancelled = True
        self._fit_error_message = 'Fitting cancelled by user'
        self._show_results_dialog = True

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
                items = sorted(items)
            except TypeError:
                pass
            return [experiment for _, experiment in items]

        return list(experiments)

    def prepare_threaded_fit(self, minimizers_logic: 'Minimizers') -> tuple:
        """Prepare data for threaded fitting.

        :param minimizers_logic: The minimizers logic instance to get the current method.
        :return: Tuple of (fitter, x_data, y_data, weights, method) or (None, None, None, None, None) on error.
        """
        try:
            from easyreflectometry.fitting import MultiFitter

            experiments = self._ordered_experiments()
            if not experiments:
                self._fit_error_message = 'No experiments to fit'
                self._running = False
                self._finished = True
                self._show_results_dialog = True
                return None, None, None, None, None

            # Create MultiFitter with all models
            models = [experiment.model for experiment in experiments]
            multi_fitter = MultiFitter(*models)

            # Apply the user-selected minimizer to the new fitter
            selected_minimizer = minimizers_logic.selected_minimizer_enum()
            if selected_minimizer is not None:
                multi_fitter.easy_science_multi_fitter.switch_minimizer(selected_minimizer)
                logger.info(
                    'Fitting: applied minimizer %s to MultiFitter (engine: %s, method: %s)',
                    selected_minimizer.name,
                    multi_fitter.easy_science_multi_fitter.minimizer.package,
                    multi_fitter.easy_science_multi_fitter.minimizer._method,
                )
            if minimizers_logic.tolerance is not None:
                multi_fitter.easy_science_multi_fitter.tolerance = minimizers_logic.tolerance
            if minimizers_logic.max_iterations is not None:
                multi_fitter.easy_science_multi_fitter.max_evaluations = minimizers_logic.max_iterations

            # Prepare data arrays for all experiments, masking out zero-variance points
            import numpy as np

            x_data = []
            y_data = []
            weights = []
            for idx, experiment in enumerate(experiments):
                x_vals = np.asarray(experiment.x)
                y_vals = np.asarray(experiment.y)
                ye_vals = np.asarray(experiment.ye)

                # Mask out points with zero variance (same as MultiFitter.fit in EasyReflectometryLib)
                valid = ye_vals > 0
                num_masked = int(np.sum(~valid))
                if num_masked > 0:
                    exp_name = experiment.name if hasattr(experiment, 'name') else f'index {idx}'
                    logger.warning(
                        'Masked %d data point(s) in experiment %s due to zero variance.',
                        num_masked,
                        exp_name,
                    )

                x_data.append(x_vals[valid])
                y_data.append(y_vals[valid])
                # ye contains variances (sigma²); weights = 1/sigma = 1/sqrt(variance)
                weights.append(1.0 / np.sqrt(ye_vals[valid]))

            # Method is optional in fit() - pass None to use minimizer's default
            method = None

            return multi_fitter.easy_science_multi_fitter, x_data, y_data, weights, method

        except Exception as e:
            self._fit_error_message = f'Error preparing fit: {e}'
            self._running = False
            self._finished = True
            self._show_results_dialog = True
            logger.exception('Error preparing threaded fit')
            return None, None, None, None, None

    def on_fit_finished(self, results: FitResults | List[FitResults]) -> None:
        """Handle successful completion of fitting.

        :param results: List of FitResults from the multi-fitter.
        """
        self._running = False
        self._finished = True
        self._show_results_dialog = True
        self._fit_error_message = None

        # Store result(s) - handle both single and multiple results
        if isinstance(results, list) and len(results) > 0:
            # For multi-experiment fits, store the list; use first for single-result properties
            self._results = results
            self._result = results[0]
            engine_name = getattr(results[0], 'minimizer_engine', 'unknown')
            logger.info('Fit finished: engine=%s, chi2=%s, success=%s', engine_name, self.fit_chi2, results[0].success)
        else:
            single_result = cast(Optional[FitResults], results)
            self._result = single_result
            self._results = [single_result] if single_result is not None else []

    @property
    def fit_n_pars(self) -> int:
        """Return the global number of refined parameters for the fit."""
        if self._results:
            return sum(result.n_pars for result in self._results)
        if self._result is None:
            return 0
        return self._result.n_pars

    @property
    def fit_chi2(self) -> float:
        """Return reduced chi-squared across all fits."""
        if self._results:
            try:
                if len(self._results) == 1:
                    return float(self._results[0].reduced_chi)
                total_chi2 = float(sum(result.chi2 for result in self._results))
                total_points = sum(len(result.x) for result in self._results)
                n_params = self._results[0].n_pars
                total_dof = total_points - n_params
                if total_dof <= 0:
                    return 0.0
                return total_chi2 / total_dof
            except (ValueError, TypeError):
                return 0.0
        if self._result is None:
            return 0.0
        try:
            return float(self._result.reduced_chi)
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
            self._fit_error_message = None
            try:
                # This needs extension to support multiple data sets
                exp_data = self._project_lib.experimental_data_for_model_at_index(0)
                self._result = self._project_lib.fitter.fit_single_data_set_1d(exp_data)
            except FitError as e:
                # Handle fit failure - create a failed result
                self._result = None
                self._fit_error_message = str(e)
                logger.warning('Fit failed: %s', e)
            except Exception as e:
                # Handle any other unexpected exceptions
                self._result = None
                self._fit_error_message = str(e)
                logger.warning('Unexpected error during fit: %s', e)
            finally:
                self._running = False
                self._finished = True
                self._show_results_dialog = True
