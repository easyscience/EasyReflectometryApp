import sys
from types import ModuleType
from types import SimpleNamespace

import numpy as np

from EasyReflectometryApp.Backends.Py.logic import fitting as fitting_module
from tests.factories import make_experiment
from tests.factories import make_fit_result
from tests.factories import make_model
from tests.factories import make_project


class StubMinimizersLogic:
    def __init__(self, selected=None, tolerance=1e-5, max_iterations=250):
        self._selected = selected
        self.tolerance = tolerance
        self.max_iterations = max_iterations

    def selected_minimizer_enum(self):
        return self._selected


class FakeEasyScienceMultiFitter:
    def __init__(self):
        self.switched_to = None
        self.tolerance = None
        self.max_evaluations = None
        self.minimizer = SimpleNamespace(package='fake-engine', _method='fake-method')

    def switch_minimizer(self, value):
        self.switched_to = value


class FakeMultiFitter:
    def __init__(self, *models):
        self.models = models
        self.easy_science_multi_fitter = FakeEasyScienceMultiFitter()


def install_fake_multifitter(monkeypatch):
    # Inject a fake module into sys.modules because the real easyreflectometry.fitting
    # module pulls in heavy calculator backends at import time. Using monkeypatch.setitem
    # ensures the original module is restored automatically after the test.
    fake_module = ModuleType('easyreflectometry.fitting')
    fake_module.MultiFitter = FakeMultiFitter
    monkeypatch.setitem(sys.modules, 'easyreflectometry.fitting', fake_module)


def test_prepare_threaded_fit_handles_empty_experiments():
    project = make_project(experiments={})
    logic = fitting_module.Fitting(project)

    result = logic.prepare_threaded_fit(StubMinimizersLogic())

    assert result == (None, None, None, None, None)
    assert logic.fit_error_message == 'No experiments to fit'
    assert logic.fit_finished is True
    assert logic.show_results_dialog is True


def test_prepare_threaded_fit_builds_masked_arrays_and_configures_minimizer(monkeypatch):
    install_fake_multifitter(monkeypatch)
    model_a = make_model(name='A')
    model_b = make_model(name='B')
    experiments = {
        5: make_experiment('Exp B', model=model_b, x=np.array([5.0, 6.0]), y=np.array([7.0, 8.0]), ye=np.array([9.0, 16.0])),
        2: make_experiment('Exp A', model=model_a, x=np.array([1.0, 2.0, 3.0]), y=np.array([4.0, 5.0, 6.0]), ye=np.array([1.0, 0.0, 4.0])),
    }
    project = make_project(experiments=experiments)
    logic = fitting_module.Fitting(project)
    selected = SimpleNamespace(name='DREAM')

    fitter, x_data, y_data, weights, method = logic.prepare_threaded_fit(StubMinimizersLogic(selected, 1e-4, 321))

    assert fitter.switched_to is selected
    assert fitter.tolerance == 1e-4
    assert fitter.max_evaluations == 321
    assert [values.tolist() for values in x_data] == [[1.0, 3.0], [5.0, 6.0]]
    assert [values.tolist() for values in y_data] == [[4.0, 6.0], [7.0, 8.0]]
    assert [values.tolist() for values in weights] == [[1.0, 0.5], [1 / 3, 0.25]]
    assert method is None


def test_on_fit_finished_and_fit_properties_cover_multi_and_single_results(monkeypatch):
    project = make_project()
    logic = fitting_module.Fitting(project)
    monkeypatch.setattr(fitting_module, 'count_free_parameters', lambda current_project: 2)

    logic.prepare_for_threaded_fit()
    logic.on_fit_finished([
        make_fit_result(success=True, chi2=4.0, n_pars=2, x=[1, 2, 3], reduced_chi=1.1),
        make_fit_result(success=True, chi2=6.0, n_pars=2, x=[1, 2, 3, 4], reduced_chi=1.2),
    ])

    assert logic.fit_finished is True
    assert logic.fit_success is True
    assert logic.fit_n_pars == 2
    assert logic.fit_chi2 == 2.0

    logic.on_fit_finished(make_fit_result(success=False, chi2=9.0, n_pars=1, x=[1, 2], reduced_chi=4.5))
    assert logic.fit_success is False
    assert logic.fit_n_pars == 1
    assert logic.fit_chi2 == 4.5


def test_fit_n_pars_uses_global_free_parameter_count_for_multi_experiment_results(monkeypatch):
    project = make_project()
    logic = fitting_module.Fitting(project)
    monkeypatch.setattr(fitting_module, 'count_free_parameters', lambda current_project: 3)

    logic.prepare_for_threaded_fit()
    logic.on_fit_finished([
        make_fit_result(success=True, chi2=4.0, n_pars=3, x=[1, 2, 3], reduced_chi=1.1),
        make_fit_result(success=True, chi2=6.0, n_pars=3, x=[1, 2, 3, 4], reduced_chi=1.2),
    ])

    assert logic.fit_n_pars == 3


