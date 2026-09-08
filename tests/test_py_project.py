import warnings
from datetime import datetime

import pytest

from EasyReflectometryApp.Backends.Py import project as project_module


class StubProjectLogic:
    def __init__(self, _project_lib):
        self.created = False
        self.creation_date = '2026-03-22'
        self.path = 'C:/tmp/demo-project'
        self.path_json = 'project.json'
        self.name = 'Demo'
        self.description = 'Desc'
        self.root_path = 'C:/work'
        self.created_calls = 0
        self.loaded_paths = []
        self.saved_calls = 0
        self.reset_calls = 0
        self.added_samples = []
        self.replaced_samples = []
        # Stands in for the model/experiment content the real fingerprint covers.
        self.content_version = 0

    def content_fingerprint(self) -> str:
        return f'{self.name}|{self.description}|{self.root_path}|{self.content_version}'

    def create(self):
        self.created_calls += 1
        self.created = True

    def load(self, path):
        self.loaded_paths.append(path)
        self.created = True

    def save(self):
        self.saved_calls += 1

    def reset(self):
        self.reset_calls += 1
        self.created = False

    def add_sample_from_orso(self, sample):
        self.added_samples.append(sample)
        self.content_version += 1

    def replace_models_from_orso(self, sample):
        self.replaced_samples.append(sample)
        self.content_version += 1


def _build_project(monkeypatch, created=False):
    monkeypatch.setattr(project_module, 'ProjectLogic', StubProjectLogic)
    project = project_module.Project(project_lib=object())
    if created:
        project.create()
    return project


def test_setters_emit_only_on_change(monkeypatch, qcore_application):
    project = _build_project(monkeypatch)
    counts = {'name': 0, 'external_name': 0, 'description': 0, 'location': 0}
    project.nameChanged.connect(lambda: counts.__setitem__('name', counts['name'] + 1))
    project.externalNameChanged.connect(lambda: counts.__setitem__('external_name', counts['external_name'] + 1))
    project.descriptionChanged.connect(lambda: counts.__setitem__('description', counts['description'] + 1))
    project.locationChanged.connect(lambda: counts.__setitem__('location', counts['location'] + 1))

    project.setName('Demo')
    project.setDescription('Desc')
    project.setLocation('C:/work')
    assert counts == {'name': 0, 'external_name': 0, 'description': 0, 'location': 0}

    project.setName('Updated')
    project.setDescription('Updated Desc')
    project.setLocation('D:/new')
    assert counts == {'name': 1, 'external_name': 1, 'description': 1, 'location': 1}


def test_load_create_reset_and_signals(monkeypatch, qcore_application):
    project = _build_project(monkeypatch)
    monkeypatch.setattr(project_module.IO, 'generalizePath', lambda path: f'gen:{path}')

    counts = {'created': 0, 'external_created': 0, 'external_loaded': 0, 'external_reset': 0}
    project.createdChanged.connect(lambda: counts.__setitem__('created', counts['created'] + 1))
    project.externalCreatedChanged.connect(lambda: counts.__setitem__('external_created', counts['external_created'] + 1))
    project.externalProjectLoaded.connect(lambda: counts.__setitem__('external_loaded', counts['external_loaded'] + 1))
    project.externalProjectReset.connect(lambda: counts.__setitem__('external_reset', counts['external_reset'] + 1))

    project.create()
    project.load('in.json')
    project.save()
    project.reset()

    assert project._logic.created_calls == 1
    assert project._logic.loaded_paths == ['gen:in.json']
    assert project._logic.saved_calls == 1
    assert project._logic.reset_calls == 1
    assert counts == {'created': 3, 'external_created': 2, 'external_loaded': 1, 'external_reset': 1}


