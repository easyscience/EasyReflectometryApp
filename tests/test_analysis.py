from types import SimpleNamespace
from unittest.mock import MagicMock

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from EasyReflectometryApp.Backends.Py import analysis as analysis_module
from EasyReflectometryApp.Backends.Py.logic.experiment_selection import ExperimentSelection
from EasyReflectometryApp.Backends.Py.logic.fitting import Fitting
from tests.factories import make_project


class StubParametersLogic:
    def __init__(self, _project_lib):
        pass

    @property
    def parameters(self):
        return []


class StubCalculatorsLogic:
    def __init__(self, _project_lib):
        pass


class StubExperimentLogic:
    def __init__(self, project_lib):
        self._project_lib = project_lib

    def available(self):
        return ['Exp 1']

    def current_index(self):
        return 0


class StubMinimizersLogic:
    def __init__(self, _project_lib):
        self.tolerance = None
        self.max_iterations = None

    def selected_minimizer_enum(self):
        return None

    def is_bayesian_selected(self):
        return False


class StubWorker(QObject):
    finished = Signal(list)
    failed = Signal(str)
    progressDetail = Signal(dict)

    instances = []

    def __init__(self, fitter, method_name, args=(), kwargs=None, parent=None):
        super().__init__(parent)
        self.fitter = fitter
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs or {}
        self.parent = parent
        self.stop_calls = 0
        self.start_calls = 0
        self.delete_calls = 0
        self.termination_enabled = None
        StubWorker.instances.append(self)

    def setTerminationEnabled(self, value):
        self.termination_enabled = value

    def start(self):
        self.start_calls += 1

    def stop(self):
        self.stop_calls += 1

    def deleteLater(self):
        self.delete_calls += 1


def _make_analysis(monkeypatch):
    project = make_project()
    monkeypatch.setattr(analysis_module, 'ParametersLogic', StubParametersLogic)
    monkeypatch.setattr(analysis_module, 'CalculatorsLogic', StubCalculatorsLogic)
    monkeypatch.setattr(analysis_module, 'ExperimentLogic', StubExperimentLogic)
    monkeypatch.setattr(analysis_module, 'MinimizersLogic', StubMinimizersLogic)
    monkeypatch.setattr(analysis_module, 'FitterWorker', StubWorker)
    analysis = analysis_module.Analysis(project)
    analysis._clearCacheAndEmitParametersChanged = MagicMock()
    return analysis


def test_start_threaded_fit_propagates_progress_to_properties(monkeypatch, qcore_application):
    StubWorker.instances = []
    analysis = _make_analysis(monkeypatch)
    analysis._fitting_logic.prepare_threaded_fit = MagicMock(
        return_value=('fake-fitter', ['x'], ['y'], ['w'], None)
    )
    fitting_changed = {'count': 0}
    analysis.fittingChanged.connect(
        lambda: fitting_changed.__setitem__('count', fitting_changed['count'] + 1)
    )

    analysis._start_threaded_fit()

    worker = StubWorker.instances[-1]
    worker.progressDetail.emit(
        {
            'iteration': 9,
            'chi2': 3.5,
            'reduced_chi2': 1.4,
            'parameter_values': {'thickness': 12.0},
            'refresh_plots': False,
            'finished': False,
        }
    )

    assert worker.method_name == 'fit'
    assert worker.kwargs == {'weights': ['w'], 'method': None}
    assert worker.start_calls == 1
    assert analysis.fittingRunning is True
    assert analysis.fitIteration == 9
    assert analysis.fitInterimChi2 == 3.5
    assert analysis.fitInterimReducedChi2 == 1.4
    assert analysis.fitProgressMessage == 'Fitting... iter 9, Chi2 = 3.5'
    assert analysis.fitHasInterimUpdate is True
    assert analysis.fitHasPreviewUpdate is False
    assert analysis.fitPreviewParameterValues == {'thickness': 12.0}
    assert fitting_changed['count'] >= 2


