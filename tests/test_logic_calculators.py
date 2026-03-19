from EasyReflectometryApp.Backends.Py.logic.calculators import Calculators
from tests.factories import make_project


def test_available_returns_configured_interfaces():
    project = make_project(calculator_interfaces=['refnx', 'refl1d'])

    logic = Calculators(project)

    assert logic.available() == ['refnx', 'refl1d']
    assert logic.current_index() == 0


def test_set_current_index_updates_project_calculator():
    project = make_project(calculator_interfaces=['refnx', 'refl1d'])

    logic = Calculators(project)

    changed = logic.set_current_index(1)

    assert changed is True
    assert logic.current_index() == 1
    assert project.calculator == 'refl1d'


def test_set_current_index_returns_false_when_unchanged():
    project = make_project(calculator_interfaces=['refnx', 'refl1d'])

    logic = Calculators(project)

    changed = logic.set_current_index(0)

    assert changed is False
    assert project.calculator == 'refnx'