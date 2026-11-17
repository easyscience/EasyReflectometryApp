"""
QThread-based worker for non-blocking fitting operations.

This module provides a FitterWorker class that runs fitting operations
in a background thread to keep the UI responsive during long-running fits.
"""

import time
from typing import Any
from typing import Optional

from PySide6.QtCore import QThread
from PySide6.QtCore import Signal


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

    #: Shortest time between two ``progressDetail`` emissions. lmfit and DFO call
    #: back on every evaluation; a person reads the progress at most a few times a second.
    PROGRESS_INTERVAL_S = 0.1

    CANCELLED_MESSAGE = 'Fitting cancelled by user'

    def __init__(
        self,
        fitter: Any,
        method_name: str,
        args: tuple = (),
        kwargs: Optional[dict] = None,
        parent: Optional[Any] = None,
    ):
        """
        Initialize the fitter worker.

        :param fitter: The fitter object (e.g., MultiFitter or its internal fitter).
        :param method_name: Name of the method to call on the fitter.
        :param args: Positional arguments to pass to the method.
        :param kwargs: Keyword arguments to pass to the method.
        :param parent: Optional parent QObject.
        """
        super().__init__(parent)
        self._fitter = fitter
        self._method_name = method_name
        self._args = args
        self._kwargs = kwargs if kwargs is not None else {}
        self._stop_requested = False
        self._last_progress_emit: float | None = None
        self._pending_refresh_plots = False

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
            # Every engine polls it during the run (BUMPS, DREAM, lmfit, DFO).
            kwargs.setdefault('abort_test', lambda: self._stop_requested)
        try:
            result = method(*self._args, **kwargs)
        except Exception as ex:
            if not self._stop_requested:
                self.failed.emit(str(ex) or f'{type(ex).__name__}: Unknown error during fitting')
                return
            result = None

        # A stopped run either returns early (BUMPS fit) or raises (lmfit, DFO, DREAM);
        # both are a cancellation, not a result or an error.
        if self._stop_requested:
            self.failed.emit(self.CANCELLED_MESSAGE)
            return

        # Ensure result is a list for consistent handling
        if not isinstance(result, list):
            result = [result]

        self.finished.emit(result)

    def _progress_callback(self, payload: dict) -> None:
        """Relay progress payloads from the minimizer to Qt, at most once per ``PROGRESS_INTERVAL_S``.

        Each payload is a full snapshot, so dropping one in between loses nothing,
        except ``refresh_plots``, which is an event: it is carried into the next
        emitted payload.
        """
        refresh_plots = self._pending_refresh_plots or bool(payload.get('refresh_plots', False))
        now = time.monotonic()
        if self._last_progress_emit is not None and now - self._last_progress_emit < self.PROGRESS_INTERVAL_S:
            self._pending_refresh_plots = refresh_plots
            return
        self._last_progress_emit = now
        self._pending_refresh_plots = False
        self.progressDetail.emit({**payload, 'refresh_plots': refresh_plots})

    def stop(self) -> None:
        """
        Request the fitting operation to stop.

        This only sets a flag; the thread is **not** terminated. Every engine
        polls it through ``abort_test`` (lmfit and DFO on each evaluation, BUMPS
        and DREAM on each step), so the run stops promptly and ``failed`` is
        emitted with ``CANCELLED_MESSAGE``.
        """
        self._stop_requested = True

    @property
    def stop_requested(self) -> bool:
        """Return True if stop has been requested."""
        return self._stop_requested
