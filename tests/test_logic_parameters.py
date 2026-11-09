from EasyReflectometryApp.Backends.Py.logic import parameters as parameters_module
from tests.factories import FakeModel
from tests.factories import FakeParameter
from tests.factories import make_model
from tests.factories import make_model_collection
from tests.factories import make_parameter
from tests.factories import make_project


class FakeNode:
    """Minimal stand-in for an easyscience ModelBase container in the object tree.

    The new core no longer populates the global_object.map graph, so
    ``_from_parameters_to_list_of_dicts`` walks the model object tree
    instead. These nodes let the tests build that tree from named
    containers (assemblies, materials, ...) holding Parameters and
    sub-collections.
    """

    def __init__(self, name, unique_name, **children):
        self.name = name
        self.unique_name = unique_name
        for key, value in children.items():
            setattr(self, key, value)


class FakeLayerNode(FakeNode):
    """Stand-in for a library ``Layer``: its thickness and roughness are per-layer parameters."""


class FakeMagnetismNode(FakeNode):
    """Stand-in for a library ``LayerMagnetism``."""


def _patch_tree_types(monkeypatch):
    # The traversal uses module-level `Parameter`/`ModelBase` for isinstance
    # checks, and `Layer`/`LayerMagnetism` to classify parameters; point them
    # at the test fakes so the fake tree is walkable.
    monkeypatch.setattr(parameters_module, 'Parameter', FakeParameter)
    monkeypatch.setattr(parameters_module, 'ModelBase', FakeNode)
    monkeypatch.setattr(parameters_module, 'Layer', FakeLayerNode)
    monkeypatch.setattr(parameters_module, 'LayerMagnetism', FakeMagnetismNode)


def test_from_parameters_to_list_of_dicts_marks_decoupled_density_knobs_inactive(monkeypatch):
    _patch_tree_types(monkeypatch)

    density = make_parameter(name='density', unique_name='density', value=2.33, free=True, enabled=True)
    # molecular_weight is intentionally absent: in the lib it is a
    # DescriptorNumber (a formula constant), so the Parameter tree walk
    # never yields it. The scattering length stands in as the second knob.
    b_real = make_parameter(name='scattering_length_real', unique_name='b_real', value=4.15, free=False, enabled=True)
    thickness = make_parameter(name='thickness', unique_name='thickness', value=20.0, free=True, enabled=True)

    def build_model(sld_coupled):
        model = make_model(name='M1 internal', unique_name='m1', user_data={'original_name': 'M1'})
        layer = FakeLayerNode('Layer', 'm1_layer', thickness=thickness, roughness=None)
        assembly = FakeNode('LayerA', 'm1_asm', layers=[layer])
        model.sample = [assembly]
        # Density-material knobs live under the material node, which carries
        # the sld_coupled toggle (duck-typed stand-in for MaterialDensity).
        material = FakeNode('SiDensity', 'm1_mat', density=density, scattering_length_real=b_real)
        material.sld_coupled = sld_coupled
        model.material = material
        return model

    decoupled = parameters_module._from_parameters_to_list_of_dicts(
        [density, b_real, thickness], make_model_collection(build_model(sld_coupled=False))
    )
    rows = {entry['display_name']: entry for entry in decoupled}
    for label in ('SiDensity density', 'SiDensity scattering_length_real'):
        assert rows[label]['kind'] == 'inactive'
        assert rows[label]['fit'] is False
        assert rows[label]['readOnly'] is True
        assert rows[label]['enabled'] is True  # greyed, never filtered out
        assert rows[label]['dependency'] == 'unused (SLD is fitted directly)'
    # Non-knob parameters are untouched.
    assert rows['M1 LayerA thickness']['kind'] == 'parameter'
    assert rows['M1 LayerA thickness']['fit'] is True

    coupled = parameters_module._from_parameters_to_list_of_dicts(
        [density, b_real, thickness], make_model_collection(build_model(sld_coupled=True))
    )
    rows = {entry['display_name']: entry for entry in coupled}
    assert rows['SiDensity density']['kind'] == 'parameter'
    assert rows['SiDensity density']['fit'] is True
    assert rows['SiDensity scattering_length_real']['kind'] == 'parameter'


