"""Automatic saves against the real backend and the real file system.

`Project.autosave` is the single gate: it writes only when autosave is on, a project has been
created and changed, and no fit is running. Each automatic save first keeps the file it replaces
as `project.json.bak`. The checkpoints that call it are a page change (QML), the backend's
`checkpointRequested` signals (before a fit or an engine switch, after a successful run) and an
ORSO sample replacement (covered with the stub logic in test_py_project.py).
"""

import json
from pathlib import Path

import pytest
from easyscience import global_object

from EasyReflectometryApp.Backends.Py import py_backend as backend_module
from EasyReflectometryApp.Backends.Py.logic import fitting as fitting_module


@pytest.fixture(scope='module')
def _backend(qcore_application):
    # The library registers object names globally; another module's backend may still be alive.
    global_object.registry.clear()
    yield backend_module.PyBackend()
    global_object.registry.clear()


@pytest.fixture
def py_backend(_backend, qcore_application, tmp_path):
    """The shared backend with a freshly created, clean project in a temporary directory."""
    project = _backend._project
    project.reset()
    project.setAutosaveEnabled(True)
    project.setLocation(str(tmp_path / 'anything'))
    project.setName('AutosaveProject')
    project.create()
    qcore_application.processEvents()
    assert project.created is True
    assert project.hasUnsavedChanges is False
    yield _backend
    _backend._analysis._fitting_logic._running = False
    project.setAutosaveEnabled(True)


def _project_file(project) -> Path:
    return Path(project._logic.path_json)


def _backup_file(project) -> Path:
    return Path(project.backupPath)


def _on_disk(path: Path) -> dict:
    return json.loads(path.read_text(encoding='utf-8'))


def test_autosave_writes_a_changed_project_and_keeps_the_replaced_file(py_backend):
    project = py_backend._project
    saved = []
    project.projectSaved.connect(saved.append)
    before = _project_file(project).read_text(encoding='utf-8')
    project.setDescription('edited')

    assert project.autosave('test') is True

    assert project.hasUnsavedChanges is False
    assert project.lastSaveAutomatic is True
    assert project.lastSaved != ''
    assert saved == [str(_project_file(project))]
    assert _on_disk(_project_file(project))['info']['short_description'] == 'edited'
    assert _backup_file(project).read_text(encoding='utf-8') == before


def test_backup_holds_the_version_before_the_latest_automatic_save(py_backend):
    project = py_backend._project
    project.setDescription('first')
    project.autosave('test')
    project.setDescription('second')
    project.autosave('test')

    assert _on_disk(_backup_file(project))['info']['short_description'] == 'first'
    assert _on_disk(_project_file(project))['info']['short_description'] == 'second'


def test_a_manual_save_leaves_the_backup_alone(py_backend):
    project = py_backend._project
    project.setDescription('edited')

    project.save()

    assert project.lastSaveAutomatic is False
    assert not _backup_file(project).exists()


def test_autosave_does_nothing_for_an_unchanged_project(py_backend):
    project = py_backend._project
    saved = []
    project.projectSaved.connect(saved.append)

    assert project.autosave('test') is False

    assert saved == []
    assert not _backup_file(project).exists()


def test_autosave_does_nothing_before_a_project_is_created(py_backend):
    project = py_backend._project
    project.reset()
    project.setDescription('edited before any project exists')

    assert project.autosave('test') is False
    assert project.lastSaved == ''


def test_autosave_does_nothing_while_turned_off(py_backend):
    project = py_backend._project
    project.setAutosaveEnabled(False)
    project.setDescription('edited')

    assert project.autosave('test') is False
    assert project.hasUnsavedChanges is True


def test_turning_autosave_off_is_not_a_project_change(py_backend):
    project = py_backend._project

    project.setAutosaveEnabled(False)

    assert project.autosaveEnabled is False
    assert project.hasUnsavedChanges is False


def test_autosave_does_nothing_while_a_fit_is_running(py_backend):
    """The fit thread writes into the models a save would serialize."""
    project = py_backend._project
    project.setDescription('edited')
    py_backend._analysis._fitting_logic._running = True

    assert project.autosave('test') is False
    assert project.hasUnsavedChanges is True


def test_failures_are_reported_once_per_streak(py_backend, monkeypatch):
    project = py_backend._project
    errors = []
    project.autosaveError.connect(errors.append)

    def refuse(backup=False):
        raise PermissionError('locked')

    monkeypatch.setattr(project._logic, 'save', refuse)
    project.setDescription('edited')

    assert project.autosave('test') is False
    assert project.autosave('test') is False

    assert len(errors) == 1
    assert 'No permission to write' in errors[0]
    assert project.autosaveFailing is True
    assert project.hasUnsavedChanges is True

    monkeypatch.undo()
    assert project.autosave('test') is True
    assert project.autosaveFailing is False


