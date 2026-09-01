import os

from EasyApplication.Logic.Logging import console
from easyreflectometry import Project as ProjectLib
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
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


# Spin channels accepted by the polarized import, in canonical order.
_CHANNELS = ('pp', 'pm', 'mp', 'mm')


class Experiment(QObject):
    experimentChanged = Signal()
    externalExperimentChanged = Signal()
    qRangeUpdated = Signal()
    # Emitted with a user-facing message when an import is rejected.
    loadFailed = Signal(str)
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
            if self._project_logic.count_datasets_in_file(generalized) > 1:
                _count, changed = self._project_logic.load_all_experiments_from_file(generalized)
            else:
                changed = self._project_logic.load_new_experiment(generalized)
            if changed:
                q_range_changed = True
            self.experimentChanged.emit()
            self.externalExperimentChanged.emit()
        if q_range_changed:
            self.qRangeUpdated.emit()

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