def test_fit_progress_updates_transient_state_and_message():
    project = make_project()
    logic = fitting_module.Fitting(project)

    logic.prepare_for_threaded_fit()
    logic.on_fit_progress(
        {
            'iteration': 12,
            'chi2': 4.25,
            'reduced_chi2': 1.75,
            'parameter_values': {'alpha': 2.0},
            'refresh_plots': True,
            'finished': False,
        }
    )

    assert logic.fit_iteration == 12
    assert logic.fit_interim_chi2 == 4.25
    assert logic.fit_interim_reduced_chi2 == 1.75
    assert logic.fit_preview_parameter_values == {'alpha': 2.0}
    assert logic.fit_has_preview_update is True
    assert logic.fit_has_interim_update is True
    assert logic.fit_progress_message == 'Fitting... iter 12, Chi2 = 4.25'


def test_fit_progress_state_resets_on_finish_failure_and_stop():
    project = make_project()
    logic = fitting_module.Fitting(project)

    logic.prepare_for_threaded_fit()
    logic.on_fit_progress({'iteration': 3, 'chi2': 8.0, 'parameter_values': {'beta': 1.0}})
    logic.on_fit_finished(make_fit_result(success=True, chi2=8.0, n_pars=1, x=[1, 2], reduced_chi=4.0))

    assert logic.fit_iteration == 0
    assert logic.fit_progress_message == ''
    assert logic.fit_has_interim_update is False

    logic.prepare_for_threaded_fit()
    logic.on_fit_progress({'iteration': 4, 'chi2': 7.0, 'refresh_plots': True})
    logic.on_fit_failed('boom')

    assert logic.fit_iteration == 0
    assert logic.fit_preview_parameter_values == {}
    assert logic.fit_has_preview_update is False

    logic.prepare_for_threaded_fit()
    logic.on_fit_progress({'iteration': 5, 'chi2': 6.0})
    logic.stop_fit()

    assert logic.fit_iteration == 0
    assert logic.fit_progress_message == ''
    assert logic.fit_has_interim_update is False


def test_fit_failure_and_cancellation_state_transitions():
    project = make_project()
    logic = fitting_module.Fitting(project)

    logic.on_fit_failed('boom')
    assert logic.fit_error_message == 'boom'
    assert logic.fit_finished is True
    assert logic.show_results_dialog is True

    logic.stop_fit()
    assert logic.fit_cancelled is True
    assert logic.fit_error_message == 'Fitting cancelled by user'

    logic.reset_stop_flag()
    assert logic.fit_cancelled is False


def test_start_stop_handles_success_and_fiterror():
    project = make_project(models=[object()])
    project.fitter = SimpleNamespace(fit_single_data_set_1d=lambda exp_data: make_fit_result(success=True, chi2=1.7, reduced_chi=1.7))
    logic = fitting_module.Fitting(project)

    logic.start_stop()
    assert logic.fit_finished is True
    assert logic.show_results_dialog is True
    assert logic.fit_chi2 == 1.7

    def _raise_fit_error(exp_data):
        raise fitting_module.FitError('fit failed')

    project.fitter = SimpleNamespace(fit_single_data_set_1d=_raise_fit_error)
    logic.start_stop()
    assert 'fit failed' in logic.fit_error_message


# ===================================================================
# Bayesian sampling preparation
# ===================================================================

def test_prepare_threaded_sample_handles_empty_experiments():
    project = make_project(experiments={})
    logic = fitting_module.Fitting(project)

    result = logic.prepare_threaded_sample(StubMinimizersLogic())

    assert result == (None, None)
    assert logic.fit_error_message == 'No experiments to sample'
    assert logic.fit_finished is True
    assert logic.show_results_dialog is True


def test_prepare_threaded_sample_builds_multifitter_and_datagroup(monkeypatch):
    install_fake_multifitter(monkeypatch)
    model_a = make_model(name='A')
    experiments = {
        0: make_experiment('Exp A', model=model_a,
                           x=np.array([1.0, 2.0]), y=np.array([4.0, 5.0]), ye=np.array([0.1, 0.2])),
    }
    project = make_project(experiments=experiments)
    logic = fitting_module.Fitting(project)

    # Mock the datagroup collection to avoid scipp dependency
    monkeypatch.setattr(logic, 'collect_selected_experiments_datagroup', lambda: 'fake-data-group')

    multi_fitter, data_group = logic.prepare_threaded_sample(StubMinimizersLogic())

    assert multi_fitter is not None
    assert multi_fitter.models == (model_a,)
    assert data_group == 'fake-data-group'


