from EasyReflectometryApp.Backends.Py.logic import assemblies as assemblies_module
from tests.factories import FakeMultilayer
from tests.factories import FakeRepeatingMultilayer
from tests.factories import FakeSurfactantLayer
from tests.factories import make_assembly
from tests.factories import make_layer
from tests.factories import make_material
from tests.factories import make_material_collection
from tests.factories import make_model
from tests.factories import make_model_collection
from tests.factories import make_project
from tests.factories import make_sample


def test_from_assemblies_collection_to_list_of_dicts_includes_special_fields(monkeypatch):
    monkeypatch.setattr(assemblies_module, 'RepeatingMultilayer', FakeRepeatingMultilayer)
    monkeypatch.setattr(assemblies_module, 'SurfactantLayer', FakeSurfactantLayer)

    repeating = FakeRepeatingMultilayer(repetitions=3, name='Repeat')
    surfactant = FakeSurfactantLayer(name='Surf')
    surfactant.constrain_area_per_molecule = 'True'
    surfactant.conformal_roughness = 'True'

    result = assemblies_module._from_assemblies_collection_to_list_of_dicts([FakeMultilayer(name='Plain'), repeating, surfactant])

    assert result[0]['type'] == 'Multi-layer'
    assert result[1]['repetitions'].value == 3
    assert result[2]['constrain_apm'] == 'True'
    assert result[2]['conformal_roughness'] == 'True'


def test_assemblies_add_new_and_type_transitions(monkeypatch):
    monkeypatch.setattr(assemblies_module, 'Multilayer', FakeMultilayer)
    monkeypatch.setattr(assemblies_module, 'RepeatingMultilayer', FakeRepeatingMultilayer)
    monkeypatch.setattr(assemblies_module, 'SurfactantLayer', FakeSurfactantLayer)
    materials = make_material_collection(make_material('Air'), make_material('Si'), make_material('D2O'))
    sample = make_sample(make_assembly(name='Existing', layers=[make_layer(material=materials[1])]))
    model = make_model(sample=sample)
    project = make_project(materials=materials, models=make_model_collection(model))
    logic = assemblies_module.Assemblies(project)

    logic.add_new()
    assert logic._assemblies[-1].layers[0].material.name == 'Si'

    assert logic.set_name_at_current_index('Renamed Assembly') is True
    assert logic._assemblies[0].name == 'Renamed Assembly'

    assert logic.set_type_at_current_index('Repeating Multi-layer') is True
    assert isinstance(logic._assemblies[0], FakeRepeatingMultilayer)
    assert logic.repetitions_at_current_index == '1'
    assert logic.set_repeated_layer_reptitions(5) is True
    assert logic.repetitions_at_current_index == '5'

    assert logic.set_type_at_current_index('Surfactant Layer') is True
    assert isinstance(logic._assemblies[0], FakeSurfactantLayer)
    assert logic._assemblies[0].layers[0].solvent.name == 'Air'
    assert logic._assemblies[0].layers[1].solvent.name == 'D2O'
    assert logic.set_constrain_apm('True') is True
    assert logic.set_conformal_roughness('True') is True


def test_assemblies_duplicate_move_and_remove(monkeypatch):
    monkeypatch.setattr(assemblies_module, 'Multilayer', FakeMultilayer)
    monkeypatch.setattr(assemblies_module, 'RepeatingMultilayer', FakeRepeatingMultilayer)
    monkeypatch.setattr(assemblies_module, 'SurfactantLayer', FakeSurfactantLayer)
    model = make_model(sample=make_sample(make_assembly(name='A1'), make_assembly(name='A2')))
    project = make_project(models=make_model_collection(model))
    project.current_assembly_index = 1
    logic = assemblies_module.Assemblies(project)

    logic.duplicate_selected()
    assert len(logic._assemblies) == 3

    logic.move_selected_up()
    assert project.current_assembly_index == 0

    logic.move_selected_down()
    assert project.current_assembly_index == 1

    logic.remove_at_index('2')
    assert len(logic._assemblies) == 2


def test_assemblies_set_type_at_index_updates_target_row_when_current_index_differs(monkeypatch):
    monkeypatch.setattr(assemblies_module, 'Multilayer', FakeMultilayer)
    monkeypatch.setattr(assemblies_module, 'RepeatingMultilayer', FakeRepeatingMultilayer)
    monkeypatch.setattr(assemblies_module, 'SurfactantLayer', FakeSurfactantLayer)

    materials = make_material_collection(make_material('Air'), make_material('Si'), make_material('D2O'))
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(name='Top Layer', material=materials[0])]),
        make_assembly(name='Middle', layers=[make_layer(name='Middle Layer', material=materials[1])]),
        make_assembly(name='Bottom', layers=[make_layer(name='Bottom Layer', material=materials[1])]),
    )
    model = make_model(sample=sample)
    project = make_project(materials=materials, models=make_model_collection(model))
    project.current_assembly_index = 2
    logic = assemblies_module.Assemblies(project)

    assert logic.set_type_at_index(1, 'Surfactant Layer') is True

    assert isinstance(logic._assemblies[1], FakeSurfactantLayer)
    assert logic._assemblies[1].layers[0].solvent.name == 'Air'
    assert logic._assemblies[1].layers[1].solvent.name == 'D2O'

    assert isinstance(logic._assemblies[2], FakeMultilayer)
    assert logic._assemblies[2].name == 'Bottom'
    assert project.current_assembly_index == 2
