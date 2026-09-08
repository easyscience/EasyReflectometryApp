import warnings
from datetime import datetime

from easyreflectometry import Project as ProjectLib
from easyreflectometry.orso_utils import load_orso_model
from orsopy.fileio import orso
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .helpers import IO
from .logic.project import Project as ProjectLogic


class Project(QObject):
    createdChanged = Signal()
    nameChanged = Signal()
    descriptionChanged = Signal()
    locationChanged = Signal()
    lastSavedChanged = Signal()

    externalCreatedChanged = Signal()
    externalNameChanged = Signal()
    externalProjectLoaded = Signal()
    externalProjectReset = Signal()
    sampleLoadWarning = Signal(str)
    projectLoadError = Signal(str)
    projectSaved = Signal(str)
    projectSaveError = Signal(str)

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._logic = ProjectLogic(project_lib)
        self._last_saved = ''

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

    @Property(str, notify=lastSavedChanged)
    def lastSaved(self) -> str:
        """ISO-8601 wall-clock time of the last successful save, or '' if never saved.

        This is the time of the last save made from this session, which is deliberately not
        the same as `creationDate` (the project's stored modification stamp). The value is
        left unformatted so that QML can render it with a locale-aware `Qt.formatTime`.
        """
        return self._last_saved

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

    def _clear_last_saved(self) -> None:
        """Drop the save stamp when the project it referred to is gone (reset or load)."""
        if self._last_saved:
            self._last_saved = ''
            self.lastSavedChanged.emit()

    def _mark_saved(self) -> None:
        self._last_saved = datetime.now().isoformat(timespec='seconds')
        self.lastSavedChanged.emit()
        self.projectSaved.emit(self._logic.path_json)

    def _save_error_message(self, exception: Exception) -> str:
        """Turn a save failure into a sentence a user can act on, keeping the raw text as detail.

        The library raises rather than prints since the atomic-save change, so these are the
        failures that actually reach the GUI. The previously saved file is always intact.
        """
        path = self._logic.path_json
        if isinstance(exception, FileExistsError):
            explanation = f'A project already exists at "{path}".\nChoose a different name or location.'
        elif isinstance(exception, PermissionError):
            explanation = f'No permission to write "{path}".\nThe file may be read-only or open in another program.'
        elif isinstance(exception, ValueError):
            # Raised while serializing, e.g. a constraint that depends on a parameter which is
            # not reachable from the models.
            explanation = f'The project could not be saved to "{path}" because it cannot be serialized.'
        elif isinstance(exception, OSError):
            explanation = f'The project could not be written to "{path}".'
        else:
            return f'Failed to save the project to "{path}".\n\n{exception}'
        return f'{explanation}\n\nDetails: {exception}'

    @Slot()
    def create(self) -> None:
        # create() writes the project file, so it is a first save and reports through the same
        # signals. It can fail on a colliding path, which the library now raises instead of
        # printing.
        error = None
        try:
            self._logic.create()
        except Exception as ex:
            error = self._save_error_message(ex)
        # Emitted either way, so that the UI reflects the real `created` state even when the
        # directories were made but the file was not written.
        self.createdChanged.emit()
        self.externalCreatedChanged.emit()
        if error is not None:
            self.projectSaveError.emit(error)
        else:
            self._mark_saved()

    @Slot(str)
    def load(self, path: str) -> None:
        try:
            self._logic.load(IO.generalizePath(path))
        except ValueError as ex:
            # easyreflectometry rejects project files whose file_format predates
            # the current schema. Show a user-facing message for that case and
            # surface any other unreadable-JSON error verbatim, rather than
            # letting it propagate uncaught.
            if 'file_format' in str(ex):
                message = (
                    'This project file uses obsolete and unsupported format.\n'
                    'Please re-create the project from its underlying data and save it again.'
                )
            else:
                message = str(ex)
            self.projectLoadError.emit(message)
            return
        self._clear_last_saved()
        self.createdChanged.emit()
        self.nameChanged.emit()
        self.descriptionChanged.emit()
        self.locationChanged.emit()
        self.externalProjectLoaded.emit()

    @Slot()
    def save(self) -> None:
        # The whole call is guarded: the library's unlink-free atomic save raises, and a locked
        # destination raises out of os.replace, so nothing may escape into this slot uncaught.
        try:
            self._logic.save()
        except Exception as ex:
            self.projectSaveError.emit(self._save_error_message(ex))
            return
        self._mark_saved()

    @Slot()
    def reset(self) -> None:
        self._logic.reset()
        self._clear_last_saved()
        self.createdChanged.emit()
        self.nameChanged.emit()
        self.descriptionChanged.emit()
        self.locationChanged.emit()
        self.externalCreatedChanged.emit()
        self.externalNameChanged.emit()
        self.externalProjectReset.emit()

    @Slot(str, bool)
    def sampleLoad(self, url: str, append: bool = True) -> None:
        try:
            orso_data = orso.load_orso(IO.generalizePath(url))
        except Exception as ex:
            self.projectLoadError.emit(f'Failed to load ORSO file: {ex}')
            return
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
