from types import SimpleNamespace

from EasyReflectometryApp.Backends.Py.logic import minimizers as minimizers_module
from tests.factories import make_multi_fitter_stub
from tests.factories import make_project


class FakeEnumValue:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


class FakeAvailableMinimizers:
    LMFit = FakeEnumValue('LMFit')
    Bumps = FakeEnumValue('Bumps')
    DFO = FakeEnumValue('DFO')
    Bumps_simplex = FakeEnumValue('Bumps_simplex')
    DREAM = FakeEnumValue('DREAM')
    SciPy = FakeEnumValue('SciPy')

    def __iter__(self):
        return iter([self.LMFit, self.Bumps, self.DFO, self.DREAM, self.SciPy])


def test_minimizers_filters_out_blocked_entries(monkeypatch):
    monkeypatch.setattr(minimizers_module, 'AvailableMinimizers', FakeAvailableMinimizers())
    project = make_project(minimizer_name='Initial')

    logic = minimizers_module.Minimizers(project)

    # Bayesian sentinel is prepended at index 0
    assert logic.minimizers_available() == ['BUMPS-DREAM (Bayesian)', 'DREAM', 'SciPy']
    # Index 0 is Bayesian sentinel: selected_minimizer_enum() falls back to Bumps_simplex
    assert logic.selected_minimizer_enum().name == 'Bumps_simplex'
    assert logic.is_bayesian_selected() is True


def test_minimizers_set_index_updates_project_and_runtime_properties(monkeypatch):
    monkeypatch.setattr(minimizers_module, 'AvailableMinimizers', FakeAvailableMinimizers())
    project = make_project(minimizer_name='Initial')
    project._fitter = SimpleNamespace(easy_science_multi_fitter=make_multi_fitter_stub())

    logic = minimizers_module.Minimizers(project)

    # Index 0 = Bayesian sentinel, index 1 = DREAM, index 2 = SciPy
    assert logic.set_minimizer_current_index(2) is True
    assert project.minimizer.name == 'SciPy'
    assert logic.set_minimizer_current_index(2) is False

    assert logic.tolerance == 1e-6
    assert logic.max_iterations == 5000
    assert logic.set_tolerance(2e-6) is True
    assert logic.set_tolerance(2e-6) is False
    assert logic.set_max_iterations(7000) is True
    assert logic.set_max_iterations(7000) is False


def test_minimizers_return_defaults_without_fitter(monkeypatch):
    monkeypatch.setattr(minimizers_module, 'AvailableMinimizers', FakeAvailableMinimizers())
    project = make_project(minimizer_name='Initial')

    logic = minimizers_module.Minimizers(project)

    assert logic.tolerance == 1e-6
    assert logic.max_iterations == 5000
    assert logic.set_tolerance(2e-6) is False
    assert logic.set_max_iterations(7000) is False
