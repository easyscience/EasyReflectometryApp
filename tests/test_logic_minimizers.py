from types import SimpleNamespace

import pytest
from easyreflectometry.fit_settings import FitSettings
from easyscience import AvailableMinimizers

from EasyReflectometryApp.Backends.Py.logic import minimizers as minimizers_module


def _project(settings=None):
    """The minimizers logic only reads and writes the project's fit settings."""
    return SimpleNamespace(fit_settings=settings or FitSettings())


def _index(logic, name):
    return logic.minimizers_available().index(name)


def test_aliases_are_not_offered_and_bayesian_comes_first():
    logic = minimizers_module.Minimizers(_project())

    available = logic.minimizers_available()

    assert available[0] == minimizers_module.BAYESIAN_LABEL
    assert 'Bumps_simplex' in available and 'LMFit_leastsq' in available
    assert not {'LMFit', 'Bumps', 'DFO'} & set(available)


def test_index_is_computed_from_the_settings():
    project = _project()
    logic = minimizers_module.Minimizers(project)

    # A loaded project's minimizer shows without anyone touching the combo
    project.fit_settings.minimizer = AvailableMinimizers.LMFit_powell
    assert logic.minimizer_current_index() == _index(logic, 'LMFit_powell')

    # An alias set directly on the project shows as the member it stands for
    project.fit_settings.minimizer = AvailableMinimizers.Bumps
    assert logic.minimizer_current_index() == _index(logic, 'Bumps_simplex')

    project.fit_settings.minimizer = AvailableMinimizers.Bumps_simplex
    project.fit_settings.mode = 'sample'
    assert logic.minimizer_current_index() == 0
    assert logic.is_bayesian_selected() is True


def test_selecting_writes_the_settings():
    project = _project()
    logic = minimizers_module.Minimizers(project)

    assert logic.set_minimizer_current_index(0) is True
    assert (project.fit_settings.mode, project.fit_settings.minimizer) == ('sample', AvailableMinimizers.Bumps_simplex)

    assert logic.set_minimizer_current_index(_index(logic, 'DFO_leastsq')) is True
    assert (project.fit_settings.mode, project.fit_settings.minimizer) == ('minimize', AvailableMinimizers.DFO_leastsq)
    assert logic.set_minimizer_current_index(_index(logic, 'DFO_leastsq')) is False


def test_generic_settings_work_before_any_fit_and_reset_to_engine_default():
    project = _project()
    logic = minimizers_module.Minimizers(project)

    assert logic.tolerance is None and logic.max_iterations is None  # engine defaults
    assert logic.set_tolerance(2e-6) is True
    assert logic.set_max_iterations(7000.0) is True
    assert (project.fit_settings.tolerance, project.fit_settings.max_evaluations) == (2e-6, 7000)
    assert logic.set_tolerance(2e-6) is False

    assert logic.set_tolerance(None) is True
    assert logic.set_max_iterations(None) is True
    assert logic.tolerance is None and logic.max_iterations is None


@pytest.mark.parametrize(('field', 'value'), [('tolerance', -1.0), ('tolerance', float('inf')), ('max_iterations', 0)])
def test_invalid_values_are_rejected_and_nothing_changes(field, value):
    project = _project()
    logic = minimizers_module.Minimizers(project)

    with pytest.raises(ValueError):
        getattr(logic, f'set_{field}')(value)
    assert getattr(logic, field) is None


def test_objective_is_a_setting():
    project = _project()
    logic = minimizers_module.Minimizers(project)

    assert logic.objectives == ['hybrid', 'mighell', 'legacy_mask']
    assert logic.set_objective('legacy_mask') is True
    assert project.fit_settings.objective == 'legacy_mask'
    with pytest.raises(ValueError):
        logic.set_objective('nonsense')


def test_finite_bounds_follow_the_engine_not_the_label():
    project = _project()
    logic = minimizers_module.Minimizers(project)

    project.fit_settings.minimizer = AvailableMinimizers.LMFit_differential_evolution
    assert logic.requires_finite_bounds() is True
    project.fit_settings.minimizer = AvailableMinimizers.Bumps_simplex
    assert logic.requires_finite_bounds() is False


def test_options_of_the_selected_minimizer():
    project = _project(FitSettings(minimizer=AvailableMinimizers.LMFit_differential_evolution))
    logic = minimizers_module.Minimizers(project)

    assert logic.set_option('seed', 3) is True
    seed = next(option for option in logic.options() if option['name'] == 'seed')
    assert (seed['isSet'], seed['value']) == (True, 3)
    with pytest.raises(ValueError):
        logic.set_option('popsize', 0)
    assert logic.set_option('seed', None) is True
    assert project.fit_settings.engine_options == {}


def test_app_defaults_give_a_new_project_bumps():
    project = _project(FitSettings(minimizer=AvailableMinimizers.LMFit_leastsq, mode='sample'))

    minimizers_module.apply_app_defaults(project)

    assert project.fit_settings.minimizer is minimizers_module.APP_DEFAULT_MINIMIZER
    assert project.fit_settings.mode == 'minimize'
