from types import SimpleNamespace

import numpy as np
import pytest
from easyscience import Fitter
from easyscience import Minimizers
from easyscience import Parameter
from easyscience.base_classes import ModelBase

from EasyReflectometryApp.Backends.Py.workers import fitter_worker as fitter_worker_module
from EasyReflectometryApp.Backends.Py.workers.fitter_worker import FitCancelled
from EasyReflectometryApp.Backends.Py.workers.fitter_worker import FitterWorker
from tests.factories import make_worker_fitter


class SilentError(Exception):
    def __str__(self):
        return ''


def test_run_emits_finished_with_list_result(qcore_application):
    worker = FitterWorker(make_worker_fitter(method_result=[1, 2]), 'fit')
    received = {'finished': None, 'failed': None}

    worker.finished.connect(lambda value: received.__setitem__('finished', value))
    worker.failed.connect(lambda value: received.__setitem__('failed', value))

    worker.run()

    assert received['finished'] == [1, 2]
    assert received['failed'] is None


def test_run_wraps_non_list_result(qcore_application):
    worker = FitterWorker(make_worker_fitter(method_result='ok'), 'fit')
    received = []
    worker.finished.connect(received.append)

    worker.run()

    assert received == [['ok']]


def test_run_emits_failed_when_stop_requested_before_start(qcore_application):
    worker = FitterWorker(make_worker_fitter(method_result='ok'), 'fit')
    received = []
    worker.failed.connect(received.append)
    worker.stop()

    worker.run()

    assert received == ['Fitting cancelled before start']


def test_run_emits_failed_for_missing_method(qcore_application):
    worker = FitterWorker(object(), 'missing_method')
    received = []
    worker.failed.connect(received.append)

    worker.run()

    assert received == ["Fitter has no method 'missing_method'"]


def test_run_emits_failed_for_exception_message(qcore_application):
    worker = FitterWorker(make_worker_fitter(error=RuntimeError('boom')), 'fit')
    received = []
    worker.failed.connect(received.append)

    worker.run()

    assert received == ['boom']


def test_run_uses_fallback_message_for_empty_exception_string(qcore_application):
    worker = FitterWorker(make_worker_fitter(error=SilentError()), 'fit')
    received = []
    worker.failed.connect(received.append)

    worker.run()

    assert received == ['SilentError: Unknown error during fitting']


def test_run_injects_progress_callback_for_fit_method(qcore_application):
    fitter = make_worker_fitter(method_result='ok')
    worker = FitterWorker(fitter, 'fit', kwargs={'weights': [1.0]})

    worker.run()

    _, kwargs = fitter.calls[0]
    assert 'progress_callback' in kwargs
    assert callable(kwargs['progress_callback'])
    assert kwargs['weights'] == [1.0]


@pytest.mark.parametrize('method_name', ['fit', 'mcmc_sample'], ids=['bumps-fit', 'dream-sampling'])
def test_run_passes_abort_test_to_bumps_and_dream(qcore_application, method_name):
    fitter = make_worker_fitter(method_result='ok')
    fitter.minimizer = SimpleNamespace(package='bumps')
    setattr(fitter, method_name, fitter.fit)
    worker = FitterWorker(fitter, method_name)

    worker.run()

    abort_test = fitter.calls[0][1]['abort_test']
    assert abort_test() is False
    worker.stop()
    assert abort_test() is True
    # BUMPS stops through abort_test only; the callback keeps relaying progress.
    worker._progress_callback({'iteration': 1})


@pytest.mark.parametrize('package', ['lmfit', 'dfo'])
def test_run_stops_other_engines_from_the_progress_callback(qcore_application, package):
    """lmfit and DFO take no abort_test in the released core: the callback raises instead."""
    fitter = make_worker_fitter(method_result='ok')
    fitter.minimizer = SimpleNamespace(package=package)
    worker = FitterWorker(fitter, 'fit')
    received = []
    worker.progressDetail.connect(received.append)

    worker.run()

    kwargs = fitter.calls[0][1]
    assert 'abort_test' not in kwargs
    kwargs['progress_callback']({'iteration': 1})
    worker.stop()
    with pytest.raises(FitCancelled):
        kwargs['progress_callback']({'iteration': 2})
    assert [payload['iteration'] for payload in received] == [1]


@pytest.mark.parametrize('error', [None, RuntimeError('Fit aborted by user')], ids=['returns', 'raises'])
def test_run_reports_a_stop_as_cancelled_however_the_engine_ends(qcore_application, error):
    """BUMPS returns after an abort; lmfit, DFO and DREAM raise. Both are a cancellation."""
    worker = None

    def stop_then_end(*args, **kwargs):
        worker.stop()
        if error is not None:
            raise error
        return 'partial'

    fitter = make_worker_fitter(method_result='ok')
    fitter.fit = stop_then_end
    worker = FitterWorker(fitter, 'fit')
    received = {'finished': [], 'failed': []}
    worker.finished.connect(received['finished'].append)
    worker.failed.connect(received['failed'].append)

    worker.run()

    assert received == {'finished': [], 'failed': [FitterWorker.CANCELLED_MESSAGE]}


@pytest.fixture
def clock(monkeypatch):
    """A controllable monotonic clock for the progress throttle."""
    now = {'t': 100.0}
    monkeypatch.setattr(fitter_worker_module.time, 'monotonic', lambda: now['t'])
    return now


