"""Magnetic materials, rho_m coupling and the model's guide field in the backend logic."""

import pytest
from easyreflectometry import Project as RealProject
from easyreflectometry.sample import MaterialMagnetic
from easyscience import global_object

from EasyReflectometryApp.Backends.Py.logic.layers import Layers
from EasyReflectometryApp.Backends.Py.logic.parameters import Parameters
from EasyReflectometryApp.Backends.Py.logic.structure import guide_field_reference
from EasyReflectometryApp.Backends.Py.logic.structure import magnetic_vector_for_layer

FE_RHO_M = 5.042


@pytest.fixture
def project():
    """A refl1d project whose film layer (assembly 1, layer 0) is iron and magnetic."""
    global_object.map._clear()
    project = RealProject()
    project.calculator = 'refl1d'
    project.default_model()
    iron = MaterialMagnetic(name='Fe')
    project._materials.add_material(iron)
    film = project.models[0].sample[1].layers[0]
    film.material = iron
    project.models[0].interface = project.models[0].interface  # rebind the new material
    project.current_assembly_index = 1
    project.current_layer_index = 0
    assert Layers(project).set_magnetic_at_index(0, True)
    return project


def _film(project):
    return project.models[0].sample[1].layers[0]


def _rows(project):
    return {row['name']: row for row in Parameters(project).all_parameters()}


class TestCoupling:
    def test_rows_report_the_material_and_the_coupling(self, project):
        logic = Layers(project)
        row = logic.magnetism[0]
        assert (row['material_magnetic'], row['rho_m_coupled']) == (True, False)

        assert logic.set_rho_m_coupled_at_index(0, True) is True
        assert logic.set_rho_m_coupled_at_index(0, True) is False

        row = logic.magnetism[0]
        assert row['rho_m_coupled'] is True
        assert float(row['rho_m']) == pytest.approx(FE_RHO_M, abs=1e-3)

    def test_coupled_rho_m_cannot_be_typed(self, project):
        logic = Layers(project)
        logic.set_rho_m_coupled_at_index(0, True)

        assert logic.set_rho_m_at_index(0, 1.0) is False
        assert _film(project).magnetism.rho_m.value == pytest.approx(FE_RHO_M, abs=1e-3)

    def test_coupling_reaches_the_calculator(self, project):
        Layers(project).set_rho_m_coupled_at_index(0, True)
        film = _film(project)
        film.material.magnetic_moment = 1.1

        wrapper = project.models[0].interface()._wrapper
        assert wrapper.get_layer_value(film.unique_name, 'magnetism_rhoM') == pytest.approx(FE_RHO_M / 2, abs=1e-3)


class TestField:
    def test_defaults_and_reference(self, project):
        field = Layers(project).field
        assert field == {
            'guide_field_angle': 270.0,
            'applied_field': 0.0,
            'model_magnetic': True,
            'in_plane': True,
            'phi': 0.0,
        }
        assert all(type(value) in (float, bool) for value in field.values())

    @pytest.mark.parametrize(
        ('angle', 'in_plane', 'phi'),
        [(270.0, True, 0.0), (-90.0, True, 0.0), (90.0, True, 180.0), (0.0, False, 180.0), (45.0, False, 180.0)],
    )
    def test_reference_follows_the_angle(self, angle, in_plane, phi):
        assert guide_field_reference(angle) == {'in_plane': in_plane, 'phi': phi}

    def test_set_field(self, project):
        logic = Layers(project)
        assert logic.set_field('guide_field_angle', '0') is True
        assert logic.set_field('guide_field_angle', '0') is False
        assert logic.set_field('applied_field', 'not a number') is False
        assert logic.field['in_plane'] is False
        assert project.models[0].guide_field_angle.value == 0.0

    def test_field_parameters_follow_magnetism(self, project):
        rows = _rows(project)
        field_rows = [row for name, row in rows.items() if 'guide_field_angle' in name or 'applied_field' in name]
        assert len(field_rows) == 2 and all(row['enabled'] for row in field_rows)

        Layers(project).set_magnetic_at_index(0, False)

        model = project.models[0]
        assert not model.guide_field_angle.enabled and not model.applied_field.enabled

    def test_arrow_components_follow_the_field(self, project):
        magnetism = _film(project).magnetism
        magnetism.rho_m = 3.0

        in_plane = magnetic_vector_for_layer(magnetism)
        normal = magnetic_vector_for_layer(magnetism, guide_field_angle=0.0)

        assert (in_plane['m_par'], in_plane['m_perp']) == pytest.approx((3.0, 0.0), abs=1e-12)
        assert (normal['m_par'], normal['m_perp']) == pytest.approx((0.0, 3.0), abs=1e-12)
        # The arrow itself is drawn in the sample plane and does not move.
        assert normal['phi'] == in_plane['phi']


