"""User-set parameter limits are kept, and the unphysical ones are flagged.

The library opens a default window around a new parameter (50-200 % of a
thickness, -1..10 for an SLD); the core clamps a value to it and refuses a bound
that would exclude the value. Whatever the user enters, on the Sample or the
Analysis page, must win over that window.
"""

import math

import pytest
from easyreflectometry import Project
from easyscience import global_object
from easyscience.variable import Parameter

from EasyReflectometryApp.Backends.Py.logic.helpers import set_bound
from EasyReflectometryApp.Backends.Py.logic.helpers import set_value_widening_bounds
from EasyReflectometryApp.Backends.Py.logic.layers import Layers as LayersLogic
from EasyReflectometryApp.Backends.Py.logic.parameters import Parameters as ParametersLogic
from EasyReflectometryApp.Backends.Py.sample import Sample


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.registry.clear()
    yield
    global_object.registry.clear()


def _parameter(value=100.0, low=50.0, high=200.0):
    return Parameter(value, min=low, max=high)


class TestHelpers:
    @pytest.mark.parametrize(('value', 'expected'), [(300.0, (300.0, 50.0, 300.0)), (10.0, (10.0, 10.0, 200.0))])
    def test_a_value_past_a_bound_moves_it(self, value, expected):
        parameter = _parameter()
        set_value_widening_bounds(parameter, value)
        assert (parameter.value, parameter.min, parameter.max) == expected

    @pytest.mark.parametrize(
        ('bound', 'value', 'expected'),
        [('min', 150.0, (150.0, 150.0, 200.0)), ('max', 80.0, (80.0, 50.0, 80.0)), ('min', 5.0, (100.0, 5.0, 200.0))],
    )
    def test_a_bound_is_kept_moving_the_value_onto_it(self, bound, value, expected):
        parameter = _parameter()
        set_bound(parameter, bound, value)
        assert (parameter.value, parameter.min, parameter.max) == expected

    @pytest.mark.parametrize(('bound', 'value'), [('min', 200.0), ('min', 500.0), ('max', 50.0), ('max', 1.0)])
    def test_a_bound_leaving_no_room_is_refused_and_changes_nothing(self, bound, value):
        parameter = _parameter()
        with pytest.raises(ValueError):
            set_bound(parameter, bound, value)
        assert (parameter.value, parameter.min, parameter.max) == (100.0, 50.0, 200.0)


@pytest.fixture
def backend(qcore_application):
    return Sample(Project())  # installs the default model and its default limits


@pytest.fixture
def project(backend):
    return backend._project_lib


def _film_layer(project):
    return project.models[0].sample[1].layers[0]


def _row(logic, parameter):
    return next(row for row in logic.all_parameters() if row['object'] is parameter)


def _select(logic, parameter):
    rows = [row for row in logic.parameters if row.get('enabled', True)]
    logic.set_current_index(next(i for i, row in enumerate(rows) if row['object'] is parameter))


class TestAnalysisTable:
    def test_a_min_above_the_value_is_kept(self, project):
        thickness = _film_layer(project).thickness
        thickness.min, thickness.max = 50.0, 200.0
        logic = ParametersLogic(project)
        _select(logic, thickness)

        assert logic.set_current_parameter_min('150')

        assert (thickness.value, thickness.min) == (150.0, 150.0)
        assert _row(logic, thickness)['min'] == 150.0

    def test_a_min_above_the_max_is_refused(self, project):
        thickness = _film_layer(project).thickness
        thickness.min, thickness.max = 50.0, 200.0
        before = thickness.value
        logic = ParametersLogic(project)
        _select(logic, thickness)

        assert not logic.set_current_parameter_min('300')
        assert (thickness.value, thickness.min, thickness.max) == (before, 50.0, 200.0)

    def test_unphysical_bounds_are_flagged_and_infinite_ones_are_not(self, project):
        layer = _film_layer(project)
        logic = ParametersLogic(project)
        layer.thickness.min = -5.0
        layer.material.sld.max = 20.0
        layer.roughness.max = math.inf

        thickness_row = _row(logic, layer.thickness)
        sld_row = _row(logic, layer.material.sld)
        roughness_row = _row(logic, layer.roughness)
        assert (thickness_row['minUnphysical'], thickness_row['maxUnphysical']) == (True, False)
        assert (sld_row['minUnphysical'], sld_row['maxUnphysical']) == (False, True)
        # What the table's tooltip explains a red bound with
        assert (thickness_row['physicalRange'], sld_row['physicalRange']) == ([0.0, math.inf], [-1.0, 10.0])
        assert roughness_row['maxUnphysical'] is False

    def test_the_default_limits_are_physical(self, project):
        logic = ParametersLogic(project)
        rows = [row for row in logic.all_parameters() if row['kind'] == 'parameter']
        assert not [row['name'] for row in rows if row['minUnphysical'] or row['maxUnphysical']]


class TestSamplePage:
    @pytest.fixture
    def layers(self, project):
        project.current_assembly_index = 1  # the film, whose layer has a default window
        project.current_layer_index = 0
        return LayersLogic(project)

    def test_a_thickness_past_its_window_widens_it(self, project, layers):
        thickness = _film_layer(project).thickness
        thickness.min, thickness.max = 50.0, 200.0

        assert layers.set_thickness_at_index(0, 300.0)

        assert (thickness.value, thickness.max) == (300.0, 300.0)

    def test_an_sld_past_the_physical_window_is_kept_and_flagged(self, project, backend):
        sld = _film_layer(project).material.sld
        assert (sld.min, sld.max) == (-1.0, 10.0)
        index = project._materials.index(_film_layer(project).material)

        backend.setMaterialSldAtIndex(index, 12.0)

        assert (sld.value, sld.max) == (12.0, 12.0)
        assert _row(ParametersLogic(project), sld)['maxUnphysical'] is True

    def test_theta_m_keeps_its_angle_domain(self, project, layers):
        project.calculator = 'refl1d'  # the engine that models magnetism
        layers.set_magnetic_at_index(0, True)
        theta_m = _film_layer(project).magnetism.theta_m

        layers.set_theta_m_at_index(0, 400.0)

        assert (theta_m.value, theta_m.max) == (360.0, 360.0)

    def test_a_bound_constraint_past_the_value_is_kept(self, project, backend):
        thickness = _film_layer(project).thickness
        thickness.min, thickness.max = 50.0, 200.0
        name = _row(backend._parameters_logic, thickness)['name']

        result = backend.addConstraint(backend.constrainableParameterNames.index(name), '>', '150')

        assert result['success'], result
        assert (thickness.value, thickness.min) == (150.0, 150.0)
