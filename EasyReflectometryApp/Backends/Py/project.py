import logging
import warnings
from contextlib import contextmanager
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

logger = logging.getLogger(__name__)


class Project(QObject):
    createdChanged = Signal()
    nameChanged = Signal()
    descriptionChanged = Signal()
    locationChanged = Signal()
    lastSavedChanged = Signal()
    hasUnsavedChangesChanged = Signal()

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
        self._has_unsaved_changes = False
        self._dirty_suspended = 0
        # Fingerprint of the project content as it was last known to match the disk (taken on
        # create, save, load and reset). None means "unknown", in which case a dirtying signal
        # is trusted as is.
        self._clean_fingerprint = None

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
        """ISO-8601 time of the last successful save, with UTC offset, or '' if never saved.

        This is the time of the last save made from this session, which is deliberately not
        the same as `creationDate` (the project's stored modification stamp). The value is
        left unformatted so that QML can render it with a locale-aware `Qt.formatTime`.
        """
        return self._last_saved

    @Property(bool, notify=hasUnsavedChangesChanged)
    def hasUnsavedChanges(self) -> bool:
        """Whether the project holds edits that `save()` would write to disk.

        Set from every backend signal that changes what the project file would contain (the
        inventory lives in `py_backend.DIRTYING_SIGNALS`) and from this object's own setters;
        cleared by create, save, load and reset. Always False while no project has been
        created, since there is nothing on disk for the edits to differ from.
        """
        return self._has_unsaved_changes

    # Properties with setters

    @Property(str, notify=nameChanged)
    def name(self) -> str:
        return self._logic.name

    @Slot(str)
    def setName(self, new_value: str) -> None:
        if self._logic.name != new_value:
            self._logic.name = new_value
            self.markDirty()
            self.nameChanged.emit()
            self.externalNameChanged.emit()

    @Property(str, notify=descriptionChanged)
    def description(self) -> str:
        return self._logic.description

    @Slot(str)
    def setDescription(self, new_value: str) -> None:
        if self._logic.description != new_value:
            self._logic.description = new_value
            self.markDirty()
            self.descriptionChanged.emit()

    @Property(str, notify=locationChanged)
    def location(self) -> str:
        return self._logic.root_path

    @Slot(str)
    def setLocation(self, new_value: str) -> None:
        if self._logic.root_path != new_value:
            self._logic.root_path = new_value
            self.markDirty()
            self.locationChanged.emit()

    # Methods

    @Slot()
    def markDirty(self) -> None:
        """Record that the project differs from the file on disk.

        Connected to every dirtying backend signal by `py_backend._connect_dirty_tracking`, and
        called directly by this object's setters.

        Ignored while no project has been created (nothing on disk to differ from, and `save()`
        refuses anyway) and while a create/load/reset is fanning out its own signals. The
        signals are a fast, over-approximate trigger: some fire on a mere selection change, and
        the sample's coalesced `constraintsChanged` fires one event-loop turn after the load
        that caused it. So the clean-to-edited transition is confirmed against the content
        fingerprint recorded at the last clean point, which costs one serialization per
        transition rather than one per signal.
        """
        if self._dirty_suspended or self._has_unsaved_changes:
            return
        if not self._logic.created:
            return
        if self._content_unchanged_since_clean():
            return
        self._has_unsaved_changes = True
        self.hasUnsavedChangesChanged.emit()

    def _content_unchanged_since_clean(self) -> bool:
        if self._clean_fingerprint is None:
            return False
        try:
            return self._logic.content_fingerprint() == self._clean_fingerprint
        except Exception:
            # A project that cannot be serialized right now cannot be proven unchanged; the
            # save path will report the actual problem.
            logger.debug('Could not fingerprint the project; treating it as changed', exc_info=True)
            return False

    def _record_clean_state(self) -> None:
        """Remember the current content as matching the disk and clear the flag."""
        try:
            self._clean_fingerprint = self._logic.content_fingerprint()
        except Exception:
            logger.debug('Could not fingerprint the project after a clean point', exc_info=True)
            self._clean_fingerprint = None
        self._clear_dirty()

    def _clear_dirty(self) -> None:
        if not self._has_unsaved_changes:
            return
        self._has_unsaved_changes = False
        self.hasUnsavedChangesChanged.emit()

    @contextmanager
    def _suspended_dirty_tracking(self):
        """Run a create/load/reset without its own relays marking the project dirty.

        Those relays run through the sample, experiment and analysis parts, which emit the very
        signals dirty tracking listens to. Suppressing them during the fan-out keeps the
        fan-out from fingerprinting the project once per signal. (Deferred emissions land after
        the block and are caught by the fingerprint check instead.)

        Suspending is all this does; clearing the flag is left to the callers, because only they
        know whether the change actually reached disk.
        """
        self._dirty_suspended += 1
        try:
            yield
        finally:
            self._dirty_suspended -= 1

    def _clear_last_saved(self) -> None:
        """Drop the save stamp when the project it referred to is gone (reset or load)."""
        if self._last_saved:
            self._last_saved = ''
            self.lastSavedChanged.emit()

    def _mark_saved(self) -> None:
        self._record_clean_state()
        # Aware stamp: unambiguous if it is ever logged or shown outside the local session.
        self._last_saved = datetime.now().astimezone().isoformat(timespec='seconds')
        self.lastSavedChanged.emit()
        self.projectSaved.emit(self._logic.path_json)

    def _save_error_message(self, exception: Exception) -> str:
        """Turn a save failure into a sentence a user can act on, keeping the raw text as detail.

        The library raises rather than prints, so these are the failures that actually reach the
        GUI. The previously saved file is always intact.
        """
        path = self._logic.path_json
        if isinstance(exception, FileExistsError):
            # Only create() can raise this (save() overwrites): the project directory is taken.
            explanation = f'A project already exists at "{self._logic.path}".\nChoose a different name or location.'
        elif isinstance(exception, PermissionError):
            explanation = f'No permission to write "{path}".\nThe file may be read-only or open in another program.'
        elif isinstance(exception, (TypeError, ValueError)):
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
        # signals. It can fail on a colliding path, which the library raises instead of printing.
        error = None
        with self._suspended_dirty_tracking():
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
        path = IO.generalizePath(path)
        try:
            self._logic.load(path)
        except FileNotFoundError:
            self.projectLoadError.emit(f'The project file "{path}" does not exist.')
            return
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
        except OSError as ex:
            self.projectLoadError.emit(f'The project file "{path}" could not be read.\n\nDetails: {ex}')
            return
        self._clear_last_saved()
        # The fingerprint is taken before the fan-out: whatever the relays emit, now or on a
        # later event-loop turn, is compared against the state that was just loaded.
        self._record_clean_state()
        with self._suspended_dirty_tracking():
            self.createdChanged.emit()
            self.nameChanged.emit()
            self.descriptionChanged.emit()
            self.locationChanged.emit()
            self.externalProjectLoaded.emit()
        self._clear_dirty()

    @Slot()
    def save(self) -> None:
        if not self._logic.created:
            # Nothing has been created, so there is no project file of our own to update; saving
            # would write the in-memory defaults over whatever sits at the current path.
            self.projectSaveError.emit('No project has been created yet.\nCreate or open a project before saving.')
            return
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
        self._record_clean_state()
        with self._suspended_dirty_tracking():
            self.createdChanged.emit()
            self.nameChanged.emit()
            self.descriptionChanged.emit()
            self.locationChanged.emit()
            self.externalCreatedChanged.emit()
            self.externalNameChanged.emit()
            self.externalProjectReset.emit()
        self._clear_dirty()

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
        # An imported sample is project content, unlike the project loads this signal otherwise
        # announces; marked here rather than left to the relay's incidental table signals.
        self.markDirty()
        # notify listeners
        self.externalProjectLoaded.emit()