def test_on_stop_fit_requests_worker_stop_and_keeps_ui_locked_until_thread_exits(monkeypatch, qcore_application):
    """Cancel only requests a cooperative stop; ``running`` stays True until the
    worker thread actually exits, so a second fit cannot start while a
    non-abortable minimizer is still mutating the shared parameters."""
    StubWorker.instances = []
    analysis = _make_analysis(monkeypatch)
    analysis._fitting_logic.prepare_threaded_fit = MagicMock(
        return_value=('fake-fitter', ['x'], ['y'], ['w'], None)
    )

    analysis._start_threaded_fit()
    worker = StubWorker.instances[-1]

    analysis._onStopFit()

    assert worker.stop_calls == 1
    assert analysis._fitter_thread is worker
    # UI stays locked: the thread has not exited yet.
    assert analysis.fittingRunning is True
    assert analysis._fitting_logic.fit_cancelled is True

    # Worker thread exits and reports the cancellation.
    worker.failed.emit('Fitting cancelled by user')

    assert analysis._fitter_thread is None
    assert analysis.fittingRunning is False
    assert analysis.fitErrorMessage == 'Fitting cancelled by user'


def test_stale_worker_signals_are_ignored_after_new_fit_starts(monkeypatch, qcore_application):
    """Late signals from a superseded worker must not clobber the current run."""
    StubWorker.instances = []
    analysis = _make_analysis(monkeypatch)
    analysis._fitting_logic.prepare_threaded_fit = MagicMock(
        return_value=('fake-fitter', ['x'], ['y'], ['w'], None)
    )

    analysis._start_threaded_fit()
    stale_worker = StubWorker.instances[-1]

    # Simulate a newer worker having taken over.
    analysis._start_threaded_fit()
    current_worker = StubWorker.instances[-1]
    assert analysis._fitter_thread is current_worker

    # The old worker finally exits — its failure signal must be ignored.
    stale_worker.failed.emit('Fitting cancelled by user')

    assert analysis._fitter_thread is current_worker
    assert analysis.fittingRunning is True
    assert analysis.fitErrorMessage in ('', None)


def test_fitting_start_stop_emits_stop_signal_when_fit_is_running(monkeypatch, qcore_application):
    analysis = _make_analysis(monkeypatch)
    analysis._fitting_logic.prepare_for_threaded_fit()
    received = {'count': 0}
    analysis.stopFit.connect(lambda: received.__setitem__('count', received['count'] + 1))

    analysis.fittingStartStop()

    assert received['count'] == 1


def _param(name, min_value, max_value, fit=True):
    return {'name': name, 'min': min_value, 'max': max_value, 'fit': fit}


def _make_analysis_for_prefit(monkeypatch, parameters, minimizer='LMFit_leastsq'):
    analysis = _make_analysis(monkeypatch)
    analysis._chached_parameters = parameters
    analysis._minimizers_logic.minimizers_available = lambda: [minimizer]
    analysis._minimizers_logic.minimizer_current_index = lambda: 0
    return analysis


def test_prefit_errors_empty_for_valid_parameters(monkeypatch, qcore_application):
    analysis = _make_analysis_for_prefit(monkeypatch, [_param('a', 0.0, 1.0), _param('b', 5.0, 5.0, fit=False)])

    assert analysis._prefit_errors() == []


def test_prefit_errors_reports_every_parameter_with_invalid_bounds(monkeypatch, qcore_application):
    analysis = _make_analysis_for_prefit(monkeypatch, [_param('a', 1.0, 1.0), _param('b', 2.0, 0.0)])

    errors = analysis._prefit_errors()

    assert len(errors) == 2
    assert "'a'" in errors[0]
    assert "'b'" in errors[1]


def test_prefit_errors_rejects_infinite_bounds_for_differential_evolution(monkeypatch, qcore_application):
    parameters = [_param('a', float('-inf'), 1.0), _param('b', 0.0, float('inf')), _param('c', 0.0, 1.0)]
    analysis = _make_analysis_for_prefit(monkeypatch, parameters, minimizer='LMFit_differential_evolution')

    errors = analysis._prefit_errors()

    assert len(errors) == 1
    assert '\na,\nb\n' in errors[0]


