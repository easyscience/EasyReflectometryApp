import pytest
from easyreflectometry.sample import MaterialDensity
from numpy.testing import assert_almost_equal

from EasyReflectometryApp.Backends.Py.logic.material import Material
from EasyReflectometryApp.Backends.Py.logic.material import _from_materials_collection_to_list_of_dicts
from tests.factories import make_material
from tests.factories import make_material_collection
from tests.factories import make_project


def make_density_material(formula='Si', density=2.33, name='SiDensity'):
    return MaterialDensity(chemical_structure=formula, density=density, name=name)


def test_from_materials_collection_to_list_of_dicts_serializes_values():
    materials = make_material_collection(
        make_material('Air', sld=0.0, isld=0.0),
        make_material('Si', sld=2.07, isld=0.1),
    )

    result = _from_materials_collection_to_list_of_dicts(materials)

    assert result == [
        {'label': 'Air', 'sld': '0.0', 'isld': '0.0', 'kind': 'sld', 'formula': '', 'density': '', 'sld_coupled': True},
        {'label': 'Si', 'sld': '2.07', 'isld': '0.1', 'kind': 'sld', 'formula': '', 'density': '', 'sld_coupled': True},
    ]


def test_from_materials_collection_marks_density_materials():
    materials = make_material_collection(make_density_material('Si', 2.33))

    (row,) = _from_materials_collection_to_list_of_dicts(materials)

    assert row['kind'] == 'density'
    assert row['formula'] == 'Si'
    assert row['density'] == '2.33'
    assert row['sld_coupled'] is True


def test_set_sld_refused_on_coupled_density_material():
    materials = make_material_collection(make_density_material())
    project = make_project(materials=materials)
    logic = Material(project)
    coupled_sld = materials[0].sld.value

    assert logic.set_sld_at_index(0, 9.9) is False
    assert logic.set_isld_at_index(0, 9.9) is False
    assert logic.set_sld_at_current_index(9.9) is False
    assert logic.set_isld_at_current_index(9.9) is False
    assert_almost_equal(materials[0].sld.value, coupled_sld)

    assert logic.set_sld_coupled_at_index(0, False) is True
    assert logic.set_sld_at_index(0, 9.9) is True
    assert materials[0].sld.value == 9.9


def test_set_sld_coupled_at_index_change_state_and_guards():
    materials = make_material_collection(make_density_material(), make_material('Air'))
    project = make_project(materials=materials)
    logic = Material(project)

    assert logic.set_sld_coupled_at_index(0, True) is False  # already coupled
    assert logic.set_sld_coupled_at_index(0, False) is True
    assert materials[0].sld_coupled is False
    assert logic.set_sld_coupled_at_index(0, False) is False  # no change

    assert logic.set_sld_coupled_at_index(1, False) is False  # not a density material
    assert logic.set_sld_coupled_at_index(5, False) is False  # out of bounds


def test_set_formula_at_index_updates_derived_sld():
    materials = make_material_collection(make_density_material('Co', 8.9))
    project = make_project(materials=materials)
    logic = Material(project)

    assert logic.set_formula_at_index(0, 'B') is True
    assert materials[0].chemical_structure == 'B'
    # sld follows the new formula's scattering length AND molecular weight
    assert_almost_equal(materials[0].molecular_weight.value, 10.81)
    assert_almost_equal(materials[0].sld.value, 26.277925961998147)

    assert logic.set_formula_at_index(0, 'B') is False  # unchanged
    assert logic.set_formula_at_index(0, '   ') is False  # blank
    assert logic.set_formula_at_index(0, '###') is False  # invalid, rejected
    assert materials[0].chemical_structure == 'B'


def test_set_density_at_index():
    materials = make_material_collection(make_density_material('Si', 2.33))
    project = make_project(materials=materials)
    logic = Material(project)
    original_sld = materials[0].sld.value

    assert logic.set_density_at_index(0, '4.66') is True
    assert materials[0].density.value == pytest.approx(4.66)
    assert_almost_equal(materials[0].sld.value, 2 * original_sld)

    assert logic.set_density_at_index(0, 4.66) is False  # unchanged
    assert logic.set_density_at_index(0, 'abc') is False  # not a number


def test_set_density_at_index_clamps_below_the_min_bound():
    # The core's Parameter.value setter clamps out-of-bounds writes to
    # min/max rather than raising (unlike __init__, which raises) — so a
    # negative density silently becomes 0.0, not rejected. The setter's
    # try/except guards a hypothetical raise without assuming one.
    materials = make_material_collection(make_density_material('Si', 2.33))
    project = make_project(materials=materials)
    logic = Material(project)

    assert logic.set_density_at_index(0, '-1') is True
    assert materials[0].density.value == pytest.approx(0.0)


def test_material_logic_add_duplicate_move_and_remove():
    materials = make_material_collection(
        make_material('Air', sld=0.0),
        make_material('Si', sld=2.07),
    )
    project = make_project(materials=materials)
    logic = Material(project)

    logic.add_new()
    assert len(project._materials) == 3

    project.current_material_index = 1
    logic.duplicate_selected()
    assert len(project._materials) == 4
    assert project._materials[2].name == 'Si'

    logic.move_selected_up()
    assert project.current_material_index == 0

    logic.move_selected_down()
    assert project.current_material_index == 1

    logic.remove_at_index('3')
    assert len(project._materials) == 3


def test_material_setters_return_change_state():
    materials = make_material_collection(make_material('Air', sld=0.0, isld=0.0))
    project = make_project(materials=materials)
    logic = Material(project)

    assert logic.set_name_at_current_index('Vacuum') is True
    assert logic.set_name_at_current_index('Vacuum') is False

    assert logic.set_sld_at_current_index(1.23) is True
    assert logic.set_sld_at_current_index(1.23) is False

    assert logic.set_isld_at_current_index(0.45) is True
    assert logic.set_isld_at_current_index(0.45) is False
