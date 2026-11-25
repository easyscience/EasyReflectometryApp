"""Quitting the application while a fit runs (#382).

The fit workers are children of ``Analysis``: one still running when the application
destroys it aborts the process with "QThread: Destroyed while thread is still running".
``Analysis`` stops and waits for them on ``aboutToQuit``. These tests run a real
``FitterWorker`` thread, connected by ``Analysis`` itself, including the blocking
preview connection a worker can be parked in when the event loop stops.
"""

import threading
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
import shiboken6

from EasyReflectometryApp.Backends.Py import analysis as analysis_module
from EasyReflectometryApp.Backends.Py.workers import fitter_worker as fitter_worker_module
from EasyReflectometryApp.Backends.Py.workers.fitter_worker import FitterWorker
from tests.test_analysis import _make_analysis
from tests.test_analysis import _prepared


class ParkingFitter:
    """An lmfit-like fit that reports progress until the worker's callback cancels it.

    Each evaluation takes two seconds on the worker's clock, so the second one is due a
    preview: the worker then waits in the blocking ``previewRequested`` emit until the
    GUI thread delivers it, which the test's GUI thread does not do on its own.
    """

    minimizer = SimpleNamespace(package='lmfit')

    def __init__(self, clock):
        self.clock = clock
        self.parking = threading.Event()

    def fit(self, *args, progress_callback=None, **kwargs):
        # Bounded, so a broken stop still ends the thread instead of aborting pytest.
        give_up = time.monotonic() + 20.0
        iteration = 0
        while time.monotonic() < give_up:
            iteration += 1
            self.clock['t'] += 2.0
            if iteration == 2:
                self.parking.set()
            progress_callback({'iteration': iteration, 'chi2': 100.0 - iteration, 'parameter_values': {'p': iteration}})
            time.sleep(0.001)
        return 'never stopped'


@pytest.fixture
def analysis_running_a_parked_fit(monkeypatch, qcore_application):
    clock = {'t': 100.0}
    # The worker's clock only: the quit handler's deadline keeps the real one.
    monkeypatch.setattr(fitter_worker_module, 'time', SimpleNamespace(monotonic=lambda: clock['t']))
    analysis = _make_analysis(monkeypatch)
    monkeypatch.setattr(analysis_module, 'FitterWorker', FitterWorker)
    fitter = ParkingFitter(clock)
    analysis._fitting_logic.prepare_threaded_fit = MagicMock(return_value=_prepared(core_fitter=fitter))
    analysis._fitting_logic.apply_parameter_values = MagicMock()
    analysis._fitting_logic.record_on_project = MagicMock()

    analysis._start_threaded_fit()
    worker = analysis._fitter_thread
    assert isinstance(worker, FitterWorker) and worker.parent() is analysis
    assert fitter.parking.wait(5.0)
    time.sleep(0.2)  # into the blocking preview emit
    assert worker.isRunning()
    yield analysis, worker
    # Whatever the test did, no thread may outlive it.
    worker.stop()
    while not worker.wait(50):
        qcore_application.processEvents()


@pytest.mark.parametrize('which', ['current', 'superseded'])
def test_quitting_stops_a_fit_parked_in_its_blocking_preview(analysis_running_a_parked_fit, which):
    analysis, worker = analysis_running_a_parked_fit
    if which == 'superseded':
        # Cancelled and replaced by a newer run, but still finishing its evaluation.
        analysis._fitter_thread = None
    emitted = []
    analysis.externalFittingChanged.connect(lambda: emitted.append('external'))
    analysis.fitFailed.connect(lambda message: emitted.append(message))

    started = time.monotonic()
    analysis._stop_workers_for_quit()

    assert not worker.isRunning()
    assert time.monotonic() - started < analysis_module.QUIT_WAIT_S
    # Stopped and dropped as stale: no preview drawn, nothing recorded or announced.
    analysis._fitting_logic.apply_parameter_values.assert_not_called()
    analysis._fitting_logic.record_on_project.assert_not_called()
    assert emitted == []
    assert analysis._fitter_thread is None
    # Not deleted while it was waited for (its deleteLater was disconnected).
    assert shiboken6.isValid(worker)


def test_quitting_with_no_fit_running_does_nothing(monkeypatch, qcore_application):
    analysis = _make_analysis(monkeypatch)
    analysis._fitting_logic.stop_fit = MagicMock()

    analysis._stop_workers_for_quit()

    analysis._fitting_logic.stop_fit.assert_not_called()


def test_analysis_stops_its_workers_when_the_application_quits(monkeypatch, qcore_application):
    calls = []
    monkeypatch.setattr(analysis_module.Analysis, '_stop_workers_for_quit', lambda self: calls.append(self))
    analysis = _make_analysis(monkeypatch)

    qcore_application.aboutToQuit.emit()

    assert analysis in calls