def test_a_manual_save_ends_a_failure_streak(py_backend, monkeypatch):
    project = py_backend._project
    monkeypatch.setattr(project._logic, 'save', lambda backup=False: (_ for _ in ()).throw(OSError('disk')))
    project.setDescription('edited')
    project.autosave('test')
    assert project.autosaveFailing is True
    monkeypatch.undo()

    project.save()

    assert project.autosaveFailing is False


def test_a_backup_that_cannot_be_written_does_not_block_the_save(py_backend, monkeypatch):
    project = py_backend._project
    project.setDescription('edited')

    def broken_copy(*_args, **_kwargs):
        raise OSError('no space for the backup')

    monkeypatch.setattr('EasyReflectometryApp.Backends.Py.logic.project.shutil.copy2', broken_copy)

    assert project.autosave('test') is True
    assert _on_disk(_project_file(project))['info']['short_description'] == 'edited'
    assert not _backup_file(project).exists()
    assert list(_project_file(project).parent.glob('*.tmp')) == []


def _other_engine_index(analysis) -> int:
    available = analysis._calculators_logic.available()
    if len(available) < 2:
        pytest.skip('only one calculation engine is installed')
    current = analysis._calculators_logic.current_index()
    return next(index for index in range(len(available)) if index != current)


@pytest.mark.parametrize('page', ['sample', 'analysis'])
def test_switching_the_engine_saves_the_project_as_it_was(py_backend, page):
    project = py_backend._project
    analysis = py_backend._analysis
    old_engine = analysis._calculators_logic.available()[analysis._calculators_logic.current_index()]
    new_index = _other_engine_index(analysis)
    project.setDescription('edited before the switch')

    if page == 'sample':
        py_backend._sample.setCalculationEngineIndex(new_index)
    else:
        analysis.setCalculatorCurrentIndex(new_index)

    on_disk = _on_disk(_project_file(project))
    assert on_disk['info']['short_description'] == 'edited before the switch'
    assert on_disk['calculator'] == old_engine
    # The switch itself is the next unsaved change.
    assert project.hasUnsavedChanges is True


def test_selecting_the_current_engine_again_is_not_a_checkpoint(py_backend):
    project = py_backend._project
    project.setDescription('edited')

    py_backend._sample.setCalculationEngineIndex(py_backend._analysis._calculators_logic.current_index())

    assert project.hasUnsavedChanges is True


def test_starting_a_fit_saves_the_starting_point_first(py_backend, monkeypatch):
    project = py_backend._project
    analysis = py_backend._analysis
    order = []
    monkeypatch.setattr(analysis, '_prefit_errors', lambda: [])
    monkeypatch.setattr(analysis, '_start_threaded_fit', lambda: order.append(project.hasUnsavedChanges))
    project.setDescription('starting point')

    analysis.fittingStartStop()

    # The project was already clean on disk when the fit was started.
    assert order == [False]
    assert project.lastSaveAutomatic is True


def test_a_refused_fit_is_not_a_checkpoint(py_backend, monkeypatch):
    project = py_backend._project
    analysis = py_backend._analysis
    monkeypatch.setattr(analysis, '_prefit_errors', lambda: ['bad bounds'])
    project.setDescription('edited')

    analysis.fittingStartStop()

    assert project.hasUnsavedChanges is True


@pytest.mark.parametrize('success, saved', [(True, True), (False, False)])
def test_a_finished_fit_is_saved_only_when_it_succeeded(py_backend, monkeypatch, success, saved):
    project = py_backend._project
    analysis = py_backend._analysis
    fitting_logic = analysis._fitting_logic
    monkeypatch.setattr(fitting_logic, 'on_fit_finished', lambda _results: None)
    monkeypatch.setattr(fitting_logic, 'record_on_project', lambda _results: None)
    monkeypatch.setattr(fitting_module.Fitting, 'fit_success', property(lambda _self: success))
    project.setDescription('fitted values')

    analysis._on_fit_finished([])

    assert project.hasUnsavedChanges is (not saved)
    assert project.lastSaveAutomatic is saved


def test_a_failed_fit_is_not_a_checkpoint(py_backend):
    project = py_backend._project
    project.setDescription('edited')

    py_backend._analysis._on_fit_failed('diverged')

    assert project.hasUnsavedChanges is True
