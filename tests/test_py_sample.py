from EasyReflectometryApp.Backends.Py.sample import Sample
from tests.factories import FakeLayerMagnetism
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

def test_structure_properties_expose_flattened_stack(qcore_application):
    materials = make_material_collection(make_material('Air'), make_material('Si'))
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(name='Air Layer', material=materials[0], thickness=0.0)]),
        make_assembly(name='Mid', layers=[make_layer(name='Si Layer', material=materials[1], thickness=30.0)]),
        make_assembly(name='Bottom', layers=[make_layer(name='Sub Layer', material=materials[1], thickness=0.0)]),
    )
    backend = Sample(make_project(materials=materials, models=make_model_collection(make_model(sample=sample))))

    assert [box['kind'] for box in backend.structure] == ['superphase', 'layer', 'subphase']
    assert [entry['label'] for entry in backend.structureLegend] == ['Air', 'Si']
    assert backend.structureTotalThickness == 30.0


def test_structure_cache_cleared_and_signal_emitted_on_invalidation(qcore_application):
    materials = make_material_collection(make_material('Air'), make_material('Si'))
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(material=materials[0], thickness=0.0)]),
        make_assembly(name='Mid', layers=[make_layer(name='Si Layer', material=materials[1], thickness=30.0)]),
        make_assembly(name='Bottom', layers=[make_layer(material=materials[1], thickness=0.0)]),
    )
    backend = Sample(make_project(materials=materials, models=make_model_collection(make_model(sample=sample))))
    emitted = []
    backend.structureChanged.connect(lambda: emitted.append(True))

    assert len(backend.structure) == 3
    sample[1].layers.append(make_layer(name='New Layer', material=materials[1], thickness=10.0))
    assert len(backend.structure) == 3  # cached until invalidated

    backend._clearStructureCacheAndEmit()

    assert emitted == [True]
    assert len(backend.structure) == 4
    assert backend.structureTotalThickness == 40.0


def test_set_current_model_index_refreshes_layers_and_selection(qcore_application):
    materials = make_material_collection(make_material('Air'), make_material('D2O'), make_material('Si'))
    first = make_sample(
        make_assembly(name='Superphase', layers=[make_layer(name='Air Layer', material=materials[0])]),
        make_assembly(name='Substrate', layers=[make_layer(name='Si Layer', material=materials[2])]),
    )
    second = make_sample(
        make_assembly(name='Superphase', layers=[make_layer(name='D2O Layer', material=materials[1])]),
        make_assembly(name='Substrate', layers=[make_layer(name='Si Layer', material=materials[2])]),
    )
    project = make_project(
        materials=materials,
        models=make_model_collection(make_model(name='M1', sample=first), make_model(name='M2', sample=second)),
    )
    project.current_model_index = 0
    project.current_assembly_index = 1

    backend = Sample(project)
    assert [layer['material'] for layer in backend.layers] == ['Si']

    fired = []
    for name in ('assembliesIndexChanged', 'layersIndexChanged', 'layersChange'):
        getattr(backend, name).connect(lambda name=name: fired.append(name))

    backend.setCurrentModelIndex(1)

    assert backend.currentModelName == 'M2'
    assert backend.currentAssemblyIndex == 0
    assert backend.currentLayerIndex == 0
    assert [layer['material'] for layer in backend.layers] == ['D2O']
    assert set(fired) == {'assembliesIndexChanged', 'layersIndexChanged', 'layersChange'}


def test_magnetism_edits_invalidate_the_structure_cache(qcore_application):
    """The Structure boxes carry the moment direction, so a theta_m/rho_m edit
    changes them without changing their number - the CR-Mo1 failure mode."""
    materials = make_material_collection(make_material('Air'), make_material('Fe'), make_material('Si'))
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(material=materials[0], thickness=0.0)]),
        make_assembly(
            name='Fe',
            layers=[
                make_layer(
                    name='Fe Layer',
                    material=materials[1],
                    thickness=40.0,
                    magnetism=FakeLayerMagnetism(rho_m=3.0, theta_m=270.0),
                )
            ],
        ),
        make_assembly(name='Bottom', layers=[make_layer(material=materials[2], thickness=0.0)]),
    )
    project = make_project(materials=materials, models=make_model_collection(make_model(sample=sample)))
    project.current_assembly_index = 1
    backend = Sample(project)
    emitted = []
    backend.structureChanged.connect(lambda: emitted.append(True))

    assert backend.structure[1]['phi'] == 0.0  # theta_m 270 points along the guide field

    backend.setLayerThetaMAtIndex(0, 40.0)
    assert emitted == [True]
    assert backend.structure[1]['phi'] == 130.0

    backend.setLayerRhoMAtIndex(0, -3.0)
    assert emitted == [True, True]
    assert backend.structure[1]['phi'] == 310.0  # a negative moment points the other way
    assert backend.structure[1]['m'] == 3.0


def test_attaching_and_detaching_magnetism_rebuilds_the_structure(qcore_application):
    materials = make_material_collection(make_material('Air'), make_material('Fe'), make_material('Si'))
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(material=materials[0], thickness=0.0)]),
        make_assembly(name='Fe', layers=[make_layer(name='Fe Layer', material=materials[1], thickness=40.0)]),
        make_assembly(name='Bottom', layers=[make_layer(material=materials[2], thickness=0.0)]),
    )
    project = make_project(
        materials=materials,
        models=make_model_collection(make_model(sample=sample)),
        calculator_name='refl1d',
    )
    project.current_assembly_index = 1
    backend = Sample(project)
    emitted = []
    backend.structureChanged.connect(lambda: emitted.append(True))

    assert 'magnetic' not in backend.structure[1]

    backend.setLayerMagneticAtIndex(0, True)
    assert emitted == [True]
    assert backend.structure[1]['magnetic'] is True

    backend.setLayerMagneticAtIndex(0, False)
    assert emitted == [True, True]
    assert 'magnetic' not in backend.structure[1]