def test_from_parameters_to_list_of_dicts_prefixes_layers_and_deduplicates_shared_params(monkeypatch):
    _patch_tree_types(monkeypatch)

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

    def build_model(unique_name, original_name, with_background):
        model = make_model(
            name=f'{original_name} internal', unique_name=unique_name, user_data={'original_name': original_name}
        )
        # Model -> sample -> assembly -> layers -> layer -> thickness (a layer parameter)
        layer = FakeLayerNode('Layer', f'{unique_name}_layer', thickness=thickness, roughness=None)
        assembly = FakeNode('LayerA', f'{unique_name}_asm', layers=[layer])
        model.sample = [assembly]
        # Non-layer params (scale, background) live under a shared 'Instrument' parent
        instrument = FakeNode('Instrument', f'{unique_name}_instr', scale=scale)
        if with_background:
            instrument.background = dependent
        model.instrument = instrument
        return model

    models = make_model_collection(
        build_model('m1', 'M1', with_background=True),
        build_model('m2', 'M2', with_background=False),
    )

    result = parameters_module._from_parameters_to_list_of_dicts([thickness, scale, dependent], models)

    # The thickness is one object in both models: one row, named for both, and marked shared
    assert [entry['display_name'] for entry in result] == [
        'M1+M2 LayerA thickness',
        'Instrument scale',
        'Instrument background',
    ]
    assert result[1]['dependency'] == ''
    assert result[2]['dependency'] == '2*Instrument scale'
    assert result[2]['enabled'] is False
    assert result[0]['alias'] == 'm1_m2_layera_thickness'
    assert result[0]['sharedBy'] == ['M1', 'M2'] and result[0]['sharedByIndices'] == [0, 1]
    assert result[2]['sharedBy'] == [] and result[1]['followedBy'] == 0


def test_layer_alias_attributes_do_not_shortcut_the_canonical_path(monkeypatch):
    """Real assemblies expose ``front_layer``/``back_layer`` properties that
    alias into ``layers`` and sort *before* it in ``dir()`` order. The canonical
    Model -> sample -> assembly -> layers -> layer chain must win the recorded
    path; otherwise ``path[-4]`` (expected: the assembly) resolves to the wrong
    ancestor and superphase/subphase parameters get mislabelled."""
    _patch_tree_types(monkeypatch)

    thickness = make_parameter(name='thickness', unique_name='thickness', value=20.0, free=True, enabled=True)
    roughness = make_parameter(name='roughness', unique_name='roughness', value=3.0, free=True, enabled=True)

    model = make_model(name='M1 internal', unique_name='m1', user_data={'original_name': 'M1'})
    layer = FakeLayerNode('Layer', 'layer', thickness=thickness, roughness=roughness)
    assembly = FakeNode(
        'Superphase', 'asm',
        back_layer=layer,   # alias, sorts before 'layers'
        front_layer=layer,  # alias, sorts before 'layers'
        layers=[layer],     # canonical container
    )
    model.sample = [assembly]
    models = make_model_collection(model)

    result = parameters_module._from_parameters_to_list_of_dicts([thickness, roughness], models)

    assert [entry['display_name'] for entry in result] == [
        'M1 Superphase thickness',
        'M1 Superphase roughness',
    ]
    assert all(entry['group'] == 'Superphase' for entry in result)


