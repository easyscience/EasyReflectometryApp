import os
import warnings

from EasyApplication.Logic.Logging import console
from easyreflectometry import Project as ProjectLib
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import QUrl
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot
from PySide6.QtQml import QJSValue

from .helpers import IO
from .logic.models import Models as ModelsLogic
from .logic.project import Project as ProjectLogic


def _from_qml(value):
    """Unwrap a QJSValue handed over by QML into plain Python data."""
    if isinstance(value, QJSValue):
        return value.toVariant()
    return value


def _local_path(path) -> str:
    """A local file path from a QML file-dialog entry (`QUrl`), a file URL or a path.

    `str()` of a `QUrl` is its Python repr, and `generalizePath` does not undo
    percent-encoding (spaces, non-ASCII names), so URLs go through Qt.
    """
    if isinstance(path, QUrl):
        return path.toLocalFile()
    path = str(path)
    if path.startswith('file:'):
        return QUrl(path).toLocalFile()
    return IO.generalizePath(path)


# The library's caveat for a file without a resolution column merged with
# files that have one, in the words of the user guide.
_NO_RESOLUTION_WARNING = 'carry no q-resolution'
_NO_RESOLUTION_MESSAGE = (
    'the file has no q-resolution column while the other data of this experiment do; '
    'its points are given a percentage (dq/q) resolution instead.'
)


def _user_warning_text(message) -> str:
    """The library's warning text, reworded for the dialog where it names internals."""
    text = str(message)
    if _NO_RESOLUTION_WARNING in text:
        return _NO_RESOLUTION_MESSAGE
    return text


# Spin channels accepted by the polarized import, in canonical order.
_CHANNELS = ('pp', 'pm', 'mp', 'mm')


