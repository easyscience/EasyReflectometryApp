from unittest.mock import MagicMock

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from EasyReflectometryApp.Backends.Py import analysis as analysis_module
from EasyReflectometryApp.Backends.Py.logic.fitting import Fitting
from tests.factories import make_project


class StubParametersLogic:
    def __init__(self, _project_lib):
        pass


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