"""Dirty tracking against the real backend.

Two layers are under test. The inventory (`DIRTYING_SIGNALS`): a mutation path whose signal is
missing from it leaves `hasUnsavedChanges` False, so the close prompt never fires and the user's
work is discarded silently; `test_every_external_signal_is_classified` makes that hard to do by
accident. And the content check behind the flag: the signals over-approximate (a selection change
emits the same ones as an edit, and the sample relays `layersChange` into `constraintsChanged`
through a 0 ms timer, so a load's own fan-out lands after the load has finished), so the flag
only flips when the project content actually differs from the last clean state.

The event-loop tests here are the ones that matter: a synchronous check passes while a freshly
loaded project turns dirty one `processEvents()` later.
"""

import pytest
from PySide6.QtCore import QMetaMethod
from PySide6.QtCore import Signal

from EasyReflectometryApp.Backends.Py import py_backend as backend_module
from EasyReflectometryApp.Backends.Py.analysis import Analysis
from EasyReflectometryApp.Backends.Py.experiment import Experiment
from EasyReflectometryApp.Backends.Py.project import Project
from EasyReflectometryApp.Backends.Py.sample import Sample

PART_CLASSES = {
    '_project': Project,
    '_sample': Sample,
    '_experiment': Experiment,
    '_analysis': Analysis,
}


def _signal_names(cls) -> set:
    return {name for name, value in vars(cls).items() if isinstance(value, Signal)}


_ARGUMENT_DEFAULTS = {'int': 0, 'double': 0.0, 'float': 0.0, 'QString': '', 'bool': False}


def _emit(owner, signal_name: str) -> None:
    """Emit a signal without caring what it carries; only the connection is under test."""
    meta_object = owner.metaObject()
    for index in range(meta_object.methodCount()):
        method = meta_object.method(index)
        if method.methodType() != QMetaMethod.MethodType.Signal:
            continue
        if bytes(method.name()).decode() != signal_name:
            continue
        argument_types = [bytes(parameter).decode() for parameter in method.parameterTypes()]
        getattr(owner, signal_name).emit(*(_ARGUMENT_DEFAULTS[each] for each in argument_types))
        return
    raise AssertionError(f'{type(owner).__name__} exposes no signal {signal_name} to Qt')


@pytest.fixture(scope='module')
def _backend(qcore_application):
    return backend_module.PyBackend()


@pytest.fixture
def py_backend(_backend, qcore_application, tmp_path):
    """The shared backend with a freshly created, clean project in a temporary directory."""
    project = _backend._project
    project.reset()
    # setLocation takes the parent of what it is given; the project ends up at tmp_path/<name>.
    project.setLocation(str(tmp_path / 'anything'))
    project.setName('DirtyTrackingProject')
    project.create()
    qcore_application.processEvents()
    assert project.created is True
    assert project.hasUnsavedChanges is False
    return _backend


def _forget_clean_state(project) -> None:
    """Make the next dirtying signal count regardless of content: the connection is under test."""
    project._clear_dirty()
    project._clean_fingerprint = None


def test_every_external_signal_is_classified():
    """A new external* signal must be declared as dirtying or explicitly excluded.

    This fails when someone adds one and wires it nowhere, which is the failure mode that costs
    a user their unsaved fit.
    """
    for part_name, cls in PART_CLASSES.items():
        external = {name for name in _signal_names(cls) if name.startswith('external')}
        classified = set(backend_module.DIRTYING_SIGNALS.get(part_name, ())) | set(
            backend_module.NON_DIRTYING_EXTERNAL_SIGNALS.get(part_name, ())
        )
        unclassified = external - classified
        assert not unclassified, (
            f'{cls.__name__} signal(s) {sorted(unclassified)} are neither in DIRTYING_SIGNALS nor '
            f'in NON_DIRTYING_EXTERNAL_SIGNALS. Decide whether they change what save() writes.'
        )


def test_declared_signals_exist_on_their_backend_part():
    """Guards against a rename silently emptying the inventory."""
    for mapping in (backend_module.DIRTYING_SIGNALS, backend_module.NON_DIRTYING_EXTERNAL_SIGNALS):
        for part_name, signal_names in mapping.items():
            cls = PART_CLASSES[part_name]
            missing = set(signal_names) - _signal_names(cls)
            assert not missing, f'{cls.__name__} has no signal(s) {sorted(missing)}'


@pytest.mark.parametrize(
    ('part_name', 'signal_name'),
    [(part, signal) for part, signals in backend_module.DIRTYING_SIGNALS.items() for signal in signals],
)
def test_each_dirtying_signal_is_connected(py_backend, part_name, signal_name):
    """Emitting the signal on a real backend must set the flag — proves the connection exists."""
    project = py_backend._project
    _forget_clean_state(project)
    assert project.hasUnsavedChanges is False

    _emit(getattr(py_backend, part_name), signal_name)

    assert project.hasUnsavedChanges is True, f'{part_name}.{signal_name} does not mark the project dirty'


def test_setters_mark_a_created_project_dirty(py_backend):
    project = py_backend._project

    project.setName('A new name')
    assert project.hasUnsavedChanges is True

    project._record_clean_state()
    project.setDescription('A new description')
    assert project.hasUnsavedChanges is True