def test_progress_callback_emits_the_first_payload_at_once(qcore_application, clock):
    worker = FitterWorker(make_worker_fitter(method_result='ok'), 'fit')
    received = []
    worker.progressDetail.connect(received.append)

    worker._progress_callback({'iteration': 5, 'chi2': 12.5, 'refresh_plots': False})

    assert received == [{'iteration': 5, 'chi2': 12.5, 'refresh_plots': False}]


def test_progress_callback_emits_at_most_once_per_interval(qcore_application, clock):
    worker = FitterWorker(make_worker_fitter(method_result='ok'), 'fit')
    received = []
    worker.progressDetail.connect(received.append)

    worker._progress_callback({'iteration': 1})
    clock['t'] += FitterWorker.PROGRESS_INTERVAL_S * 0.99
    worker._progress_callback({'iteration': 2})
    clock['t'] += FitterWorker.PROGRESS_INTERVAL_S * 0.02
    worker._progress_callback({'iteration': 3})

    assert [payload['iteration'] for payload in received] == [1, 3]


def test_progress_callback_carries_a_suppressed_refresh_request(qcore_application, clock):
    worker = FitterWorker(make_worker_fitter(method_result='ok'), 'fit')
    received = []
    worker.progressDetail.connect(received.append)

    worker._progress_callback({'iteration': 1, 'refresh_plots': False})
    worker._progress_callback({'iteration': 2, 'refresh_plots': True})  # suppressed
    clock['t'] += FitterWorker.PROGRESS_INTERVAL_S * 1.5
    worker._progress_callback({'iteration': 3, 'refresh_plots': False})
    clock['t'] += FitterWorker.PROGRESS_INTERVAL_S * 1.5
    worker._progress_callback({'iteration': 4, 'refresh_plots': False})

    assert [(payload['iteration'], payload['refresh_plots']) for payload in received] == [(1, False), (3, True), (4, False)]


class _AbsSin(ModelBase):
    """|sin(phase * x + offset)|, counting its evaluations."""

    def __init__(self, offset: float, phase: float):
        super().__init__()
        self._offset = Parameter(offset, display_name='offset')
        self._phase = Parameter(phase, display_name='phase')
        self.evaluations = 0

    @property
    def offset(self) -> Parameter:
        return self._offset

    @property
    def phase(self) -> Parameter:
        return self._phase

    def __call__(self, x):
        self.evaluations += 1
        return np.abs(np.sin(self._phase.value * x + self._offset.value))


@pytest.mark.parametrize(
    'minimizer',
    [
        Minimizers.LMFit_leastsq,
        Minimizers.LMFit_powell,
        Minimizers.LMFit_scipy_least_squares,
        Minimizers.DFO,
        Minimizers.Bumps_simplex,
    ],
    ids=lambda minimizer: minimizer.name,
)
def test_cancel_stops_a_real_core_fit(qcore_application, minimizer):
    """Cancel works against the installed core for every engine, without core's lmfit/DFO abort_test.

    The worker is run synchronously, so ``progressDetail`` is delivered directly
    and can request the stop from inside the fit, after the first payload.
    """
    x = np.linspace(0, 5, 200)
    y = np.abs(np.sin(np.pi * x + 0.2))
    model = _AbsSin(0.354, 3.05)
    model.offset.fixed = False
    model.phase.fixed = False
    fitter = Fitter(model, model)
    fitter.switch_minimizer(minimizer)
    worker = FitterWorker(fitter, 'fit', args=(x, y), kwargs={'weights': np.ones_like(x)})
    received = {'finished': [], 'failed': []}
    worker.finished.connect(received['finished'].append)
    worker.failed.connect(received['failed'].append)
    worker.progressDetail.connect(lambda _payload: worker.stop())

    worker.run()

    assert received == {'finished': [], 'failed': [FitterWorker.CANCELLED_MESSAGE]}
    # Stopped at the evaluation or step after the first progress report, not run to the end.
    assert model.evaluations < 20
    if minimizer.package != 'bumps':
        # lmfit and DFO put the parameters back; BUMPS keeps its best point (core's behaviour).
        assert (model.offset.value, model.phase.value) == (0.354, 3.05)


def test_stop_sets_flag_without_terminating_idle_thread(qcore_application, monkeypatch):
    worker = FitterWorker(make_worker_fitter(method_result='ok'), 'fit')
    terminated = {'terminate': 0, 'wait': 0}
    monkeypatch.setattr(worker, 'isRunning', lambda: False)
    monkeypatch.setattr(worker, 'terminate', lambda: terminated.__setitem__('terminate', terminated['terminate'] + 1))
    monkeypatch.setattr(worker, 'wait', lambda: terminated.__setitem__('wait', terminated['wait'] + 1))

    worker.stop()

    assert worker.stop_requested is True
    assert terminated == {'terminate': 0, 'wait': 0}


def test_stop_terminates_running_thread(qcore_application, monkeypatch):
    worker = FitterWorker(make_worker_fitter(method_result='ok'), 'fit')
    terminated = {'terminate': 0, 'wait': 0}
    monkeypatch.setattr(worker, 'isRunning', lambda: True)
    monkeypatch.setattr(worker, 'terminate', lambda: terminated.__setitem__('terminate', terminated['terminate'] + 1))
    monkeypatch.setattr(worker, 'wait', lambda: terminated.__setitem__('wait', terminated['wait'] + 1))

    worker.stop()

    assert worker.stop_requested is True
    assert terminated == {'terminate': 0, 'wait': 0}
