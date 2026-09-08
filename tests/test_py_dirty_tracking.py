"""Dirty tracking: the inventory of signals that mark the project unsaved.

The point of these tests is the inventory, not the flag. A mutation path whose signal is missing
from `DIRTYING_SIGNALS` leaves `hasUnsavedChanges` False, so the close prompt never fires and the
user's work is discarded silently. `test_every_external_signal_is_classified` is what makes that
hard to do by accident.
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
def py_backend(qcore_application):
    return backend_module.PyBackend()


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
    project._clear_dirty()
    assert project.hasUnsavedChanges is False

    _emit(getattr(py_backend, part_name), signal_name)

    assert project.hasUnsavedChanges is True, f'{part_name}.{signal_name} does not mark the project dirty'


def test_project_starts_clean_and_setters_mark_it_dirty(py_backend):
    project = py_backend._project
    project._clear_dirty()

    project.setName('A new name')
    assert project.hasUnsavedChanges is True

    project._clear_dirty()
    project.setDescription('A new description')
    assert project.hasUnsavedChanges is True


def test_setter_that_changes_nothing_does_not_dirty(py_backend):
    project = py_backend._project
    project._clear_dirty()

    project.setName(project.name)
    project.setDescription(project.description)

    assert project.hasUnsavedChanges is False
