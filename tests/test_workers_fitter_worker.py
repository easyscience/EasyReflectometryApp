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


def test_progress_callback_emits_detail_payload(qcore_application):
    worker = FitterWorker(make_worker_fitter(method_result='ok'), 'fit')
    received = []
    worker.progressDetail.connect(received.append)
    payload = {'iteration': 5, 'chi2': 12.5, 'finished': False}

    should_continue = worker._progress_callback(payload)

    assert should_continue is True
    assert received == [payload]


def test_progress_callback_requests_stop_when_flagged(qcore_application):
    worker = FitterWorker(make_worker_fitter(method_result='ok'), 'fit')

    worker.stop()

    should_continue = worker._progress_callback({'iteration': 1})

    assert should_continue is False


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
