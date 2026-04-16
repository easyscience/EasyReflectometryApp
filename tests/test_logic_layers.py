from EasyReflectometryApp.Backends.Py.logic import layers as layers_module
from tests.factories import FakeLayerAreaPerMolecule
from tests.factories import make_assembly
from tests.factories import make_layer
from tests.factories import make_layer_collection
from tests.factories import make_material
from tests.factories import make_material_collection
from tests.factories import make_model
from tests.factories import make_model_collection
from tests.factories import make_project
from tests.factories import make_sample


def test_from_layers_collection_to_list_of_dicts_respects_assembly_enablement(monkeypatch):
    monkeypatch.setattr(layers_module, 'LayerAreaPerMolecule', FakeLayerAreaPerMolecule)
    layer = FakeLayerAreaPerMolecule(
        name='Headgroup',
        material=make_material('Tail Material'),
        thickness=12.0,
        roughness=3.0,
        solvent=make_material('Water'),
        area_per_molecule=44.0,
        solvent_fraction=0.35,
        molecular_formula='C12H25',
    )

    regular = layers_module._from_layers_collection_to_list_of_dicts(make_layer_collection(layer), 'regular')
    superphase = layers_module._from_layers_collection_to_list_of_dicts(make_layer_collection(layer), 'superphase')
    subphase = layers_module._from_layers_collection_to_list_of_dicts(make_layer_collection(layer), 'subphase')

    assert regular[0]['thickness_enabled'] == 'True'
    assert regular[0]['roughness_enabled'] == 'True'
    assert regular[0]['formula'] == 'C12H25'
    assert regular[0]['apm'] == '44.0'
    assert regular[0]['solvent'] == 'Water'
    assert regular[0]['solvation'] == '0.35'
    assert superphase[0]['thickness_enabled'] == 'False'
    assert superphase[0]['roughness_enabled'] == 'False'
    assert subphase[0]['thickness_enabled'] == 'False'
    assert subphase[0]['roughness_enabled'] == 'True'


def test_layers_add_new_creates_si_material_when_missing(monkeypatch):
    monkeypatch.setattr(layers_module, 'Material', make_material)
    materials = make_material_collection(make_material('Air'), make_material('D2O'))
    sample = make_sample(
        make_assembly(name='Top'),
        make_assembly(name='Middle'),
        make_assembly(name='Bottom'),
    )
    model = make_model(sample=sample)
    project = make_project(materials=materials, models=make_model_collection(model))
    project.current_assembly_index = 1
    logic = layers_module.Layers(project)

    logic.add_new()

    assert [material.name for material in project._materials] == ['Air', 'D2O', 'Si']
    assert logic._layers[-1].material.name == 'Si'
    assert logic._layers[-1].name == 'Si Layer'


def test_layers_move_duplicate_and_setters_update_current_layer(monkeypatch):
    monkeypatch.setattr(layers_module, 'Material', make_material)
    materials = make_material_collection(make_material('Air'), make_material('Si'))
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(name='Top Layer', material=materials[0])]),
        make_assembly(
            name='Middle',
            layers=[
                make_layer(name='Layer A', material=materials[0], thickness=10.0, roughness=2.0),
                make_layer(name='Layer B', material=materials[1], thickness=20.0, roughness=4.0),
            ],
        ),
        make_assembly(name='Bottom', layers=[make_layer(name='Bottom Layer', material=materials[1])]),
    )
    model = make_model(sample=sample)
    project = make_project(materials=materials, models=make_model_collection(model))
    project.current_assembly_index = 1
    project.current_layer_index = 1
    logic = layers_module.Layers(project)

    assert logic._assembly_type == 'regular'
    assert logic.set_name_at_current_index('Renamed') is True
    assert logic.set_thickness_at_current_index(25.0) is True
    assert logic.set_roughness_at_current_index(5.0) is True
    assert logic.set_material_at_current_index(0) is True
    assert logic._layers[1].name == 'Air Layer'
    assert logic.set_material_at_current_index(0) is False

    logic.duplicate_selected()
    assert len(logic._layers) == 3

    logic.move_selected_up()
    assert project.current_layer_index == 0

    logic.move_selected_down()
    assert project.current_layer_index == 1

    logic.remove_at_index('2')
    assert len(logic._layers) == 2


def test_layers_index_based_setters_update_target_row_even_when_current_index_differs(monkeypatch):
    monkeypatch.setattr(layers_module, 'Material', make_material)
    monkeypatch.setattr(layers_module, 'LayerAreaPerMolecule', FakeLayerAreaPerMolecule)

    air = make_material('Air')
    si = make_material('Si')
    d2o = make_material('D2O')
    materials = make_material_collection(air, si, d2o)

    surfactant_layer = FakeLayerAreaPerMolecule(
        name='Headgroup',
        material=air,
        thickness=11.0,
        roughness=2.0,
        solvent=d2o,
        area_per_molecule=44.0,
        solvent_fraction=0.35,
        molecular_formula='C12H25',
    )

    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(name='Top Layer', material=air)]),
        make_assembly(
            name='Middle',
            layers=[
                make_layer(name='Layer A', material=air, thickness=10.0, roughness=1.0),
                surfactant_layer,
            ],
        ),
        make_assembly(name='Bottom', layers=[make_layer(name='Bottom Layer', material=si)]),
    )
    model = make_model(sample=sample)
    project = make_project(materials=materials, models=make_model_collection(model))
    project.current_assembly_index = 1
    project.current_layer_index = 1
    logic = layers_module.Layers(project)

    assert logic.set_thickness_at_index(0, 15.0) is True
    assert logic._layers[0].thickness.value == 15.0
    assert logic._layers[1].thickness.value == 11.0

    assert logic.set_roughness_at_index(0, 3.5) is True
    assert logic._layers[0].roughness.value == 3.5
    assert logic._layers[1].roughness.value == 2.0

    assert logic.set_material_at_index(0, 1) is True
    assert logic._layers[0].material.name == 'Si'
    assert logic._layers[0].name == 'Si Layer'
    assert logic._layers[1].material.name == 'Air'

    assert logic.set_formula_at_index(1, 'C10H21') is True
    assert logic._layers[1].molecular_formula == 'C10H21'

    assert logic.set_solvation_at_index(1, 0.5) is True
    assert logic._layers[1].solvent_fraction == 0.5

    assert logic.set_apm_at_index(1, 55.0) is True
    assert logic._layers[1].area_per_molecule == 55.0

    assert logic.set_solvent_at_index(1, 0) is True
    assert logic._layers[1].solvent.name == 'Air'


def test_layers_index_based_setters_ignore_invalid_indices(monkeypatch):
    monkeypatch.setattr(layers_module, 'Material', make_material)

    air = make_material('Air')
    si = make_material('Si')
    materials = make_material_collection(air, si)
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(name='Top Layer', material=air)]),
        make_assembly(name='Middle', layers=[make_layer(name='Layer A', material=air, thickness=10.0, roughness=1.0)]),
        make_assembly(name='Bottom', layers=[make_layer(name='Bottom Layer', material=si)]),
    )
    model = make_model(sample=sample)
    project = make_project(materials=materials, models=make_model_collection(model))
    project.current_assembly_index = 1
    logic = layers_module.Layers(project)

    assert logic.set_material_at_index(3, 1) is False
    assert logic.set_material_at_index(0, 5) is False
    assert logic.set_solvent_at_index(2, 0) is False
    assert logic.set_thickness_at_index(4, 12.0) is False

    assert logic._layers[0].material.name == 'Air'
    assert logic._layers[0].thickness.value == 10.0