class Experiment(QObject):
    experimentChanged = Signal()
    externalExperimentChanged = Signal()
    qRangeUpdated = Signal()
    # Emitted with a user-facing message when an import is rejected.
    loadFailed = Signal(str)
    # Emitted with a user-facing message when an import succeeded with a caveat.
    loadWarning = Signal(str)
    # Emitted with the list position of a newly imported experiment.
    experimentLoaded = Signal(int)

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._model_logic = ModelsLogic(project_lib)
        self._project_logic = ProjectLogic(project_lib)

    @Property(float, notify=experimentChanged)
    def scaling(self) -> float:
        return self._model_logic.scaling_at_current_index

    @Property(float, notify=experimentChanged)
    def background(self) -> float:
        return self._model_logic.background_at_current_index

    @Property(str, notify=experimentChanged)
    def resolution(self) -> str:
        return self._model_logic.resolution_at_current_index

    @Property(bool, notify=experimentChanged)
    def experimentalData(self) -> bool:
        return self._project_logic.experimental_data_at_current_index

    # Setters
    @Slot(int)
    def setModelIndex(self, value: int) -> None:
        self._model_logic.index = value

    @Slot(float)
    def setScaling(self, new_value: float) -> None:
        if self._model_logic.set_scaling_at_current_index(new_value):
            self.experimentChanged.emit()
            self.externalExperimentChanged.emit()

    @Slot(float)
    def setBackground(self, new_value: float) -> None:
        if self._model_logic.set_background_at_current_index(new_value):
            self.experimentChanged.emit()
            self.externalExperimentChanged.emit()

    @Slot(str)
    def setResolution(self, new_value: str) -> None:
        if self._model_logic.set_resolution_at_current_index(new_value):
            self.experimentChanged.emit()
            self.externalExperimentChanged.emit()

    # Actions
    @Slot(str)
    def load(self, paths: str) -> None:
        # paths is a string containing paths separated by a comma.
        # make a list out of it
        if isinstance(paths, str):
            paths = paths.split(',')

        q_range_changed = False
        for path in paths:
            generalized = IO.generalizePath(path)
            # A file that cannot be read is reported and skipped; the library adds
            # all of a file's datasets or none.
            try:
                if self._project_logic.count_datasets_in_file(generalized) > 1:
                    _count, changed = self._project_logic.load_all_experiments_from_file(generalized)
                else:
                    changed = self._project_logic.load_new_experiment(generalized)
            except Exception as error:  # noqa: BLE001 - any parse error reaches the user, not the event loop
                console.error(f'Import of {generalized} failed: {error}')
                self.loadFailed.emit(f'{os.path.basename(generalized)}: {error}')
                continue
            if changed:
                q_range_changed = True
            self.experimentChanged.emit()
            self.externalExperimentChanged.emit()
        if q_range_changed:
            self.qRangeUpdated.emit()

    @Slot('QVariant')
    def appendToCurrent(self, paths) -> None:
        """Add the files to the current experiment as more curves of the same contrast.

        A contrast is often measured as several curves (one per angle or
        wavelength band), each with its own q-resolution. Every file's points
        are merged into the current experiment and keep their own resolution,
        so the fit smears each point with the width it was measured with.

        `paths` is a list of `QUrl` (a QML file dialog's `selectedFiles`), file
        URLs or local paths.

        A file that cannot be added (a polarized experiment, a file holding
        several datasets, a parse error) is skipped; the others are still added.
        A file without a resolution column mixed with files that have one is
        added with an assumed resolution. All refusals and caveats of one call
        are reported together: through `loadFailed` when any file was refused,
        otherwise through `loadWarning`.
        """
        paths = _from_qml(paths)
        if isinstance(paths, (str, QUrl)):
            paths = paths.split(',') if isinstance(paths, str) else [paths]

        failures = []
        caveats = []
        q_range_changed = False
        for path in paths:
            if not path or (isinstance(path, QUrl) and path.isEmpty()):
                continue
            generalized = _local_path(path)
            name = os.path.basename(generalized)
            # catch_warnings swaps the process-wide warning state; the Experimental
            # data group is disabled while a fit runs, so no worker thread is
            # warning concurrently when this is reached from the GUI.
            try:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    changed = self._project_logic.append_to_current_experiment(generalized)
            except Exception as error:  # noqa: BLE001 - any refusal reaches the user, not the event loop
                console.error(f'Adding {generalized} to the current experiment failed: {error}')
                failures.append(f'{name}: {error}')
                continue
            for caught_warning in caught:
                if issubclass(caught_warning.category, UserWarning):
                    console.info(f'{name}: {caught_warning.message}')
                    caveats.append(f'{name}: {_user_warning_text(caught_warning.message)}')
                else:
                    # Not meant for the user (e.g. deprecations): hand it back to
                    # the normal warning machinery instead of swallowing it.
                    warnings.warn_explicit(
                        caught_warning.message,
                        caught_warning.category,
                        caught_warning.filename,
                        caught_warning.lineno,
                    )
            if changed:
                q_range_changed = True
            self.experimentChanged.emit()
            self.externalExperimentChanged.emit()
        if q_range_changed:
            self.qRangeUpdated.emit()
        # One message per call: the GUI shows a single dialog, so per-file
        # emissions would leave only the last one visible.
        if failures:
            message = '\n'.join(failures)
            if caveats:
                message += '\n\nAdded with a warning:\n' + '\n'.join(caveats)
            self.loadFailed.emit(message)
        elif caveats:
            self.loadWarning.emit('\n'.join(caveats))

    @Slot('QVariant', result='QVariantList')
    def suggestPolarizedChannels(self, paths) -> list:
        """Suggested spin-channel assignment for the selected files.

        Returns one ``{'path': ..., 'name': ..., 'channel': ...}`` row per file
        (``channel`` is '' when undetected) for the assignment dialog to edit.
        """
        paths = _from_qml(paths)
        if isinstance(paths, str):
            paths = paths.split(',')
        generalized = [IO.generalizePath(path) for path in paths]
        suggestion = self._project_logic.suggest_polarized_channel_assignment(generalized)
        return [
            {'path': path, 'name': os.path.basename(path), 'channel': channel}
            for path, channel in suggestion.items()
        ]

    @Slot('QVariant')
    def loadPolarized(self, assignments) -> None:
        """Load one polarized experiment from dialog rows ``[{'path','channel'},...]``.

        Rows with an empty channel are excluded ('not used' in the dialog). The
        assignment must be unambiguous: every remaining row needs an existing
        file and a known channel ('pp', 'pm', 'mp', 'mm'), and no channel may
        appear twice. Invalid input is rejected with a message rather than
        silently dropped — the dialog is not a trust boundary, and this slot is
        also called directly by tests and automation.

        Raises
        ------
        ValueError
            The assignment is malformed, incomplete or ambiguous.
        """
        assignments = _from_qml(assignments)
        channel_to_path = self._validated_channel_assignment(assignments)
        new_index, q_range_changed = self._project_logic.load_polarized_experiment(channel_to_path)
        self.experimentChanged.emit()
        self.externalExperimentChanged.emit()
        if q_range_changed:
            self.qRangeUpdated.emit()
        if new_index >= 0:
            # Show what was just imported: without this the new experiment is
            # only added to the list while the chart stays on the previous one.
            self.experimentLoaded.emit(new_index)

    def _validated_channel_assignment(self, assignments) -> dict:
        """Turn dialog rows into a validated ``{channel: path}`` mapping."""
        if not isinstance(assignments, (list, tuple)):
            self._reject_assignment(f'Expected a list of channel assignments, got {type(assignments).__name__}.')

        channel_to_path: dict = {}
        for row in assignments:
            row = _from_qml(row)
            if not isinstance(row, dict) or 'channel' not in row or 'path' not in row:
                self._reject_assignment(f"Malformed channel assignment row: {row!r} (expected 'path' and 'channel').")
            channel = (row['channel'] or '').strip()
            if not channel:
                # 'not used': the file is deliberately left out.
                continue
            if channel not in _CHANNELS:
                self._reject_assignment(
                    f"Unknown spin channel '{channel}'; expected one of {', '.join(_CHANNELS)}."
                )
            if channel in channel_to_path:
                self._reject_assignment(
                    f"Channel '{channel}' is assigned to more than one file; each channel needs exactly one file."
                )
            # Rows from `suggestPolarizedChannels` are already platform paths;
            # only a file:// URL (direct automation call) needs converting —
            # `generalizePath` is not idempotent on Windows (it would eat the
            # drive letter of an already-converted path).
            path = row['path'] or ''
            if path.startswith('file:'):
                path = IO.generalizePath(path)
            if not path or not os.path.isfile(path):
                self._reject_assignment(f"No such file for channel '{channel}': {row['path']!r}.")
            channel_to_path[channel] = path

        if not channel_to_path:
            self._reject_assignment('Assign at least one file to a spin channel.')
        return channel_to_path

    def _reject_assignment(self, message: str) -> None:
        """Report an invalid channel assignment and abort the load."""
        console.error(f'Polarized import rejected: {message}')
        self.loadFailed.emit(message)
        raise ValueError(message)