def test_setter_that_changes_nothing_does_not_dirty(py_backend):
    project = py_backend._project

    project.setName(project.name)
    project.setDescription(project.description)

    assert project.hasUnsavedChanges is False


# --- Lifecycle: clean now, and still clean once the event loop has turned -----------------------


def test_create_stays_clean_after_the_event_loop_turns(py_backend, qcore_application):
    project = py_backend._project
    # The fixture created the project and turned the loop once already; turn it again to be sure
    # nothing is still pending.
    qcore_application.processEvents()
    assert project.hasUnsavedChanges is False


def test_reset_stays_clean_after_the_event_loop_turns(py_backend, qcore_application):
    project = py_backend._project
    py_backend._sample.setCurrentMaterialSld(1.234)
    assert project.hasUnsavedChanges is True

    project.reset()
    assert project.hasUnsavedChanges is False
    qcore_application.processEvents()

    assert project.hasUnsavedChanges is False


def test_load_stays_clean_after_the_event_loop_turns(py_backend, qcore_application):
    project = py_backend._project
    path_json = project._logic.path_json
    py_backend._sample.setCurrentMaterialSld(1.234)
    project.save()
    assert project.hasUnsavedChanges is False

    py_backend._sample.setCurrentMaterialSld(5.678)
    assert project.hasUnsavedChanges is True
    project.load(path_json)
    assert project.hasUnsavedChanges is False
    qcore_application.processEvents()

    assert project.hasUnsavedChanges is False
    assert project.created is True


def test_load_of_a_missing_file_reports_and_keeps_the_project(py_backend, qcore_application, tmp_path):
    project = py_backend._project
    errors = []
    project.projectLoadError.connect(lambda message: errors.append(message))

    project.load(str(tmp_path / 'nowhere' / 'project.json'))

    assert len(errors) == 1
    assert 'does not exist' in errors[0]
    assert project.created is True
    assert project.name == 'DirtyTrackingProject'


# --- Selection is not content ------------------------------------------------------------------


def test_selecting_a_model_assembly_or_layer_does_not_dirty(py_backend, qcore_application):
    project = py_backend._project
    sample = py_backend._sample
    sample.addNewModel()
    assert project.hasUnsavedChanges is True
    project.save()
    assert project.hasUnsavedChanges is False

    sample.setCurrentModelIndex(1)
    sample.setCurrentModelIndex(0)
    sample.setCurrentAssemblyIndex(1)
    sample.setCurrentAssemblyIndex(0)
    sample.setCurrentLayerIndex(0)
    qcore_application.processEvents()

    assert project.hasUnsavedChanges is False


def test_selecting_an_experiment_does_not_dirty(py_backend, qcore_application):
    project = py_backend._project
    analysis = py_backend._analysis

    analysis.setExperimentCurrentIndex(0)
    analysis.setSelectedExperimentIndices([])
    py_backend.analysisSetSelectedExperimentIndices([0])
    qcore_application.processEvents()

    assert project.hasUnsavedChanges is False


# --- Edits are content ---------------------------------------------------------------------------


def test_renaming_a_layer_dirties_immediately(py_backend):
    """Persisted in the project file, and tracked on its own rather than through the deferred
    constraints relay."""
    project = py_backend._project

    py_backend._sample.setCurrentLayerName('Renamed layer')

    assert project.hasUnsavedChanges is True


def test_renaming_a_layer_by_index_dirties_immediately(py_backend):
    project = py_backend._project

    py_backend._sample.setLayerNameAtIndex(0, 'Renamed layer')

    assert project.hasUnsavedChanges is True


@pytest.mark.parametrize(
    'edit',
    [
        lambda backend: backend._sample.setCurrentAssemblyName('Renamed assembly'),
        lambda backend: backend._sample.setCurrentMaterialSld(1.234),
        lambda backend: backend._sample.addNewModel(),
        lambda backend: backend._project.setDescription('A new description'),
    ],
    ids=['assembly rename', 'material sld', 'add model', 'description'],
)
def test_content_edits_dirty(py_backend, edit):
    project = py_backend._project

    edit(py_backend)

    assert project.hasUnsavedChanges is True


def test_save_records_the_new_clean_state(py_backend, qcore_application):
    project = py_backend._project
    py_backend._sample.setCurrentMaterialSld(1.234)
    project.save()
    assert project.hasUnsavedChanges is False

    # The same signals again, without an edit: still clean.
    py_backend._sample.setCurrentAssemblyIndex(0)
    qcore_application.processEvents()
    assert project.hasUnsavedChanges is False

    # A further edit: dirty again.
    py_backend._sample.setCurrentMaterialSld(2.345)
    assert project.hasUnsavedChanges is True


# --- The save path itself ------------------------------------------------------------------------


def test_save_succeeds_with_a_newly_added_or_duplicated_model_selected(py_backend):
    """A model added through the collection had no calculator interface; the project's lazily
    built fitter then crashed inside `as_dict`, so every save with that model selected failed."""
    project = py_backend._project
    errors = []
    project.projectSaveError.connect(lambda message: errors.append(message))

    py_backend._sample.addNewModel()
    project.save()
    assert errors == []
    assert project.hasUnsavedChanges is False

    py_backend._sample.duplicateSelectedModel()
    project.save()
    assert errors == []
    assert project.hasUnsavedChanges is False