def test_sample_load_append_and_replace(monkeypatch, qcore_application):
    project = _build_project(monkeypatch)
    monkeypatch.setattr(project_module.IO, 'generalizePath', lambda path: f'gen:{path}')
    monkeypatch.setattr(project_module.orso, 'load_orso', lambda path: f'orso:{path}')
    monkeypatch.setattr(project_module, 'load_orso_model', lambda _orso_data: 'sample-model')

    loaded = {'count': 0}
    project.externalProjectLoaded.connect(lambda: loaded.__setitem__('count', loaded['count'] + 1))

    project.sampleLoad('sample.orso', append=True)
    project.sampleLoad('sample.orso', append=False)

    assert project._logic.added_samples == ['sample-model']
    assert project._logic.replaced_samples == ['sample-model']
    assert loaded['count'] == 2


def test_sample_load_marks_the_project_dirty(monkeypatch, qcore_application):
    """An imported sample is content to save, even though the relay signal it emits is not
    classified as dirtying (it is the same one a project load uses)."""
    project = _build_project(monkeypatch, created=True)
    monkeypatch.setattr(project_module.IO, 'generalizePath', lambda path: path)
    monkeypatch.setattr(project_module.orso, 'load_orso', lambda path: 'orso-data')
    monkeypatch.setattr(project_module, 'load_orso_model', lambda _orso_data: 'sample-model')
    assert project.hasUnsavedChanges is False

    project.sampleLoad('sample.orso', append=True)

    assert project.hasUnsavedChanges is True


def test_sample_load_emits_warning_when_model_missing(monkeypatch, qcore_application):
    project = _build_project(monkeypatch)
    monkeypatch.setattr(project_module.IO, 'generalizePath', lambda path: path)
    monkeypatch.setattr(project_module.orso, 'load_orso', lambda _path: 'orso-data')

    def _warn_and_return_none(_orso_data):
        warnings.warn('Missing model in ORSO', stacklevel=1)
        return None

    monkeypatch.setattr(project_module, 'load_orso_model', _warn_and_return_none)

    received = []
    project.sampleLoadWarning.connect(lambda msg: received.append(msg))

    project.sampleLoad('sample.orso')

    assert project._logic.added_samples == []
    assert project._logic.replaced_samples == []
    assert received == ['Missing model in ORSO']


def test_load_emits_error_on_outdated_file_format(monkeypatch, qcore_application):
    project = _build_project(monkeypatch)
    monkeypatch.setattr(project_module.IO, 'generalizePath', lambda path: path)

    def _raise_format_error(_path):
        raise ValueError('This project file predates file_format=2 and cannot be loaded.')

    monkeypatch.setattr(project._logic, 'load', _raise_format_error)

    errors = []
    project.projectLoadError.connect(lambda msg: errors.append(msg))
    loaded = {'count': 0}
    project.externalProjectLoaded.connect(lambda: loaded.__setitem__('count', loaded['count'] + 1))

    project.load('old_project.json')

    assert errors == [
        'This project file uses obsolete and unsupported format.\n'
        'Please re-create the project from its underlying data and save it again.'
    ]
    assert loaded['count'] == 0


@pytest.mark.parametrize(
    ('exception', 'expected_fragment'),
    [
        (FileNotFoundError('nowhere/project.json'), 'does not exist'),
        (PermissionError('denied'), 'could not be read'),
    ],
)
def test_load_reports_file_system_failures(monkeypatch, qcore_application, exception, expected_fragment):
    """The library raises for a missing or unreadable file; the slot must report, not propagate."""
    project = _build_project(monkeypatch)
    monkeypatch.setattr(project_module.IO, 'generalizePath', lambda path: path)

    def _raise(_path):
        raise exception

    monkeypatch.setattr(project._logic, 'load', _raise)
    errors = []
    project.projectLoadError.connect(lambda msg: errors.append(msg))
    loaded = {'count': 0}
    project.externalProjectLoaded.connect(lambda: loaded.__setitem__('count', loaded['count'] + 1))

    project.load('nowhere/project.json')

    assert len(errors) == 1
    assert expected_fragment in errors[0]
    assert 'nowhere/project.json' in errors[0]
    assert loaded['count'] == 0


