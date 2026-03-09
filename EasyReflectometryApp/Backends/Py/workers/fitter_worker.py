"""
QThread-based worker for non-blocking fitting operations.

This module provides a FitterWorker class that runs fitting operations
in a background thread to keep the UI responsive during long-running fits.
"""

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
        failed(str): Emitted with error message on failure.
        progress(int): Emitted with progress percentage (0-100) during fitting.

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

    # Signal emitted to report fitting progress (0-100)
    progress = Signal(int)

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

        try:
            # Get the method and call it
            method = getattr(self._fitter, self._method_name)
            result = method(*self._args, **self._kwargs)

            # NOTE: This check only catches stop requests that occurred AFTER the fit
            # completed but before we emit the result. It does NOT interrupt the fitting
            # algorithm mid-execution since lmfit/scipy don't support cancellation callbacks.
            # The effective cancellation window is only before the fit starts (checked above).
            if self._stop_requested:
                self.failed.emit('Fitting cancelled by user')
                return

            # Ensure result is a list for consistent handling
            if not isinstance(result, list):
                result = [result]

            self.finished.emit(result)

        except Exception as ex:
            # Emit failure with error message
            error_message = str(ex)
            if not error_message:
                error_message = f'{type(ex).__name__}: Unknown error during fitting'
            self.failed.emit(error_message)

    def stop(self) -> None:
        """
        Request the fitting operation to stop.

        This sets a flag that is checked during execution and also
        terminates the thread if it's still running. Call wait() after
        this to ensure proper thread cleanup.

        .. warning::
            DANGEROUS: This method uses QThread.terminate() which is strongly
            discouraged by Qt documentation. It can:
            - Leave mutex locks held indefinitely causing deadlocks
            - Corrupt data structures mid-operation
            - Prevent proper cleanup of resources (especially numpy arrays, scipy internals)
            - Cause memory leaks and undefined behavior

            The fitting libraries (lmfit, scipy) do not support graceful cancellation.
            The stop flag is only effective BEFORE the fit starts - once the fitting
            algorithm is running, it cannot be interrupted cleanly.

            See THREAD_TERMINATION_WARNING.md for details on known issues and
            potential future improvements (e.g., using subprocess instead of QThread).
        """
        self._stop_requested = True
        if self.isRunning():
            # WARNING: terminate() is dangerous but necessary since fitting
            # libraries don't support graceful cancellation. See docstring above.
            self.terminate()
            self.wait()

    @property
    def stop_requested(self) -> bool:
        """Return True if stop has been requested."""
        return self._stop_requested
