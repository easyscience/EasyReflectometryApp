from types import SimpleNamespace

from EasyReflectometryApp.Backends.Py.logic import parameters as parameters_module
from tests.factories import FakeParameter
from tests.factories import make_model
from tests.factories import make_model_collection
from tests.factories import make_parameter
from tests.factories import make_project


class FakeMap:
    def __init__(self, paths, names):
        self._paths = paths
        self._names = names

    def find_path(self, model_unique_name, parameter_unique_name):
        return self._paths.get((model_unique_name, parameter_unique_name), [])

    def get_item_by_key(self, key):
        return SimpleNamespace(name=self._names[key])


def test_from_parameters_to_list_of_dicts_prefixes_layers_and_deduplicates_shared_params(monkeypatch):
    monkeypatch.setattr(parameters_module, 'Parameter', FakeParameter)
    fake_map = FakeMap(
        {
            ('m1', 'thickness'): ['group_t1', 'param_t1'],
            ('m2', 'thickness'): ['group_t2', 'param_t2'],
            ('m1', 'scale'): ['group_scale', 'param_scale'],
            ('m2', 'scale'): ['group_scale', 'param_scale'],
            ('m1', 'dep'): ['group_dep', 'param_dep'],
        },
        {
            'group_t1': 'LayerA',
            'param_t1': 'thickness',
            'group_t2': 'LayerA',
            'param_t2': 'thickness',
            'group_scale': 'Instrument',
            'param_scale': 'scale',
            'group_dep': 'Instrument',
            'param_dep': 'background',
        },
    )
    monkeypatch.setattr(parameters_module.global_object, 'map', fake_map)

    models = make_model_collection(
        make_model(name='M1 internal', unique_name='m1', user_data={'original_name': 'M1'}),
        make_model(name='M2 internal', unique_name='m2', user_data={'original_name': 'M2'}),
    )
    scale = make_parameter(name='scale', unique_name='scale', value=1.5, free=False, enabled=True)
    thickness = make_parameter(name='thickness', unique_name='thickness', value=20.0, free=True, enabled=True)
    dependent = make_parameter(
        name='background',
        unique_name='dep',
        value=0.2,
        free=False,
        independent=False,
        dependency_expression='2*a',
        dependency_map={'a': scale},
        enabled=False,
    )

    result = parameters_module._from_parameters_to_list_of_dicts([thickness, scale, dependent], models)

    assert [entry['display_name'] for entry in result] == [
        'M1 LayerA thickness',
        'Instrument scale',
        'Instrument background',
        'M2 LayerA thickness',
    ]
    assert result[1]['dependency'] == ''
    assert result[2]['dependency'] == '2*Instrument scale'
    assert result[2]['enabled'] is False
    assert result[0]['alias'] == 'm1_layera_thickness'
    assert result[3]['alias'] == 'm2_layera_thickness'


def test_parameters_filtering_metadata_and_current_parameter_updates(monkeypatch):
    monkeypatch.setattr(parameters_module, 'count_free_parameters', lambda project: 2)
    monkeypatch.setattr(parameters_module, 'count_fixed_parameters', lambda project: 1)
    project = make_project()
    logic = parameters_module.Parameters(project)
    free_parameter = make_parameter(name='Scale', unique_name='scale', value=1.0, minimum=0.0, maximum=2.0, free=True)
    fixed_parameter = make_parameter(name='Thickness', unique_name='layer.thickness', value=10.0, minimum=1.0, maximum=50.0)
    mocked_parameters = [
        {
            'name': 'Instrument scale',
            'display_name': 'Instrument scale',
            'group': 'Instrument',
            'unique_name': 'scale',
            'fit': True,
            'enabled': True,
            'independent': True,
            'alias': 'instrument_scale',
            'object': free_parameter,
        },
        {
            'name': 'Layer thickness',
            'display_name': 'Layer thickness',
            'group': 'Layer',
            'unique_name': 'layer.thickness',
            'fit': False,
            'enabled': True,
            'independent': False,
            'alias': 'layer_thickness',
            'object': fixed_parameter,
        },
        {
            'name': 'Hidden background',
            'display_name': 'Hidden background',
            'group': 'Experiment',
            'unique_name': 'background',
            'fit': False,
            'enabled': False,
            'independent': True,
            'alias': 'hidden_background',
            'object': make_parameter(name='Background', unique_name='background'),
        },
    ]
    monkeypatch.setattr(logic, 'all_parameters', lambda: mocked_parameters)

    assert logic.as_status_string == '3 (2 free, 1 fixed)'
    assert logic.set_name_filter_criteria(' scale ') is True
    assert [entry['display_name'] for entry in logic.parameters] == ['Instrument scale']
    assert logic.set_variability_filter_criteria('fixed') is True
    logic.set_name_filter_criteria('')
    assert [entry['display_name'] for entry in logic.parameters] == ['Layer thickness']

    metadata = logic.constraint_metadata()
    assert metadata == [
        {'alias': 'hidden_background', 'displayName': 'Hidden background', 'group': 'Experiment', 'independent': True},
        {'alias': 'instrument_scale', 'displayName': 'Instrument scale', 'group': 'Instrument', 'independent': True},
        {'alias': 'layer_thickness', 'displayName': 'Layer thickness', 'group': 'Layer', 'independent': False},
    ]

    logic.set_variability_filter_criteria('all')
    logic.set_current_index(0)
    assert logic.set_current_parameter_value('1.5') is True
    assert logic.set_current_parameter_min('0.2') is True
    assert logic.set_current_parameter_max('3.2') is True
    assert logic.set_current_parameter_fit(False) is True
    assert free_parameter.value == 1.5
    assert free_parameter.min == 0.2
    assert free_parameter.max == 3.2
    assert free_parameter.free is False


def test_add_constraint_supports_arithmetic_and_constant_dependencies():
    independent = make_parameter(name='Scale', unique_name='scale', value=2.0)
    dependent = make_parameter(name='Background', unique_name='background', value=0.5)
    project = make_project()
    project.parameters = [independent, dependent]
    logic = parameters_module.Parameters(project)

    logic.add_constraint(1, '=', 3.0, '*', 0)
    assert dependent.dependency_expression == 'a*b'
    assert dependent.dependency_map == {'a': independent, 'b': 3.0}

    logic.add_constraint(1, '=', 7.0, '', -1)
    assert dependent.dependency_expression == 'a'
    assert dependent.dependency_map == {'a': 7.0}