def _spy_save_signals(project):
    saved = []
    errors = []
    stamps = []
    project.projectSaved.connect(lambda path: saved.append(path))
    project.projectSaveError.connect(lambda msg: errors.append(msg))
    project.lastSavedChanged.connect(lambda: stamps.append(project.lastSaved))
    return saved, errors, stamps


def test_save_emits_projectSaved_and_stamps_last_saved(monkeypatch, qcore_application):
    project = _build_project(monkeypatch)
    project._logic.created = True
    saved, errors, stamps = _spy_save_signals(project)

    assert project.lastSaved == ''

    project.save()

    assert saved == ['project.json']
    assert errors == []
    assert len(stamps) == 1
    assert project.lastSaved != ''
    # An aware stamp is unambiguous wherever it ends up; QML parses the offset correctly.
    assert datetime.fromisoformat(project.lastSaved).tzinfo is not None


def test_save_refuses_when_no_project_has_been_created(monkeypatch, qcore_application):
    """Saving before a create would write the defaults over whatever sits at the current path."""
    project = _build_project(monkeypatch)
    saved, errors, stamps = _spy_save_signals(project)

    project.save()

    assert project._logic.saved_calls == 0
    assert saved == []
    assert stamps == []
    assert len(errors) == 1
    assert 'No project has been created' in errors[0]


def test_save_emits_error_and_leaves_last_saved_untouched(monkeypatch, qcore_application):
    project = _build_project(monkeypatch)
    project._logic.created = True

    def _raise_permission_error():
        raise PermissionError('project.json is open in another program')

    monkeypatch.setattr(project._logic, 'save', _raise_permission_error)
    saved, errors, stamps = _spy_save_signals(project)

    project.save()

    assert saved == []
    assert stamps == []
    assert project.lastSaved == ''
    assert len(errors) == 1
    assert 'No permission to write "project.json"' in errors[0]
    assert 'open in another program' in errors[0]


@pytest.mark.parametrize(
    'exception',
    [
        ValueError('constraint depends on an unreachable parameter'),
        TypeError('Object of type float32 is not JSON serializable'),
    ],
)
def test_save_reports_serialization_failure(monkeypatch, qcore_application, exception):
    project = _build_project(monkeypatch)
    project._logic.created = True

    def _raise():
        raise exception

    monkeypatch.setattr(project._logic, 'save', _raise)
    _saved, errors, _stamps = _spy_save_signals(project)

    project.save()

    assert len(errors) == 1
    assert 'cannot be serialized' in errors[0]
    assert str(exception) in errors[0]


def test_create_reports_save_through_the_same_signals(monkeypatch, qcore_application):
    project = _build_project(monkeypatch)
    saved, errors, _stamps = _spy_save_signals(project)

    project.create()

    assert saved == ['project.json']
    assert errors == []
    assert project.lastSaved != ''


def test_create_emits_error_when_the_project_directory_already_exists(monkeypatch, qcore_application):
    project = _build_project(monkeypatch)

    def _raise_file_exists():
        raise FileExistsError('Directory C:/tmp/demo-project already exists')

    monkeypatch.setattr(project._logic, 'create', _raise_file_exists)
    saved, errors, _stamps = _spy_save_signals(project)
    created_counts = {'created': 0}
    project.createdChanged.connect(lambda: created_counts.__setitem__('created', created_counts['created'] + 1))

    project.create()

    assert saved == []
    assert project.lastSaved == ''
    assert len(errors) == 1
    # Names the directory, which is what collided, and tells the user what to change.
    assert 'A project already exists at "C:/tmp/demo-project"' in errors[0]
    assert 'Choose a different name or location' in errors[0]
    # The UI is still told to re-read `created`, so it reflects the real state after a failure.
    assert created_counts['created'] == 1


def test_reset_and_load_clear_the_last_saved_stamp(monkeypatch, qcore_application):
    project = _build_project(monkeypatch, created=True)
    monkeypatch.setattr(project_module.IO, 'generalizePath', lambda path: path)

    project.save()
    assert project.lastSaved != ''
    project.reset()
    assert project.lastSaved == ''

    project.load('other.json')
    project.save()
    assert project.lastSaved != ''
    project.load('other.json')
    assert project.lastSaved == ''


