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


def test_from_parameters_to_list_of_dicts_handles_alias_edge_cases_and_fallbacks(monkeypatch):
    monkeypatch.setattr(parameters_module, 'Parameter', FakeParameter)

    class ParameterWithoutEnabled:
        def __init__(self, name, unique_name, value=0.0, independent=True, dependency_expression='', dependency_map=None):
            self.name = name
            self.unique_name = unique_name
            self.value = value
            self.variance = 0.0
            self.min = 0.0
            self.max = 10.0
            self.unit = ''
            self.free = False
            self.independent = independent
            self.dependency_expression = dependency_expression
            self.dependency_map = dependency_map or {}

    fake_map = FakeMap(
        {
            ('m1', 'p1'): ['group_same', 'param_same'],
            ('m1', 'p2'): ['group_same', 'param_same'],
            ('m1', 'reserved'): ['group_np', 'param_np'],
            ('m1', 'numeric'): ['group_num', 'param_num'],
            ('m1', 'empty'): ['only_key'],
            ('m1', 'dep_other'): ['group_dep', 'param_dep'],
            ('m1', 'no_enabled'): ['group_ne', 'param_ne'],
        },
        {
            'group_same': 'Same Group',
            'param_same': 'Same Name',
            'group_np': 'Reserved',
            'param_np': 'np',
            'group_num': '123',
            'param_num': '456',
            'group_dep': 'DepGroup',
            'param_dep': 'DepName',
            'group_ne': 'Visible',
            'param_ne': 'Parameter',
        },
    )
    monkeypatch.setattr(parameters_module.global_object, 'map', fake_map)

    models = make_model_collection(make_model(name='M1', unique_name='m1', user_data={'original_name': 'M1'}))
    param1 = make_parameter(name='same', unique_name='p1')
    param2 = make_parameter(name='same', unique_name='p2')
    reserved = make_parameter(name='np', unique_name='reserved')
    numeric = make_parameter(name='456', unique_name='numeric')
    empty = make_parameter(name='!!!', unique_name='empty')
    dep_other = make_parameter(
        name='dep',
        unique_name='dep_other',
        independent=False,
        dependency_expression='a+1',
        dependency_map={'a': 'external'},
    )
    no_enabled = ParameterWithoutEnabled(name='visible', unique_name='no_enabled', value=2.0)

    result = parameters_module._from_parameters_to_list_of_dicts(
        [param1, param2, reserved, numeric, empty, dep_other, no_enabled],
        models,
    )

    aliases = [entry['alias'] for entry in result]
    assert aliases[0] == 'same_group_same_name'
    assert aliases[1] == 'same_group_same_name_1'
    assert aliases[2] == 'reserved_np'
    assert aliases[3] == 'p_123_456'
    assert result[4]['display_name'] == '!!!'
    assert aliases[4] == 'param'
    assert result[5]['dependency'] == 'external+1'
    assert result[6]['enabled'] is True


def test_parameters_special_filters_and_invalid_variability_normalization(monkeypatch):
    project = make_project()
    logic = parameters_module.Parameters(project)
    mocked_parameters = [
        {'name': 'Cell length a', 'display_name': 'Cell length a', 'group': 'cell', 'unique_name': 'cell.a', 'fit': True, 'enabled': True, 'independent': True, 'alias': 'cell_a', 'object': object()},
        {'name': 'Atom site x', 'display_name': 'Atom site x', 'group': 'atom_site', 'unique_name': 'atom_site.x', 'fit': False, 'enabled': True, 'independent': True, 'alias': 'atom_site_x', 'object': object()},
        {'name': 'Biso', 'display_name': 'adp b_iso', 'group': 'thermal', 'unique_name': 'b_iso', 'fit': False, 'enabled': True, 'independent': True, 'alias': 'b_iso', 'object': object()},
        {'name': 'Instrument scale', 'display_name': 'Instrument scale', 'group': 'instrument', 'unique_name': 'scale', 'fit': True, 'enabled': True, 'independent': True, 'alias': 'scale', 'object': object()},
        {'name': 'Layer thickness', 'display_name': 'Layer thickness', 'group': 'layer', 'unique_name': 'layer.thickness', 'fit': True, 'enabled': True, 'independent': True, 'alias': 'thickness', 'object': object()},
    ]
    monkeypatch.setattr(logic, 'all_parameters', lambda: mocked_parameters)

    assert logic.set_variability_filter_criteria('INVALID') is False
    assert logic.variability_filter_criteria == 'all'

    logic.set_name_filter_criteria('model')
    assert [entry['display_name'] for entry in logic.parameters] == ['Cell length a', 'Atom site x', 'adp b_iso', 'Layer thickness']

    logic.set_name_filter_criteria('experiment')
    assert [entry['display_name'] for entry in logic.parameters] == ['Instrument scale']

    logic.set_name_filter_criteria('cell')
    assert [entry['display_name'] for entry in logic.parameters] == ['Cell length a']

    logic.set_name_filter_criteria('atom_site')
    assert [entry['display_name'] for entry in logic.parameters] == ['Atom site x']

    logic.set_name_filter_criteria('b_iso')
    assert [entry['display_name'] for entry in logic.parameters] == ['adp b_iso']


def test_parameter_current_selection_edge_cases_and_unsupported_constraint(monkeypatch, capsys):
    project = make_project()
    logic = parameters_module.Parameters(project)
    parameter = make_parameter(name='Scale', unique_name='scale', value=1.0, free=True)
    monkeypatch.setattr(
        logic,
        'all_parameters',
        lambda: [
            {
                'name': 'Scale',
                'display_name': 'Scale',
                'group': 'Instrument',
                'unique_name': 'scale',
                'fit': True,
                'enabled': True,
                'independent': True,
                'alias': 'scale',
                'object': parameter,
            }
        ],
    )

    assert logic.set_current_index(0) is False
    assert logic.set_current_index(5) is True
    assert logic.set_current_parameter_value('2.0') is False
    assert logic.set_current_parameter_min('0.2') is False
    assert logic.set_current_parameter_max('4.0') is False

    logic.set_current_index(0)
    assert logic.set_current_parameter_fit(True) is False

    dependent = make_parameter(name='Background', unique_name='background', value=0.5)
    project.parameters = [parameter, dependent]
    logic.add_constraint(1, '=', 2.0, '', 0)

    # NOTE: The production code reports this error via print(). If the error reporting
    # mechanism changes to logging, this assertion must be updated to use caplog instead.
    captured = capsys.readouterr()
    assert 'Unsupported type' in captured.out
    assert dependent.independent is True
