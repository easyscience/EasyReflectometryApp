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

            # Check if stop was requested during execution
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
        """
        self._stop_requested = True
        if self.isRunning():
            self.terminate()
            self.wait()

    @property
    def stop_requested(self) -> bool:
        """Return True if stop has been requested."""
        return self._stop_requested