def test_lifecycle_leaves_the_project_clean(monkeypatch, qcore_application):
    project = _build_project(monkeypatch)
    monkeypatch.setattr(project_module.IO, 'generalizePath', lambda path: path)
    # Stand in for the relays that run while a project is created, loaded or reset: they emit the
    # very signals dirty tracking listens to, and must not leave the project looking edited.
    project.externalCreatedChanged.connect(project.markDirty)
    project.externalProjectLoaded.connect(project.markDirty)
    project.externalProjectReset.connect(project.markDirty)

    project.create()
    assert project.hasUnsavedChanges is False

    project.setName('Edited')
    assert project.hasUnsavedChanges is True
    project.save()
    assert project.hasUnsavedChanges is False

    project.setName('Edited again')
    project.load('other.json')
    assert project.hasUnsavedChanges is False

    project.setName('Edited once more')
    project.reset()
    assert project.hasUnsavedChanges is False


def test_deferred_relay_after_a_load_does_not_dirty(monkeypatch, qcore_application):
    """The sample relays part of a load through a 0 ms timer, so a dirtying signal can land after
    the load has finished and cleared the flag. It carries no edit, so it must not count."""
    project = _build_project(monkeypatch)
    monkeypatch.setattr(project_module.IO, 'generalizePath', lambda path: path)

    project.load('other.json')
    assert project.hasUnsavedChanges is False

    project.markDirty()  # what the timer's constraintsChanged does once the event loop turns

    assert project.hasUnsavedChanges is False


def test_signal_that_changes_nothing_does_not_dirty_but_a_real_edit_does(monkeypatch, qcore_application):
    """Selection changes emit the same signals as edits; only content decides."""
    project = _build_project(monkeypatch, created=True)

    project.markDirty()
    assert project.hasUnsavedChanges is False

    project._logic.content_version += 1
    project.markDirty()
    assert project.hasUnsavedChanges is True


def test_project_that_cannot_be_fingerprinted_is_treated_as_changed(monkeypatch, qcore_application):
    project = _build_project(monkeypatch, created=True)

    def _raise():
        raise ValueError('constraint depends on an unreachable parameter')

    monkeypatch.setattr(project._logic, 'content_fingerprint', _raise)

    project.markDirty()

    assert project.hasUnsavedChanges is True


def test_failed_save_keeps_the_project_dirty(monkeypatch, qcore_application):
    """The edits are still only in memory, so the close prompt must keep firing."""
    project = _build_project(monkeypatch, created=True)

    def _raise_permission_error():
        raise PermissionError('locked')

    monkeypatch.setattr(project._logic, 'save', _raise_permission_error)
    project.setName('Edited')
    assert project.hasUnsavedChanges is True

    project.save()

    assert project.hasUnsavedChanges is True


def test_edits_before_a_create_are_not_unsaved_changes(monkeypatch, qcore_application):
    """Before a create there is nothing on disk for the edits to differ from, so neither the
    Save button nor the close prompt has anything to offer. In particular a failed create must
    not leave a "dirty" project whose "Save and exit" would overwrite the colliding one."""
    project = _build_project(monkeypatch)
    project.setName('Edited')
    assert project.hasUnsavedChanges is False

    def _raise_file_exists():
        raise FileExistsError('collision')

    monkeypatch.setattr(project._logic, 'create', _raise_file_exists)
    project.create()

    assert project.created is False
    assert project.hasUnsavedChanges is False


def test_unsaved_changes_notifies_only_on_transitions(monkeypatch, qcore_application):
    project = _build_project(monkeypatch, created=True)
    changes = []
    project.hasUnsavedChangesChanged.connect(lambda: changes.append(project.hasUnsavedChanges))

    project.setName('One')
    project.setDescription('Two')
    project.setLocation('D:/three')
    assert changes == [True]

    project.save()
    assert changes == [True, False]
