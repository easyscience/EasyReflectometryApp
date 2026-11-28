from EasyReflectometryApp.Backends.Py.logic import models as models_module
from tests.factories import FakeResolutionFunction
from tests.factories import make_material
from tests.factories import make_material_collection
from tests.factories import make_model
from tests.factories import make_model_collection
from tests.factories import make_project


def test_from_models_collection_to_list_of_dicts_uses_original_name():
    models = make_model_collection(
        make_model(name='Internal 1', user_data={'original_name': 'Visible 1'}, color='#111111'),
        make_model(name='Internal 2', color='#222222'),
    )

    result = models_module._from_models_collection_to_list_of_dicts(models)

    assert result == [
        {'label': 'Visible 1', 'color': '#111111'},
        {'label': 'Internal 2', 'color': '#222222'},
    ]


def test_a_model_loaded_from_a_file_can_be_renamed():
    # A sample loaded from an ORSO file shows the file's name (user_data['original_name']).
    # Renaming once changed only model.name, so the shown name never changed and the model
    # table, which commits every keystroke, put the file's name straight back.
    models = make_model_collection(
        make_model(name='Model', user_data={'original_name': 'Si / SiO2 / film / D2O'}),
        make_model(name='Other', user_data={'original_name': 'Other file name'}),
    )
    logic = models_module.Models(make_project(models=models))

    assert logic.set_name_at_index(0, 'Film in D2O') is True
    assert logic.set_name_at_current_index('Film in D2') is True
    assert logic.models_names == ['Film in D2', 'Other file name']
    assert logic.set_name_at_index(1, 'Model') is True  # same as the internal name, not the shown one
    assert logic.models_names == ['Film in D2', 'Model']
    assert logic.set_name_at_index(1, 'Model') is False


def test_the_instrument_model_is_that_of_the_selected_experiment(monkeypatch):
    # With several contrasts each experiment has its own model, so its own scale,
    # background and resolution; the Experiment page shows those, not the current model's.
    monkeypatch.setattr(models_module, 'PercentageFwhm', FakeResolutionFunction)
    from tests.factories import make_experiment

    models = make_model_collection(
        make_model(name='D2O', scale=1.0, background=2e-7, resolution_function=object()),
        make_model(name='H2O', scale=0.95, background=5e-6, resolution_function=FakeResolutionFunction(5.0)),
    )
    experiments = {0: make_experiment('in D2O', model=models[0]), 1: make_experiment('in H2O', model=models[1])}
    project = make_project(models=models, experiments=experiments)
    logic = models_module.Models(project)

    project.current_experiment_index = 1
    assert logic.index == 0  # the Sample page's current model is left alone
    assert logic.current_experiment_model_index == 1
    assert (logic.scaling_at(1), logic.background_at(1), logic.resolution_at(1)) == (0.95, 5e-6, '5.0')
    assert logic.set_background_at(1, 6e-6) is True
    assert models[1].background.value == 6e-6
    assert models[0].background.value == 2e-7
    assert logic.set_resolution_at(0, '3.0') is False  # a measured resolution is not a percentage

    experiments[1].model = None
    assert logic.current_experiment_model_index is None
    assert models_module.Models(make_project(models=models)).current_experiment_model_index is None


def test_model_properties_and_resolution_handling(monkeypatch):
    monkeypatch.setattr(models_module, 'PercentageFwhm', FakeResolutionFunction)
    models = make_model_collection(
        make_model(name='Model A', scale=1.2, background=0.3, resolution_function=FakeResolutionFunction(7.5)),
        make_model(name='Model B', resolution_function=object()),
    )
    project = make_project(models=models)
    logic = models_module.Models(project)

    assert logic.name_at_current_index == 'Model A'
    assert logic.scaling_at_current_index == 1.2
    assert logic.background_at_current_index == 0.3
    assert logic.resolution_at_current_index == '7.5'
    assert logic.models_names == ['Model A', 'Model B']

    assert logic.set_name_at_current_index('Renamed') is True
    assert logic.set_scaling_at_current_index(2.5) is True
    assert logic.set_background_at_current_index(0.7) is True
    assert logic.set_resolution_at_current_index('3.3') is True
    assert models[0].resolution_function.constant == 3.3

    project.current_model_index = 1
    assert logic.resolution_at_current_index == '-'


def test_default_model_content_populates_expected_materials():
    materials = make_material_collection(make_material('Air'), make_material('SiO2'), make_material('Si'))
    project = make_project(materials=materials, models=make_model_collection(make_model(name='New Model')))
    model = project._models[0]
    logic = models_module.Models(project)

    logic.default_model_content(model)

    assert model.add_assemblies_called == 1
    assert model.sample.data[0].name == 'Superphase'
    assert model.sample.data[0].layers.data[0].material.name == 'Air'
    assert model.sample.data[0].layers.data[0].thickness.value == 0.0
    assert model.sample.data[0].layers.data[0].roughness.value == 0.0
    assert model.sample.data[1].name == 'SiO2'
    assert model.sample.data[1].layers.data[0].material.name == 'SiO2'
    assert model.sample.data[1].layers.data[0].thickness.value == 100.0
    assert model.sample.data[1].layers.data[0].roughness.value == 3.0
    assert model.sample.data[2].name == 'Substrate'
    assert model.sample.data[2].layers.data[0].material.name == 'Si'
    assert model.sample.data[2].layers.data[0].roughness.value == 1.2


def test_model_collection_operations_update_current_index():
    materials = make_material_collection(make_material('Air'), make_material('SiO2'), make_material('Si'))
    models = make_model_collection(make_model(name='M1'), make_model(name='M2'))
    project = make_project(materials=materials, models=models)
    logic = models_module.Models(project)

    logic.add_new()
    assert len(project._models) == 3
    assert project.current_model_index == 2

    logic.duplicate_selected_model()
    assert len(project._models) == 4
    assert project.current_model_index == 3

    logic.move_selected_up()
    assert project.current_model_index == 2

    logic.move_selected_down()
    assert project.current_model_index == 3
