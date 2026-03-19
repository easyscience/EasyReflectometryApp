from pathlib import Path

from EasyReflectometryApp.Backends.Py.logic.project import Project

from tests.factories import make_assembly
from tests.factories import make_layer
from tests.factories import make_material
from tests.factories import make_material_collection
from tests.factories import make_model
from tests.factories import make_model_collection
from tests.factories import make_project
from tests.factories import make_sample


def make_project_with_sample():
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(name='Top Layer')]),
        make_assembly(name='Middle', layers=[make_layer(name='Middle Layer')]),
        make_assembly(name='Bottom', layers=[make_layer(name='Bottom Layer')]),
    )
    model = make_model(sample=sample)
    materials = make_material_collection(make_material('Air'), make_material('SiO2'), make_material('Si'), make_material('D2O'))
    return make_project(materials=materials, models=make_model_collection(model))


def test_project_constructor_initializes_default_model_and_fixed_layer_enablement():
    project_lib = make_project_with_sample()

    logic = Project(project_lib)

    assert ('default_model',) in project_lib.calls
    assert logic.created is False
    assert project_lib.models[0].sample[0].layers[0].thickness.enabled is False
    assert project_lib.models[0].sample[0].layers[0].roughness.enabled is False
    assert project_lib.models[0].sample[-1].layers[-1].thickness.enabled is False


def test_project_metadata_and_q_properties_delegate():
    project_lib = make_project_with_sample()
    logic = Project(project_lib)

    assert logic.path == str(project_lib.path)
    assert logic.root_path == str(project_lib.path.parent)
    logic.root_path = 'C:/new/location/project.json'
    assert project_lib.calls[-1] == ('set_path_project_parent', Path('C:/new/location'))

    logic.name = 'Updated Project'
    logic.description = 'Updated Description'
    assert logic.name == 'Updated Project'
    assert logic.description == 'Updated Description'
    assert logic.creation_date == '2026-03-19'

    assert logic.set_q_min('0.02') is True
    assert logic.set_q_min('0.02') is False
    assert logic.set_q_max('0.7') is True
    assert logic.set_q_resolution('400') is True
    assert logic.q_min == 0.02
    assert logic.q_max == 0.7
    assert logic.q_resolution == 400


def test_project_info_and_delegated_file_operations():
    project_lib = make_project_with_sample()
    logic = Project(project_lib)

    info = logic.info()
    assert info['name'] == 'Demo Project'
    assert info['location'] == project_lib.path

    logic.create()
    logic.save()
    logic.load('demo.json')
    logic.load_experiment('exp.ort')
    logic.load_new_experiment('new.ort')
    assert logic.count_datasets_in_file('file.ort') == 3
    assert logic.load_all_experiments_from_file('file.ort') == 2

    assert ('create',) in project_lib.calls
    assert ('save_as_json', False) in project_lib.calls
    assert ('save_as_json', True) in project_lib.calls
    assert ('load_from_json', 'demo.json') in project_lib.calls
    assert ('load_experiment_for_model_at_index', 'exp.ort', 0) in project_lib.calls
    assert ('load_new_experiment', 'new.ort') in project_lib.calls


def test_project_experimental_data_and_orso_model_updates():
    project_lib = make_project_with_sample()
    logic = Project(project_lib)

    assert logic.experimental_data_at_current_index is True
    project_lib._current_model_index = 5
    assert logic.experimental_data_at_current_index is False

    added_model = make_model(sample=make_sample(make_assembly(), make_assembly(), make_assembly()))
    logic.add_sample_from_orso(added_model)
    assert project_lib.models[-1].sample[0].layers[0].thickness.enabled is False

    replacement_model = make_model(sample=make_sample(make_assembly(), make_assembly(), make_assembly()))
    logic.replace_models_from_orso(replacement_model)
    assert project_lib.models[0].sample[0].layers[0].thickness.enabled is False

    logic.set_sample_from_orso('sample')
    assert ('set_sample_from_orso', 'sample') in project_lib.calls


def test_project_reset_calls_reset_and_default_model():
    project_lib = make_project_with_sample()
    logic = Project(project_lib)
    project_lib.calls.clear()

    logic.reset()

    assert project_lib.calls == [('reset',), ('default_model',)]