def test_prefit_errors_allows_infinite_bounds_for_other_minimizers(monkeypatch, qcore_application):
    analysis = _make_analysis_for_prefit(monkeypatch, [_param('a', float('-inf'), float('inf'))])

    assert analysis._prefit_errors() == []


def test_fitting_start_stop_emits_prefit_check_failed_and_does_not_start(monkeypatch, qcore_application):
    StubWorker.instances = []
    analysis = _make_analysis_for_prefit(monkeypatch, [_param('a', 1.0, 0.0)])
    analysis._start_threaded_fit = MagicMock()
    received = []
    analysis.prefitCheckFailed.connect(lambda title, message: received.append((title, message)))

    analysis.fittingStartStop()

    assert len(received) == 1
    assert received[0][0] == 'Invalid Parameter Bounds'
    assert "'a'" in received[0][1]
    analysis._start_threaded_fit.assert_not_called()


def test_cancelled_worker_failure_does_not_emit_fit_failed(monkeypatch, qcore_application):
    StubWorker.instances = []
    analysis = _make_analysis(monkeypatch)
    analysis._fitting_logic = Fitting(make_project())
    analysis._clearCacheAndEmitParametersChanged = MagicMock()
    analysis._fitting_logic.prepare_for_threaded_fit()
    analysis._fitting_logic.stop_fit()
    analysis._fitter_thread = StubWorker('fake-fitter', 'fit')
    received = []
    analysis.fitFailed.connect(received.append)

    analysis._on_fit_failed('Fit cancelled by progress callback')

    assert analysis._fitter_thread is None
    assert analysis.fitErrorMessage == 'Fitting cancelled by user'
    assert received == []
    analysis._clearCacheAndEmitParametersChanged.assert_called_once_with()


def test_on_fit_finished_records_results_on_project_fitter(monkeypatch, qcore_application):
    """The canonical project fitter must learn the fit results.

    Otherwise ``project.fitter.reduced_chi`` stays None and the HTML summary's
    goodness-of-fit shows 'N/A' even though the Analysis section has a value.
    """
    from tests.factories import FakeFitResult

    analysis = _make_analysis(monkeypatch)
    analysis._fitting_logic = Fitting(make_project())
    analysis._clearCacheAndEmitParametersChanged = MagicMock()

    fitter = MagicMock()
    analysis._project_lib.fitter = fitter

    results = [FakeFitResult(chi2=20.0, n_pars=4, x=list(range(14)))]
    analysis._on_fit_finished(results)

    fitter.record_fit_results.assert_called_once()
    (recorded,) = fitter.record_fit_results.call_args.args
    assert recorded == results


# ---------------------------------------------------------------------------
# Bayesian sampling dispatch tests
# ---------------------------------------------------------------------------


class StubBayesianMinimizersLogic(StubMinimizersLogic):
    """Minimizers stub that reports Bayesian mode is active."""

    def is_bayesian_selected(self):
        return True


def _make_analysis_bayesian(monkeypatch):
    """Create an Analysis instance configured for Bayesian sampling."""
    project = make_project()
    monkeypatch.setattr(analysis_module, 'ParametersLogic', StubParametersLogic)
    monkeypatch.setattr(analysis_module, 'CalculatorsLogic', StubCalculatorsLogic)
    monkeypatch.setattr(analysis_module, 'ExperimentLogic', StubExperimentLogic)
    monkeypatch.setattr(analysis_module, 'MinimizersLogic', StubBayesianMinimizersLogic)
    monkeypatch.setattr(analysis_module, 'FitterWorker', StubWorker)
    analysis = analysis_module.Analysis(project)
    analysis._clearCacheAndEmitParametersChanged = MagicMock()
    return analysis


