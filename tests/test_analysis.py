from unittest.mock import MagicMock

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from EasyReflectometryApp.Backends.Py import analysis as analysis_module
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


def test_on_stop_fit_requests_worker_stop_without_immediate_cleanup(monkeypatch, qcore_application):
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
    assert analysis.fittingRunning is False
    assert analysis.fitErrorMessage == 'Fitting cancelled by user'


def test_fitting_start_stop_emits_stop_signal_when_fit_is_running(monkeypatch, qcore_application):
    analysis = _make_analysis(monkeypatch)
    analysis._fitting_logic.prepare_for_threaded_fit()
    received = {'count': 0}
    analysis.stopFit.connect(lambda: received.__setitem__('count', received['count'] + 1))

    analysis.fittingStartStop()

    assert received['count'] == 1


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
    assert worker.method_name == 'sample'
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

    # Mock prefitCheck to avoid complex real checks
    analysis.prefitCheck = MagicMock(return_value=True)

    # fittingStartStop should detect Bayesian mode and dispatch to sample
    analysis.fittingStartStop()

    worker = StubWorker.instances[-1]
    assert worker.method_name == 'sample'
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