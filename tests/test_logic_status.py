from EasyReflectometryApp.Backends.Py.logic.status import Status
from tests.factories import FakeMinimizerValue
from tests.factories import make_project


class StubMinimizersLogic:
    def __init__(self, available, index):
        self._available = available
        self._index = index

    def minimizers_available(self):
        return self._available

    def minimizer_current_index(self):
        return self._index


def test_status_uses_minimizer_logic_when_present():
    project = make_project(experiments={1: object(), 3: object()}, minimizer_name='ProjectDefault')
    status = Status(project)
    status.set_minimizers_logic(StubMinimizersLogic(['A', 'B'], 1))

    assert status.project == 'Demo Project'
    assert status.minimizer == 'B'
    assert status.calculator == 'refnx'
    assert status.experiments_count == '2'


def test_status_falls_back_to_project_minimizer_for_invalid_index():
    project = make_project()
    project.minimizer = FakeMinimizerValue('FallbackMinimizer')
    status = Status(project)
    status.set_minimizers_logic(StubMinimizersLogic(['A'], 10))

    assert status.minimizer == 'FallbackMinimizer'