def test_collect_selected_experiments_datagroup_builds_sc_structs(monkeypatch):
    # Fake scipp to avoid import issues
    import numpy as np

    # We need to make scipp available; we'll mock the import within the method
    model = make_model(name='M1')
    experiments = {
        0: make_experiment('Exp 1', model=model,
                           x=np.array([1.0, 2.0]), y=np.array([0.1, 0.2]), ye=np.array([0.01, 0.04])),
    }
    project = make_project(experiments=experiments)
    logic = fitting_module.Fitting(project)

    # Create a minimal sc.DataGroup stand-in
    class FakeSCUnit:
        def __init__(self, unit_str):
            self._str = unit_str
        def __eq__(self, other):
            return isinstance(other, FakeSCUnit) and other._str == self._str

    class FakeSCArray:
        _registry = []
        def __init__(self, *, dims, values, variances=None, unit=None):
            self.dims = dims
            self.values = values
            self.variances = variances
            self.unit = unit
            FakeSCArray._registry.append(self)

    class FakeSCDataGroup(dict):
        def __init__(self, data=None, coords=None, attrs=None):
            super().__init__()
            self.data = data or {}
            self.coords = coords or {}
            self.attrs = attrs or {}
        def __repr__(self):
            return f'DataGroup({dict(self.data)})'

    FakeSCArray._registry = []

    monkeypatch.setattr('scipp.Unit', FakeSCUnit)
    monkeypatch.setattr('scipp.array', FakeSCArray)
    monkeypatch.setattr('scipp.DataGroup', FakeSCDataGroup)

    dg = logic.collect_selected_experiments_datagroup()

    # Verify FakeSCArray was called to create coords and data
    assert len(FakeSCArray._registry) >= 2  # coords + data entries
    # Coords entries have 'Qz' in their dims
    coord_calls = [a for a in FakeSCArray._registry if 'Qz' in str(a.dims)]
    assert len(coord_calls) >= 1
    # Data entries have variances (ye_vals)
    data_calls = [a for a in FakeSCArray._registry if a.variances is not None]
    project = make_project()
    logic = fitting_module.Fitting(project)

    logic.prepare_for_threaded_sample()

    assert logic.running is True
    assert logic.fit_finished is False
    assert logic.show_results_dialog is False
    assert logic.sample_progress_message == 'Sampling… (this may take several minutes)'


# ===================================================================
# Bayesian sampling progress
# ===================================================================

def test_on_sample_progress_updates_step_and_total():
    project = make_project()
    logic = fitting_module.Fitting(project)

    logic.on_sample_progress({'iteration': 42, 'total_steps': 1000})

    assert logic.sample_step == 42
    assert logic.sample_total_steps == 1000
    assert logic.sample_has_update is True


def test_on_sample_progress_handles_zero_defaults():
    project = make_project()
    logic = fitting_module.Fitting(project)

    logic.on_sample_progress({})

    assert logic.sample_step == 0
    assert logic.sample_total_steps == 0


def test_on_sample_progress_handles_none_values():
    project = make_project()
    logic = fitting_module.Fitting(project)

    logic.on_sample_progress({'iteration': None, 'total_steps': None})

    assert logic.sample_step == 0
    assert logic.sample_total_steps == 0


# ===================================================================
# Bayesian sampling completion lifecycle
# ===================================================================

def test_on_sample_finished_clears_fit_state_and_shows_dialog():
    project = make_project()
    logic = fitting_module.Fitting(project)

    # Simulate that a fit was running
    logic.prepare_for_threaded_sample()
    assert logic.running is True

    logic.on_sample_finished()

    assert logic.running is False
    assert logic.fit_finished is True
    assert logic.show_results_dialog is True
    assert logic.fit_error_message == ''
    assert logic.fit_success is False  # default
    assert logic.sample_step == 0      # cleared via clear_fit_progress
    assert logic.sample_has_update is False


def test_on_sample_finished_preserves_none_result():
    """on_sample_finished does not set a FitResult — Bayesian results are stored elsewhere."""
    project = make_project()
    logic = fitting_module.Fitting(project)

    logic.on_sample_finished()

    assert logic._result is None
    assert logic._results == []


def test_clear_sample_progress_works():
    project = make_project()
    logic = fitting_module.Fitting(project)

    logic.on_sample_progress({'iteration': 50, 'total_steps': 500})
    assert logic.sample_step == 50

    logic.clear_sample_progress()

    assert logic.sample_step == 0
    assert logic.sample_total_steps == 0
    assert logic.sample_progress_message == ''
