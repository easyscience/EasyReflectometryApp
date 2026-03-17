import warnings

from EasyApp.Logic.Utils.Utils import generalizePath
from easyreflectometry import Project as ProjectLib
from easyreflectometry.orso_utils import load_orso_model
from orsopy.fileio import orso
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .logic.project import Project as ProjectLogic


class Project(QObject):
    createdChanged = Signal()
    nameChanged = Signal()
    descriptionChanged = Signal()
    locationChanged = Signal()

    externalCreatedChanged = Signal()
    externalNameChanged = Signal()
    externalProjectLoaded = Signal()
    externalProjectSaved = Signal()
    externalProjectReset = Signal()
    sampleLoadWarning = Signal(str)

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._logic = ProjectLogic(project_lib)

    # Properties

    @Property(bool, notify=createdChanged)
    def created(self) -> bool:
        return self._logic.created

    @Property(str, notify=createdChanged)
    def creationDate(self) -> str:
        return self._logic.creation_date

    @Property(str)
    def currentProjectPath(self) -> str:
        return self._logic.path

    # Properties with setters

    @Property(str, notify=nameChanged)
    def name(self) -> str:
        return self._logic.name

    @Slot(str)
    def setName(self, new_value: str) -> None:
        if self._logic.name != new_value:
            self._logic.name = new_value
            self.nameChanged.emit()
            self.externalNameChanged.emit()

    @Property(str, notify=descriptionChanged)
    def description(self) -> str:
        return self._logic.description

    @Slot(str)
    def setDescription(self, new_value: str) -> None:
        if self._logic.description != new_value:
            self._logic.description = new_value
            self.descriptionChanged.emit()

    @Property(str, notify=locationChanged)
    def location(self) -> str:
        return self._logic.root_path

    @Slot(str)
    def setLocation(self, new_value: str) -> None:
        if self._logic.root_path != new_value:
            self._logic.root_path = new_value
            self.locationChanged.emit()

    # Methods

    @Slot()
    def create(self) -> None:
        self._logic.create()
        self.createdChanged.emit()
        self.externalCreatedChanged.emit()

    @Slot(str)
    def load(self, path: str) -> None:
        self._logic.load(generalizePath(path))
        self.createdChanged.emit()
        self.nameChanged.emit()
        self.descriptionChanged.emit()
        self.locationChanged.emit()
        self.externalProjectLoaded.emit()

    @Slot()
    def save(self) -> None:
        self._logic.save()
        self.externalProjectSaved.emit()

    @Slot()
    def reset(self) -> None:
        self._logic.reset()
        self.createdChanged.emit()
        self.nameChanged.emit()
        self.descriptionChanged.emit()
        self.locationChanged.emit()
        self.externalCreatedChanged.emit()
        self.externalNameChanged.emit()
        self.externalProjectReset.emit()

    @Slot(str, bool)
    def sampleLoad(self, url: str, append: bool = True) -> None:
        # Load ORSO file content
        orso_data = orso.load_orso(generalizePath(url))
        # Load the sample model
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('always')
            sample = load_orso_model(orso_data)
        if sample is None:
            warning_msg = 'The ORSO file does not contain a valid sample model definition. No sample was loaded.'
            for w in caught_warnings:
                warning_msg = str(w.message)
            self.sampleLoadWarning.emit(warning_msg)
            return
        if append:
            # Add the sample as a new model in the project
            self._logic.add_sample_from_orso(sample)
        else:
            # Replace all existing models with the loaded sample
            self._logic.replace_models_from_orso(sample)
        # notify listeners
        self.externalProjectLoaded.emit()
