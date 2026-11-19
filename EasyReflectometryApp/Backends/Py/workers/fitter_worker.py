"""
QThread-based worker for non-blocking fitting operations.

This module provides a FitterWorker class that runs fitting operations
in a background thread to keep the UI responsive during long-running fits.
"""

import math
import time
from typing import Any
from typing import Optional

from PySide6.QtCore import QThread
from PySide6.QtCore import Signal


class FitCancelled(Exception):
    """Raised from the progress callback to stop an engine that takes no ``abort_test``.

    The engine and core let it propagate (core restores the parameter values and
    re-raises it as ``FitError``); ``FitterWorker.run`` reports it as a cancellation.
    """


class FitterWorker(QThread):
    """
    QThread-based worker for executing fitting operations in the background.

    This worker wraps a fitter object and calls the specified method with
    the provided arguments. Results are emitted via signals to avoid
    blocking the main UI thread.

    Signals:
        finished(list): Emitted with fit results on successful completion.
        failed(str): Emitted with error message on failure or cancellation.
        progressDetail(dict): Emitted with the minimizer's progress payload,
            at most once per ``PROGRESS_INTERVAL_S``.
        previewRequested(dict): Emitted with the best parameter values so far,
            at most once per ``preview_interval_s``, while the fit waits between
            evaluations. Connect it with ``Qt.BlockingQueuedConnection``: the
            receiver may then read the model, which nothing writes until it
            returns (see MD/FIT_PREVIEW_DESIGN.md).

    Example:
        worker = FitterWorker(
            fitter=multi_fitter,
            method_name='fit',
            args=(x_data, y_data),
            kwargs={'weights': weights, 'method': 'leastsq'}
        )
        worker.finished.connect(on_fit_complete)
        worker.failed.connect(on_fit_failed)
        worker.start()
    """

    # Signal emitted when fitting completes successfully
    # Carries the list of FitResults objects
    finished = Signal(list)

    # Signal emitted when fitting fails
    # Carries the error message string
    failed = Signal(str)

    # Detailed fitting progress payload emitted from minimizer callbacks
    progressDetail = Signal(dict)

    # Best parameter values so far, for the live preview of a classical fit
    previewRequested = Signal(dict)

    #: Shortest time between two ``progressDetail`` emissions. lmfit and DFO call
    #: back on every evaluation; a person reads the progress at most a few times a second.
    PROGRESS_INTERVAL_S = 0.1

    #: Default shortest time between two previews; 0 turns the preview off.
    DEFAULT_PREVIEW_INTERVAL_S = 1.0

    CANCELLED_MESSAGE = 'Fitting cancelled by user'

    def __init__(
        self,
        fitter: Any,
        method_name: str,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        parent: Optional[Any] = None,
        preview_interval_s: float = 0.0,
    ):
        """
        Initialize the fitter worker.

        :param fitter: The fitter object (e.g., MultiFitter or its internal fitter).
        :param method_name: Name of the method to call on the fitter.
        :param args: Positional arguments to pass to the method.
        :param kwargs: Keyword arguments to pass to the method.
        :param parent: Optional parent QObject.
        :param preview_interval_s: Shortest time between two ``previewRequested``; 0: no preview.
        """
        super().__init__(parent)
        self._fitter = fitter
        self._method_name = method_name
        self._args = args
        self._kwargs = kwargs if kwargs is not None else {}
        self._stop_requested = False
        # True when the engine takes no abort_test, so a stop is raised from the progress callback.
        self._raise_on_stop = False
        self._last_progress_emit: float | None = None
        # A classical fit has a best point; a sampling run does not.
        self._track_best = method_name == 'fit'
        self._best_progress: dict | None = None
        self._last_iteration = 0
        self._preview_interval_s = max(float(preview_interval_s), 0.0)
        self._last_preview: float | None = None
        self._best_changed_since_preview = False

    def run(self) -> None:
        """
        Execute the fitting operation in the background thread.

        This method is called automatically when start() is invoked.
        Results are emitted via the finished or failed signals.
        """
        # TODO: Thread-safety: fitting uses shared model state; consider snapshotting or blocking edits during execution.
        # Check if stop was requested before starting
        if self._stop_requested:
            self.failed.emit('Fitting cancelled before start')
            return

        # Verify the method exists on the fitter
        if not hasattr(self._fitter, self._method_name):
            self.failed.emit(f"Fitter has no method '{self._method_name}'")
            return

        method = getattr(self._fitter, self._method_name)
        kwargs = dict(self._kwargs)
        if self._method_name in ('fit', 'mcmc_sample'):
            kwargs.setdefault('progress_callback', self._progress_callback)
            if self._method_name == 'mcmc_sample' or self._uses_bumps_minimizer():
                # BUMPS fits and DREAM sampling poll it on every step.
                kwargs.setdefault('abort_test', lambda: self._stop_requested)
            else:
                # lmfit and DFO take no abort_test in the released core (DFO rejects
                # the keyword); they are stopped by raising from the progress callback.
                self._raise_on_stop = True
        try:
            result = method(*self._args, **kwargs)
        except Exception as ex:
            if not self._stop_requested:
                self.failed.emit(str(ex) or f'{type(ex).__name__}: Unknown error during fitting')
                return
            result = None

        # A stopped run either returns early (BUMPS fit) or raises (lmfit, DFO, DREAM);
        # both are a cancellation, not a result or an error. Decided by the stop flag,
        # not by the message: core wraps the raised exception's text.
        if self._stop_requested:
            self.failed.emit(self.CANCELLED_MESSAGE)
            return

        # Ensure result is a list for consistent handling
        if not isinstance(result, list):
            result = [result]

        self.finished.emit(result)

    def _progress_callback(self, payload: dict) -> None:
        """Relay progress payloads from the minimizer to Qt, at most once per ``PROGRESS_INTERVAL_S``.

        Each payload is a full snapshot, so dropping one in between loses nothing.
        The best point is tracked from every payload, before the throttle, and a
        preview is requested when it is due (see ``_request_preview_if_due``).

        For an engine without ``abort_test`` it raises ``FitCancelled`` once a stop
        is requested. The check comes first, so it runs on every callback (every
        evaluation for lmfit and DFO).
        """
        if self._raise_on_stop and self._stop_requested:
            raise FitCancelled(self.CANCELLED_MESSAGE)
        now = time.monotonic()
        if self._track_best:
            self._track_best_progress(payload)
            self._request_preview_if_due(now)
        if self._last_progress_emit is not None and now - self._last_progress_emit < self.PROGRESS_INTERVAL_S:
            return
        self._last_progress_emit = now
        self.progressDetail.emit(payload)

    def _track_best_progress(self, payload: dict) -> None:
        """Keep the payload with the lowest chi2 seen (lmfit reports the point just
        evaluated, DFO the best so far, BUMPS its step's point)."""
        self._last_iteration = int(payload.get('iteration', self._last_iteration) or 0)
        values = payload.get('parameter_values')
        chi2 = payload.get('chi2')
        # A BUMPS point that violates an inequality constraint carries the penalty as chi2.
        if not values or payload.get('infeasible') or chi2 is None or not math.isfinite(chi2):
            return
        if self._best_progress is None or chi2 < self._best_progress['chi2']:
            self._best_progress = {
                'chi2': float(chi2),
                'reduced_chi2': float(payload.get('reduced_chi2', chi2)),
                'parameter_values': dict(values),
            }
            self._best_changed_since_preview = True

    def _request_preview_if_due(self, now: float) -> None:
        """Emit ``previewRequested`` when the best point improved and the interval has passed.

        The first interval starts at the first callback, so the starting point is
        not previewed. With a blocking connection this returns once the preview is drawn.
        """
        if self._preview_interval_s <= 0 or self._stop_requested:
            return
        if self._last_preview is None:
            self._last_preview = now
            return
        if not self._best_changed_since_preview or now - self._last_preview < self._preview_interval_s:
            return
        self._best_changed_since_preview = False
        self.previewRequested.emit(dict(self._best_progress['parameter_values']))
        # Measured after the preview, so a slow redraw cannot take the whole interval.
        self._last_preview = time.monotonic()

    @property
    def best_progress(self) -> dict | None:
        """The best point of a classical fit so far: ``chi2``, ``reduced_chi2``,
        ``parameter_values`` and ``iterations`` (the last count reported), or None."""
        if self._best_progress is None:
            return None
        return {**self._best_progress, 'iterations': self._last_iteration}

    def _uses_bumps_minimizer(self) -> bool:
        """Return True if the fitter's minimizer is BUMPS (and therefore accepts ``abort_test``)."""
        minimizer = getattr(self._fitter, 'minimizer', None)
        return getattr(minimizer, 'package', None) == 'bumps'

    def stop(self) -> None:
        """
        Request the fitting operation to stop.

        This only sets a flag; the thread is **not** terminated. BUMPS and DREAM
        poll it through ``abort_test`` on each step; lmfit and DFO are stopped at
        their next evaluation by ``FitCancelled`` raised from the progress callback.
        Either way the run stops promptly and ``failed`` is emitted with
        ``CANCELLED_MESSAGE``.
        """
        self._stop_requested = True

    @property
    def stop_requested(self) -> bool:
        """Return True if stop has been requested."""
        return self._stop_requested