def test_from_parameters_to_list_of_dicts_classifies_by_owner_not_by_name(monkeypatch):
    _patch_tree_types(monkeypatch)

    scale = make_parameter(name='scale', unique_name='scale')
    background = make_parameter(name='background', unique_name='background')
    thickness = make_parameter(name='thickness', unique_name='thickness')
    rho_m = make_parameter(name='rho_m', unique_name='rho_m')
    # Named like experiment and layer parameters, but owned by a material.
    impostor = make_parameter(name='thickness', unique_name='impostor')
    scale_named = make_parameter(name='scale', unique_name='scale_named')

    model = make_model(name='M1 internal', unique_name='m1', user_data={'original_name': 'M1'})
    model.scale = scale
    model.background = background
    magnetism = FakeMagnetismNode('EasyLayerMagnetism', 'mag', rho_m=rho_m)
    layer = FakeLayerNode('Layer', 'layer', thickness=thickness, roughness=None, magnetism=magnetism)
    model.sample = [FakeNode('Film', 'asm', layers=[layer])]
    model.material = FakeNode('Background Material', 'mat', thickness=impostor, scale=scale_named)

    result = parameters_module._from_parameters_to_list_of_dicts(
        [scale, background, thickness, rho_m, impostor, scale_named], make_model_collection(model)
    )
    rows = {entry['unique_name']: entry for entry in result}

    assert {name for name, row in rows.items() if row['experiment']} == {'scale', 'background'}
    assert rows['thickness']['display_name'] == 'M1 Film thickness'
    assert rows['rho_m']['display_name'] == 'M1 Film rho_m'
    assert rows['impostor']['display_name'] == 'Background Material thickness'
    assert rows['scale_named']['display_name'] == 'Background Material scale'


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
        {
            'alias': 'hidden_background',
            'displayName': 'Hidden background',
            'group': 'Experiment',
            'independent': True,
            'kind': 'parameter',
        },
        {
            'alias': 'instrument_scale',
            'displayName': 'Instrument scale',
            'group': 'Instrument',
            'independent': True,
            'kind': 'parameter',
        },
        {
            'alias': 'layer_thickness',
            'displayName': 'Layer thickness',
            'group': 'Layer',
            'independent': False,
            'kind': 'parameter',
        },
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


def test_set_current_parameter_fit_refuses_inactive_row(monkeypatch):
    """An inactive density knob must not be tickable into the fit through
    any caller, QML checkbox or not — same class of bug the Select-All skip
    fixed for the fittables table."""
    project = make_project()
    logic = parameters_module.Parameters(project)
    inactive_parameter = make_parameter(name='Density', unique_name='density', value=2.33, free=False)
    mocked_parameters = [
        {
            'display_name': 'SiDensity density',
            'unique_name': 'density',
            'kind': 'inactive',
            'enabled': True,
            'object': inactive_parameter,
        },
    ]
    monkeypatch.setattr(logic, 'all_parameters', lambda: mocked_parameters)

    logic.set_current_index(0)
    assert logic.set_current_parameter_fit(True) is False
    assert inactive_parameter.free is False


def test_from_parameters_to_list_of_dicts_handles_alias_edge_cases_and_fallbacks(monkeypatch):
    _patch_tree_types(monkeypatch)

    param1 = make_parameter(name='Same Name', unique_name='p1')
    param2 = make_parameter(name='Same Name', unique_name='p2')
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
    no_enabled = make_parameter(name='visible', unique_name='no_enabled', value=2.0)
    del no_enabled.enabled  # exercise the missing-`enabled` fallback (-> True)

    model = make_model(name='M1', unique_name='m1', user_data={'original_name': 'M1'})
    # Each parameter sits under a named container so its display name and
    # alias derive from `<parent name> <parameter name>`.
    model.groups = [
        FakeNode('Same Group', 'sg', p1=param1, p2=param2),
        FakeNode('Reserved', 'res', r=reserved),
        FakeNode('123', 'num', n=numeric),
        FakeNode('', 'empty_parent', e=empty),
        FakeNode('DepGroup', 'depg', d=dep_other),
        FakeNode('Visible', 'vis', v=no_enabled),
    ]
    models = make_model_collection(model)

    result = parameters_module._from_parameters_to_list_of_dicts(
        [param1, param2, reserved, numeric, empty, dep_other, no_enabled],
        models,
    )

    aliases = [entry['alias'] for entry in result]
    assert aliases[0] == 'same_group_same_name'
    assert aliases[1] == 'same_group_same_name_1'
    assert aliases[2] == 'reserved_np'
    assert aliases[3] == 'p_123_456'
    assert result[4]['display_name'].endswith('!!!')
    assert aliases[4] == 'param'
    assert result[5]['dependency'] == 'external+1'
    assert result[6]['enabled'] is True