def test_start_threaded_sample_forwards_bayesian_kwargs(monkeypatch, qcore_application):
    """_start_threaded_sample passes samples, burn, thin, population, initializer to worker."""
    StubWorker.instances = []
    analysis = _make_analysis_bayesian(monkeypatch)
    analysis._fitting_logic.prepare_threaded_sample = MagicMock(
        return_value=('multi-fitter', 'data-group')
    )
    # Set non-default Bayesian hyper-params
    analysis._bayesian_logic.samples = 5000
    analysis._bayesian_logic.burn = 1000
    analysis._bayesian_logic.thin = 5
    analysis._bayesian_logic.population = 8
    analysis._bayesian_logic.initializer = 'lhs'

    analysis._start_threaded_sample()

    worker = StubWorker.instances[-1]
    assert worker.method_name == 'mcmc_sample'
    assert worker.args == ('data-group',)
    assert worker.kwargs == {
        'samples': 5000,
        'burn': 1000,
        'thin': 5,
        'population': 8,
        'initializer': 'lhs',
    }
    assert worker.start_calls == 1
    assert analysis.fittingRunning is True


def test_start_threaded_sample_uses_defaults_when_not_set(monkeypatch, qcore_application):
    """_start_threaded_sample uses Bayesian DEFAULTS when no custom values are set."""
    StubWorker.instances = []
    analysis = _make_analysis_bayesian(monkeypatch)
    analysis._fitting_logic.prepare_threaded_sample = MagicMock(
        return_value=('multi-fitter', 'data-group')
    )

    analysis._start_threaded_sample()

    worker = StubWorker.instances[-1]
    assert worker.kwargs == {
        'samples': 10000,
        'burn': 2000,
        'thin': 1,
        'population': 10,
        'initializer': 'eps',
    }


def test_start_threaded_sample_propagates_sampling_progress(monkeypatch, qcore_application):
    """Progress payloads with sampling=True update Bayesian-specific progress properties."""
    StubWorker.instances = []
    analysis = _make_analysis_bayesian(monkeypatch)
    analysis._fitting_logic.prepare_threaded_sample = MagicMock(
        return_value=('multi-fitter', 'data-group')
    )

    analysis._start_threaded_sample()
    worker = StubWorker.instances[-1]
    worker.progressDetail.emit({
        'iteration': 25,
        'total_steps': 100,
        'chi2': 4.2,
        'reduced_chi2': 1.8,
        'sampling': True,
    })

    assert analysis.sampleProgressStep == 25
    assert analysis.sampleProgressMessage != ''
    assert analysis.sampleProgressHasUpdate is True


def test_fitting_start_stop_dispatches_to_sample_when_bayesian(monkeypatch, qcore_application):
    """fittingStartStop calls _start_threaded_sample when Bayesian minimizer is selected."""
    StubWorker.instances = []
    analysis = _make_analysis_bayesian(monkeypatch)
    analysis._fitting_logic.prepare_threaded_sample = MagicMock(
        return_value=('multi-fitter', 'data-group')
    )

    # Mock the pre-fit check to avoid complex real checks
    analysis._prefit_errors = MagicMock(return_value=[])

    # fittingStartStop should detect Bayesian mode and dispatch to sample
    analysis.fittingStartStop()

    worker = StubWorker.instances[-1]
    assert worker.method_name == 'mcmc_sample'
    assert 'samples' in worker.kwargs
    assert 'burn' in worker.kwargs
    assert 'thin' in worker.kwargs
    assert 'population' in worker.kwargs
    assert 'initializer' in worker.kwargs


def test_start_threaded_sample_error_emits_fit_failed(monkeypatch, qcore_application):
    """When prepare_threaded_sample returns None, fitFailed signal is emitted."""
    StubWorker.instances = []
    analysis = _make_analysis_bayesian(monkeypatch)
    analysis._fitting_logic.prepare_threaded_sample = MagicMock(return_value=(None, None))
    # Make prepare_threaded_sample return None and set error message (as real code does)
    def _prepare_and_fail(*args, **kwargs):
        analysis._fitting_logic._fit_error_message = 'No experiments to sample'
        return None, None

    analysis._fitting_logic.prepare_threaded_sample = MagicMock(side_effect=_prepare_and_fail)

    received = []
    analysis.fitFailed.connect(received.append)

    analysis._start_threaded_sample()

    assert len(received) == 1
    assert 'No experiments to sample' in received[0]


