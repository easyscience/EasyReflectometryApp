import os

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


class Experiment(QObject):
    experimentChanged = Signal()
    externalExperimentChanged = Signal()
    qRangeUpdated = Signal()

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

        Rows with an empty channel are skipped; duplicate channels are invalid
        and ignored here (the dialog prevents them).
        """
        assignments = _from_qml(assignments)
        channel_to_path = {}
        for row in assignments:
            channel = row['channel']
            if channel:
                channel_to_path[channel] = row['path']
        if not channel_to_path:
            return
        q_range_changed = self._project_logic.load_polarized_experiment(channel_to_path)
        self.experimentChanged.emit()
        self.externalExperimentChanged.emit()
        if q_range_changed:
            self.qRangeUpdated.emit()