class _FakeModelWithTotalThickness(FakeModel):
    """FakeModel with the derived ``total_thickness`` the lib's Model exposes as a property."""

    _total_thickness = None

    @property
    def total_thickness(self):
        return self._total_thickness


def _build_snapshot_scenario():
    """Two contrasts covering every branch the row builder takes.

    M1 and M2 share one Film assembly (so its layer is one object in both):
    its layer is magnetic and takes rho_m from Fe, a density material with
    a decoupled nuclear SLD. M2 also owns a Substrate whose Ni material has
    a moment that no layer takes. Each model has its own experiment
    parameters; M2's scale follows M1's (a tie between contrasts) and M1's
    background is a numerical dependency.
    """
    p = make_parameter

    fe_density = p(name='density', unique_name='fe_density', value=7.87, variance=0.04, free=True)
    fe_moment = p(name='magnetic_moment', unique_name='fe_moment', value=2.2, free=True)
    fe_b_real = p(name='scattering_length_real', unique_name='fe_b_real', value=9.45)
    fe_magnetic_sld = p(name='magnetic_sld', unique_name='fe_magnetic_sld', value=5.1, unit='1/angstrom^2')
    fe = FakeNode(
        'Fe',
        'fe',
        density=fe_density,
        magnetic_moment=fe_moment,
        scattering_length_real=fe_b_real,
        rho_m=fe_magnetic_sld,
    )
    fe.sld_coupled = False

    ni_moment = p(name='magnetic_moment', unique_name='ni_moment', value=0.6, free=True)
    ni = FakeNode('Ni', 'ni', magnetic_moment=ni_moment)
    ni.sld_coupled = True

    film_thickness = p(name='thickness', unique_name='film_thickness', value=50.0, unit='angstrom', free=True)
    film_roughness = p(name='roughness', unique_name='film_roughness', value=3.0, unit='angstrom')
    film_rho_m = p(name='rho_m', unique_name='film_rho_m', value=1.0)
    film_theta_m = p(name='theta_m', unique_name='film_theta_m', value=270.0, unit='deg')
    film_layer = FakeLayerNode(
        'Film Layer',
        'film_layer',
        thickness=film_thickness,
        roughness=film_roughness,
        material=fe,
        magnetism=FakeMagnetismNode('EasyLayerMagnetism', 'film_mag', rho_m=film_rho_m, theta_m=film_theta_m),
    )
    film_layer.rho_m_coupled = True
    film = FakeNode('Film', 'film', layers=[film_layer])

    sub_thickness = p(name='thickness', unique_name='sub_thickness', value=0.0, unit='angstrom')
    sub_roughness = p(name='roughness', unique_name='sub_roughness', value=2.0, unit='angstrom', free=True)
    sub_layer = FakeLayerNode('Ni Layer', 'sub_layer', thickness=sub_thickness, roughness=sub_roughness, material=ni)
    substrate = FakeNode('Substrate', 'substrate', layers=[sub_layer])

    def build_model(index, assemblies):
        model = _FakeModelWithTotalThickness(
            name=f'M{index} internal', unique_name=f'm{index}', user_data={'original_name': f'M{index}'}
        )
        model.sample = assemblies
        model.scale = p(name='scale', unique_name=f'm{index}_scale', value=1.0, minimum=0.5, maximum=2.0, free=True)
        model.background = p(name='background', unique_name=f'm{index}_background', value=1e-6, maximum=1.0)
        model._total_thickness = p(name='total_thickness', unique_name=f'm{index}_total', value=50.0)
        return model

    m1 = build_model(1, [film])
    m2 = build_model(2, [film, substrate])
    m1.background.independent = False  # numerical dependency: '= <value>'
    m2.scale.make_dependent_on('a', {'a': m1.scale})  # a tie between contrasts

    parameters = [
        m1.scale, m1.background, m2.scale, m2.background, m1._total_thickness, m2._total_thickness,
        film_thickness, film_roughness, film_rho_m, film_theta_m,
        fe_density, fe_moment, fe_b_real, fe_magnetic_sld,
        sub_thickness, sub_roughness, ni_moment,
    ]  # fmt: skip
    return parameters, make_model_collection(m1, m2)


