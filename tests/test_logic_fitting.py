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


def test_on_fit_finished_and_fit_properties_cover_multi_and_single_results():
    project = make_project()
    logic = fitting_module.Fitting(project)

    logic.prepare_for_threaded_fit()
    logic.on_fit_finished([
        make_fit_result(success=True, chi2=4.0, n_pars=2, x=[1, 2, 3], reduced_chi=1.1),
        make_fit_result(success=True, chi2=6.0, n_pars=2, x=[1, 2, 3, 4], reduced_chi=1.2),
    ])

    assert logic.fit_finished is True
    assert logic.fit_success is True
    assert logic.fit_n_pars == 4
    assert logic.fit_chi2 == 10.0

    logic.on_fit_finished(make_fit_result(success=False, chi2=9.0, n_pars=1, x=[1, 2], reduced_chi=4.5))
    assert logic.fit_success is False
    assert logic.fit_n_pars == 1
    assert logic.fit_chi2 == 9.0


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
