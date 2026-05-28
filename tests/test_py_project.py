import warnings

from EasyReflectometryApp.Backends.Py import project as project_module


class StubProjectLogic:
    def __init__(self, _project_lib):
        self.created = False
        self.creation_date = '2026-03-22'
        self.path = 'project.json'
        self.name = 'Demo'
        self.description = 'Desc'
        self.root_path = 'C:/work'
        self.created_calls = 0
        self.loaded_paths = []
        self.saved_calls = 0
        self.reset_calls = 0
        self.added_samples = []
        self.replaced_samples = []

    def create(self):
        self.created_calls += 1
        self.created = True

    def load(self, path):
        self.loaded_paths.append(path)

    def save(self):
        self.saved_calls += 1

    def reset(self):
        self.reset_calls += 1

    def add_sample_from_orso(self, sample):
        self.added_samples.append(sample)

    def replace_models_from_orso(self, sample):
        self.replaced_samples.append(sample)


def _build_project(monkeypatch):
    monkeypatch.setattr(project_module, 'ProjectLogic', StubProjectLogic)
    return project_module.Project(project_lib=object())


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