def test_bayesian_initializer_property_round_trip(monkeypatch, qcore_application):
    """bayesianInitializer property and setter work through the QML-facing layer."""
    analysis = _make_analysis_bayesian(monkeypatch)
    assert analysis.bayesianInitializer == 'eps'
    assert analysis.bayesianInitializerOptions == ['eps', 'cov', 'lhs', 'random']

    analysis.setBayesianInitializer('lhs')
    assert analysis.bayesianInitializer == 'lhs'

    analysis.setBayesianInitializer('cov')
    assert analysis.bayesianInitializer == 'cov'

def test_model_index_for_experiment_paired_with_a_removed_model(monkeypatch, qcore_application):
    analysis = _make_analysis(monkeypatch)
    project = analysis._experiments_logic._project_lib
    project._models.add_model()
    project._experiments[0] = SimpleNamespace(model=project._models[-1])
    assert analysis.modelIndexForExperiment == len(project._models) - 1

    project._experiments[0] = SimpleNamespace(model=object())

    assert analysis.modelIndexForExperiment == -1



def _make_analysis_with_experiments(monkeypatch, count):
    """An Analysis with the real experiment logic over `count` named experiments."""
    project = make_project(experiments={i: SimpleNamespace(name=f'E{i}') for i in range(count)})
    monkeypatch.setattr(analysis_module, 'ParametersLogic', StubParametersLogic)
    monkeypatch.setattr(analysis_module, 'CalculatorsLogic', StubCalculatorsLogic)
    monkeypatch.setattr(analysis_module, 'MinimizersLogic', StubMinimizersLogic)
    monkeypatch.setattr(analysis_module, 'FitterWorker', StubWorker)
    analysis = analysis_module.Analysis(project, selection=ExperimentSelection())
    analysis._clearCacheAndEmitParametersChanged = MagicMock()
    return analysis, project


def test_selection_starts_with_the_first_experiment(monkeypatch, qcore_application):
    analysis, _project = _make_analysis_with_experiments(monkeypatch, 3)

    assert analysis.selectedExperimentIndices == [0]


def test_set_selected_experiments_makes_the_first_one_current(monkeypatch, qcore_application):
    analysis, project = _make_analysis_with_experiments(monkeypatch, 3)
    emitted = []
    analysis.experimentsChanged.connect(lambda: emitted.append('experiments'))

    analysis.setSelectedExperimentIndices([2, 1, 9])

    assert analysis.selectedExperimentIndices == [2, 1]
    assert project._current_experiment_index == 2
    assert emitted == ['experiments']

    analysis.setSelectedExperimentIndices([2, 1])  # unchanged
    assert emitted == ['experiments']


def test_removing_an_experiment_shifts_the_selection(monkeypatch, qcore_application):
    analysis, project = _make_analysis_with_experiments(monkeypatch, 4)
    analysis.setSelectedExperimentIndices([1, 3])

    analysis.removeExperiment(0)

    assert analysis.selectedExperimentIndices == [0, 2]
    assert project._current_experiment_index == 0


def test_removing_the_selected_experiment_drops_it(monkeypatch, qcore_application):
    analysis, _project = _make_analysis_with_experiments(monkeypatch, 3)
    analysis.setSelectedExperimentIndices([0, 2])

    analysis.removeExperiment(2)

    assert analysis.selectedExperimentIndices == [0]


def test_prune_drops_experiments_removed_elsewhere(monkeypatch, qcore_application):
    analysis, project = _make_analysis_with_experiments(monkeypatch, 3)
    analysis.setSelectedExperimentIndices([1, 2])
    del project._experiments[2]  # e.g. removed with its model

    assert analysis.prune_selected_experiments() is True
    assert analysis.selectedExperimentIndices == [1]
    assert project._current_experiment_index == 1


def test_reset_selects_only_the_current_experiment(monkeypatch, qcore_application):
    analysis, project = _make_analysis_with_experiments(monkeypatch, 3)
    analysis.setSelectedExperimentIndices([0, 1, 2])
    project._current_experiment_index = 1

    assert analysis.reset_selected_experiments() is True
    assert analysis.selectedExperimentIndices == [1]