def test_from_parameters_to_list_of_dicts_snapshot(monkeypatch):
    """Every key of every row, for a scenario that takes each branch: the
    guard for refactoring the row builder. ``object`` and ``exclusive_with``
    hold live Parameters, so they are checked by identity, not by value."""
    _patch_tree_types(monkeypatch)
    parameters, models = _build_snapshot_scenario()

    result = parameters_module._from_parameters_to_list_of_dicts(parameters, models)

    by_unique_name = {parameter.unique_name: parameter for parameter in parameters}
    for row in result:
        assert row['object'] is by_unique_name[row['unique_name']]
    exclusive = {row['unique_name']: getattr(row['exclusive_with'], 'unique_name', None) for row in result}
    assert exclusive == {name: None for name in exclusive} | {
        'fe_density': 'fe_moment',
        'fe_moment': 'fe_density',
    }

    snapshot = [{key: value for key, value in row.items() if key not in ('object', 'exclusive_with')} for row in result]
    assert snapshot == _EXPECTED_SNAPSHOT


def _row(unique_name, display_name, group, alias, value, **overrides):
    """An expected row: the defaults of a plain, unshared, fixed model parameter, plus ``overrides``."""
    row = {
        'name': display_name,
        'display_name': display_name,
        'group': group,
        'alias': alias,
        'unique_name': unique_name,
        'value': value,
        'error': 0.0,
        'max': 100.0,
        'min': 0.0,
        'units': '',
        'fit': False,
        'independent': True,
        'dependency': '',
        'kind': 'parameter',
        'readOnly': False,
        'enabled': True,
        'sharedBy': [],
        'sharedByIndices': [],
        'detachable': False,
        'followedBy': 0,
        'experiment': False,
    }
    unknown = set(overrides) - set(row)
    assert not unknown, f'unknown row keys: {unknown}'
    row.update(overrides)
    return row


_SHARED = {'sharedBy': ['M1', 'M2'], 'sharedByIndices': [0, 1]}
_SHARED_LAYER = {**_SHARED, 'detachable': True, 'units': 'angstrom'}
_EXPERIMENT = {'experiment': True}
_DERIVED = {'kind': 'derived', 'readOnly': True, 'dependency': 'Σ film layer thicknesses'}