class TestParameterTable:
    def test_material_magnetic_sld_is_a_material_parameter(self, project):
        rows = _rows(project)
        assert rows['Fe material rho_m']['group'] == 'Fe'
        assert 'Fe magnetic_sld' not in rows

    def test_moment_is_inactive_until_a_layer_is_coupled(self, project):
        assert _rows(project)['Fe magnetic_moment']['kind'] == 'inactive'

        Layers(project).set_rho_m_coupled_at_index(0, True)

        assert _rows(project)['Fe magnetic_moment']['kind'] == 'parameter'

    def test_density_and_moment_are_exclusive_with_a_decoupled_nuclear_sld(self, project):
        Layers(project).set_rho_m_coupled_at_index(0, True)
        iron = _film(project).material
        assert _rows(project)['Fe density']['exclusive_with'] is None

        iron.sld_coupled = False
        logic = Parameters(project)
        enabled = [row for row in logic.parameters if row.get('enabled', True)]
        names = [row['name'] for row in enabled]
        logic._current_index = names.index('Fe density')
        logic.set_current_parameter_fit(True)
        logic._current_index = names.index('Fe magnetic_moment')
        logic.set_current_parameter_fit(True)

        assert iron.magnetic_moment.free is True
        assert iron.density.free is False

    def test_magnetic_filter_includes_moment_and_field(self, project):
        logic = Parameters(project)
        logic.set_name_filter_criteria('magnetic')
        names = {row['name'] for row in logic.parameters}
        assert any('magnetic_moment' in name for name in names)
        assert any('guide_field_angle' in name for name in names)
        assert any('rho_m' in name for name in names)


def _in_fit(project, parameter):
    return any(candidate is parameter for model in project.models for candidate in model.get_fit_parameters())


class TestInactiveMeansOutOfTheFit:
    def test_moment_leaves_the_fit_when_the_last_layer_uncouples(self, project):
        logic = Layers(project)
        logic.set_rho_m_coupled_at_index(0, True)
        iron = _film(project).material
        iron.magnetic_moment.free = True
        assert _in_fit(project, iron.magnetic_moment)

        logic.set_rho_m_coupled_at_index(0, False)

        assert _rows(project)['Fe magnetic_moment']['kind'] == 'inactive'
        assert not _in_fit(project, iron.magnetic_moment)

    def test_moment_leaves_the_fit_when_the_layer_gets_another_material(self, project):
        logic = Layers(project)
        logic.set_rho_m_coupled_at_index(0, True)
        iron = _film(project).material
        iron.magnetic_moment.free = True
        other = next(index for index, material in enumerate(project._materials) if material is not iron)

        with pytest.warns(UserWarning, match='no longer coupled'):
            assert logic.set_material_at_index(0, other)

        assert not _in_fit(project, iron.magnetic_moment)

    def test_field_leaves_the_fit_when_the_model_stops_being_magnetic(self, project):
        model = project.models[0]
        model.applied_field.free = True
        model.guide_field_angle.free = True

        Layers(project).set_magnetic_at_index(0, False)

        assert not _in_fit(project, model.applied_field)
        assert not _in_fit(project, model.guide_field_angle)

    def test_decoupled_density_without_a_coupled_layer_is_inactive(self, project):
        from EasyReflectometryApp.Backends.Py.logic.material import Material

        iron = _film(project).material
        iron.density.free = True
        index = list(project._materials).index(iron)

        Material(project).set_sld_coupled_at_index(index, False)

        assert _rows(project)['Fe density']['kind'] == 'inactive'
        assert not _in_fit(project, iron.density)

    def test_decoupled_density_of_a_coupled_material_stays_fittable(self, project):
        from EasyReflectometryApp.Backends.Py.logic.material import Material

        Layers(project).set_rho_m_coupled_at_index(0, True)
        iron = _film(project).material
        iron.density.free = True
        index = list(project._materials).index(iron)

        Material(project).set_sld_coupled_at_index(index, False)

        assert _rows(project)['Fe density']['kind'] == 'parameter'
        assert _in_fit(project, iron.density)


class TestFieldWithoutAModel:
    def test_field_reports_the_defaults(self, project):
        logic = Layers(project)
        project._current_model_index = 5  # out of range: nothing to show

        assert logic.field == {
            'guide_field_angle': 270.0,
            'applied_field': 0.0,
            'model_magnetic': False,
            'in_plane': True,
            'phi': 0.0,
        }
        assert logic.set_field('applied_field', '1.0') is False
