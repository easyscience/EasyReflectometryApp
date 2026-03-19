from EasyReflectometryApp.Backends.Py.logic.material import Material
from EasyReflectometryApp.Backends.Py.logic.material import _from_materials_collection_to_list_of_dicts

from tests.factories import make_material
from tests.factories import make_material_collection
from tests.factories import make_project


def test_from_materials_collection_to_list_of_dicts_serializes_values():
    materials = make_material_collection(
        make_material('Air', sld=0.0, isld=0.0),
        make_material('Si', sld=2.07, isld=0.1),
    )

    result = _from_materials_collection_to_list_of_dicts(materials)

    assert result == [
        {'label': 'Air', 'sld': '0.0', 'isld': '0.0'},
        {'label': 'Si', 'sld': '2.07', 'isld': '0.1'},
    ]


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