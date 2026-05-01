from EasyReflectometryApp.Backends.Py.sample import Sample
from tests.factories import make_assembly
from tests.factories import make_layer
from tests.factories import make_material
from tests.factories import make_material_collection
from tests.factories import make_model
from tests.factories import make_model_collection
from tests.factories import make_project
from tests.factories import make_sample


def test_remove_selected_assembly_refreshes_cached_layers_and_clamps_layer_index(qcore_application):
    materials = make_material_collection(make_material('Air'), make_material('Si'), make_material('D2O'))
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(name='Top Layer', material=materials[0])]),
        make_assembly(
            name='Middle',
            assembly_type='Surfactant Layer',
            layers=[
                make_layer(name='Head Layer', material=materials[0]),
                make_layer(name='Tail Layer', material=materials[2]),
            ],
        ),
        make_assembly(name='Bottom', layers=[make_layer(name='Bottom Layer', material=materials[1])]),
    )
    project = make_project(materials=materials, models=make_model_collection(make_model(sample=sample)))
    project.current_model_index = 0
    project.current_assembly_index = 1
    project.current_layer_index = 1

    backend = Sample(project)

    assert [layer['label'] for layer in backend.layers] == ['Head Layer', 'Tail Layer']
    assert backend.currentAssemblyType == 'Surfactant Layer'
    assert backend.currentLayerIndex == 1

    backend.removeAssembly('1')

    assert backend.currentAssemblyIndex == 1
    assert backend.currentAssemblyType == 'Multi-layer'
    assert backend.currentLayerIndex == 0
    assert [layer['label'] for layer in backend.layers] == ['Bottom Layer']