# Rows come grouped by the first model that owns them, in model order.
_EXPECTED_SNAPSHOT = [
    # M1
    _row('m1_scale', 'M1 internal scale', 'M1 internal', 'm1_internal_scale', 1.0,
         min=0.5, max=2.0, fit=True, followedBy=1, **_EXPERIMENT),
    _row('m1_background', 'M1 internal background', 'M1 internal', 'm1_internal_background', 1e-06,
         max=1.0, independent=False, dependency='= 1e-06', **_EXPERIMENT),
    _row('m1_total', 'M1 internal total_thickness', 'M1 internal', 'm1_internal_total_thickness', 50.0, **_DERIVED),
    _row('film_thickness', 'M1+M2 Film thickness', 'Film', 'm1_m2_film_thickness', 50.0, fit=True, **_SHARED_LAYER),
    _row('film_roughness', 'M1+M2 Film roughness', 'Film', 'm1_m2_film_roughness', 3.0, **_SHARED_LAYER),
    _row('film_rho_m', 'M1+M2 Film rho_m', 'Film', 'm1_m2_film_rho_m', 1.0, **_SHARED, detachable=True),
    _row('film_theta_m', 'M1+M2 Film theta_m', 'Film', 'm1_m2_film_theta_m', 270.0,
         **_SHARED, detachable=True, units='deg'),
    # Fe drives the film's rho_m, so its density stays active though its SLD is decoupled
    _row('fe_density', 'Fe density', 'Fe', 'fe_density', 7.87, error=0.2, fit=True, **_SHARED),
    _row('fe_moment', 'Fe magnetic_moment', 'Fe', 'fe_magnetic_moment', 2.2, fit=True, **_SHARED),
    _row('fe_b_real', 'Fe scattering_length_real', 'Fe', 'fe_scattering_length_real', 9.45,
         kind='inactive', readOnly=True, dependency='unused (SLD is fitted directly)', **_SHARED),
    _row('fe_magnetic_sld', 'Fe material rho_m', 'Fe', 'fe_material_rho_m', 5.1, units='1/angstrom^2', **_SHARED),
    # M2
    # The leader (M1's scale) is not in M2's tree, so its display name falls
    # back to the bare parameter name rather than 'M1 internal scale'.
    _row('m2_scale', 'M2 internal scale', 'M2 internal', 'm2_internal_scale', 1.0,
         min=0.5, max=2.0, fit=True, independent=False, dependency='scale', **_EXPERIMENT),
    _row('m2_background', 'M2 internal background', 'M2 internal', 'm2_internal_background', 1e-06,
         max=1.0, **_EXPERIMENT),
    _row('m2_total', 'M2 internal total_thickness', 'M2 internal', 'm2_internal_total_thickness', 50.0, **_DERIVED),
    _row('sub_thickness', 'M2 Substrate thickness', 'Substrate', 'm2_substrate_thickness', 0.0, units='angstrom'),
    _row('sub_roughness', 'M2 Substrate roughness', 'Substrate', 'm2_substrate_roughness', 2.0,
         units='angstrom', fit=True),
    # Free, but no layer takes rho_m from Ni: shown inactive and unfittable
    _row('ni_moment', 'Ni magnetic_moment', 'Ni', 'ni_magnetic_moment', 0.6,
         kind='inactive', readOnly=True, dependency='unused (no layer takes ρM from this material)'),
]  # fmt: skip


def _filter_row(name, display_name, group, unique_name, alias, fit, experiment=False):
    """A parameter row as ``all_parameters`` returns it, with only the keys the filters read."""
    return {
        'name': name,
        'display_name': display_name,
        'group': group,
        'unique_name': unique_name,
        'fit': fit,
        'enabled': True,
        'independent': True,
        'alias': alias,
        'object': object(),
        'experiment': experiment,
    }


def test_parameters_special_filters_and_invalid_variability_normalization(monkeypatch):
    project = make_project()
    logic = parameters_module.Parameters(project)
    mocked_parameters = [
        _filter_row('Cell length a', 'Cell length a', 'cell', 'cell.a', 'cell_a', fit=True),
        _filter_row('Atom site x', 'Atom site x', 'atom_site', 'atom_site.x', 'atom_site_x', fit=False),
        _filter_row('Biso', 'adp b_iso', 'thermal', 'b_iso', 'b_iso', fit=False),
        _filter_row('Instrument scale', 'Instrument scale', 'instrument', 'scale', 'scale', fit=True, experiment=True),
        _filter_row('Layer thickness', 'Layer thickness', 'layer', 'layer.thickness', 'thickness', fit=True),
    ]
    monkeypatch.setattr(logic, 'all_parameters', lambda: mocked_parameters)

    assert logic.set_variability_filter_criteria('INVALID') is False
    assert logic.variability_filter_criteria == 'all'

    logic.set_name_filter_criteria('model')
    assert [entry['display_name'] for entry in logic.parameters] == [
        'Cell length a', 'Atom site x', 'adp b_iso', 'Layer thickness',
    ]

    logic.set_name_filter_criteria('experiment')
    assert [entry['display_name'] for entry in logic.parameters] == ['Instrument scale']

    # Any other word is a plain text match.
    logic.set_name_filter_criteria('atom_site')
    assert [entry['display_name'] for entry in logic.parameters] == ['Atom site x']


def test_parameter_current_selection_edge_cases(monkeypatch):
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
