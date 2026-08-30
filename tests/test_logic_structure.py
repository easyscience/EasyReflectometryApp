from EasyReflectometryApp.Backends.Py.logic.structure import COLORS
from EasyReflectometryApp.Backends.Py.logic.structure import flatten
from tests.factories import FakeGradientLayer
from tests.factories import FakeRepeatingMultilayer
from tests.factories import FakeSolvatedMaterial
from tests.factories import make_assembly
from tests.factories import make_layer
from tests.factories import make_material
from tests.factories import make_material_collection
from tests.factories import make_model
from tests.factories import make_model_collection
from tests.factories import make_project
from tests.factories import make_sample


def _project(sample, materials=None):
    materials = materials or make_material_collection(make_material('Air'), make_material('SiO2'), make_material('Si'))
    return make_project(materials=materials, models=make_model_collection(make_model(sample=sample)))


def _default_like_sample(materials):
    return make_sample(
        make_assembly(name='Superphase', layers=[make_layer(name='Air Layer', material=materials[0], thickness=0.0)]),
        make_assembly(name='SiO2', layers=[make_layer(name='SiO2 Layer', material=materials[1], thickness=25.0)]),
        make_assembly(name='Substrate', layers=[make_layer(name='Si Layer', material=materials[2], thickness=0.0)]),
    )


def test_default_model_boxes_are_tagged_and_not_double_counted():
    materials = make_material_collection(make_material('Air'), make_material('SiO2', 3.47), make_material('Si', 2.07))
    project = _project(_default_like_sample(materials), materials)

    boxes, legend, total = flatten(project)

    assert [box['label'] for box in boxes] == ['Air Layer', 'SiO2 Layer', 'Si Layer']
    assert [box['kind'] for box in boxes] == ['superphase', 'layer', 'subphase']
    assert [box['assembly_index'] for box in boxes] == [0, 1, 2]
    assert [box['layer_index'] for box in boxes] == [0, 0, 0]
    assert [box['repetitions'] for box in boxes] == [1, 1, 1]
    assert [box['color'] for box in boxes] == [COLORS[0], COLORS[1], COLORS[2]]
    assert boxes[1]['sld'] == '3.47'
    assert isinstance(boxes[1]['thickness'], float)
    assert total == 25.0  # caps excluded


def test_single_assembly_tags_first_and_last_layer_only():
    materials = make_material_collection(make_material('Air'), make_material('Si'))
    sample = make_sample(
        make_assembly(
            name='Only',
            layers=[
                make_layer(name='Top', material=materials[0]),
                make_layer(name='Mid', material=materials[1], thickness=50.0),
                make_layer(name='Bottom', material=materials[1]),
            ],
        )
    )

    boxes, _, total = flatten(_project(sample, materials))

    assert [box['kind'] for box in boxes] == ['superphase', 'layer', 'subphase']
    assert total == 50.0


def test_small_repeating_multilayer_expands():
    materials = make_material_collection(make_material('Air'), make_material('A'), make_material('B'))
    repeating = FakeRepeatingMultilayer(
        repetitions=2,
        name='Rep',
        layers=[make_layer(name='LA', material=materials[1], thickness=2.5), make_layer(name='LB', material=materials[2], thickness=5.0)],
    )
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(material=materials[0], thickness=0.0)]),
        repeating,
        make_assembly(name='Bottom', layers=[make_layer(material=materials[0], thickness=0.0)]),
    )

    boxes, _, total = flatten(_project(sample, materials))

    assert [box['label'] for box in boxes[1:-1]] == ['LA', 'LB', 'LA', 'LB']
    assert all(box['repetitions'] == 1 for box in boxes)
    assert total == 2 * 7.5


def test_large_repeating_multilayer_collapses_with_badge_on_first_box():
    materials = make_material_collection(make_material('Air'), make_material('A'), make_material('B'))
    repeating = FakeRepeatingMultilayer(
        repetitions=100,
        name='Rep',
        layers=[make_layer(name='LA', material=materials[1], thickness=2.5), make_layer(name='LB', material=materials[2], thickness=5.0)],
    )
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(material=materials[0], thickness=0.0)]),
        repeating,
        make_assembly(name='Bottom', layers=[make_layer(material=materials[0], thickness=0.0)]),
    )

    boxes, _, total = flatten(_project(sample, materials))

    assert [box['label'] for box in boxes[1:-1]] == ['LA', 'LB']  # unit emitted once
    assert [box['repetitions'] for box in boxes[1:-1]] == [100, 1]  # badge on first box only
    assert total == 100 * 7.5  # physical total counts all repeats


def test_gradient_layer_collapses_to_one_box():
    materials = make_material_collection(make_material('Air'), make_material('D2O'))
    gradient = FakeGradientLayer(name='Grad', front_material=materials[0], back_material=materials[1], thickness=2.0)
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(material=materials[0], thickness=0.0)]),
        gradient,
        make_assembly(name='Bottom', layers=[make_layer(material=materials[1], thickness=0.0)]),
    )

    boxes, _, total = flatten(_project(sample, materials))

    grad_box = boxes[1]
    assert grad_box['kind'] == 'gradient'
    assert grad_box['label'] == 'Grad'
    assert grad_box['thickness'] == 2.0
    assert grad_box['color'] == COLORS[0]
    assert grad_box['color_end'] == COLORS[1]
    assert total == 2.0


def test_ad_hoc_material_gets_fallback_color_without_raising():
    materials = make_material_collection(make_material('Air'))
    stray = make_material('NotInTable')
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(material=materials[0])]),
        make_assembly(name='Mid', layers=[make_layer(material=stray)]),
        make_assembly(name='Bottom', layers=[make_layer(material=materials[0])]),
    )

    boxes, _, _ = flatten(_project(sample, materials))

    assert boxes[1]['color'] == COLORS[1]  # first fallback slot after the 1-entry table


def test_solvated_material_is_colored_by_inner_dry_material():
    materials = make_material_collection(make_material('Air'), make_material('C32D64'))
    solvated = FakeSolvatedMaterial(materials[1], solvent_name='Air', sld=8.29)
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(material=materials[0])]),
        make_assembly(name='Tail', layers=[make_layer(name='DPPC Tail', material=solvated)]),
        make_assembly(name='Bottom', layers=[make_layer(material=materials[0])]),
    )

    boxes, _, _ = flatten(_project(sample, materials))

    assert boxes[1]['material'] == 'C32D64 in Air'  # display name stays solvated
    assert boxes[1]['color'] == COLORS[1]  # color keyed on inner dry material
    assert boxes[1]['sld'] == '8.29'  # plain-float sld unwrapped


def test_empty_models_and_stale_index_return_empty():
    project = make_project()
    assert flatten(project) == ([], [], 0.0)

    project = _project(_default_like_sample(make_material_collection(make_material('Air'), make_material('SiO2'), make_material('Si'))))
    project.current_model_index = 5
    assert flatten(project) == ([], [], 0.0)


def test_legend_lists_only_used_materials_once():
    materials = make_material_collection(make_material('Air'), make_material('Si'), make_material('Unused'))
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(material=materials[0])]),
        make_assembly(name='Mid', layers=[make_layer(material=materials[1])]),
        make_assembly(name='Mid2', layers=[make_layer(material=materials[1])]),
        make_assembly(name='Bottom', layers=[make_layer(material=materials[0])]),
    )

    _, legend, _ = flatten(_project(sample, materials))

    assert legend == [
        {'label': 'Air', 'color': COLORS[0]},
        {'label': 'Si', 'color': COLORS[1]},
    ]
