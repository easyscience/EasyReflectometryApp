"""Superphase/subphase enablement under layer edits (issue #329).

The superphase is the first layer of the first assembly and the subphase the
last layer of the last assembly, so editing the layers inside those assemblies
moves which parameters are fixed. These tests use the real reflectometry
library because enablement lives on its parameters.
"""

import pytest
from easyreflectometry import Project
from easyscience import global_object

from EasyReflectometryApp.Backends.Py.sample import Sample


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.map._clear()
    yield
    global_object.map._clear()


@pytest.fixture
def project_and_backend(qcore_application):
    project = Project()
    backend = Sample(project)  # installs the default model
    return project, backend


def _enabled(parameter):
    # The attribute appears only once enablement has run over the parameter.
    return getattr(parameter, 'enabled', True)


def _flags(layer):
    return _enabled(layer.thickness), _enabled(layer.roughness)


def _assert_only_fixed_layers_disabled(project):
    sample = project.models[0].sample
    for a, assembly in enumerate(sample):
        for i, layer in enumerate(assembly.layers):
            is_superphase = a == 0 and i == 0
            is_subphase = a == len(sample) - 1 and i == len(assembly.layers) - 1
            assert _enabled(layer.thickness) is not (is_superphase or is_subphase), (a, i)
            assert _enabled(layer.roughness) is not is_superphase, (a, i)


def _assert_table_matches_parameters(project, backend):
    layers = project.models[0].sample[project.current_assembly_index].layers
    rows = backend.layers
    assert [row['thickness_enabled'] for row in rows] == [str(_enabled(layer.thickness)) for layer in layers]
    assert [row['roughness_enabled'] for row in rows] == [str(_enabled(layer.roughness)) for layer in layers]


def test_table_treats_a_parameter_without_enablement_as_editable(project_and_backend):
    project, backend = project_and_backend
    layer = project.models[0].sample[1].layers[0]
    del layer.thickness.enabled
    backend.setCurrentAssemblyIndex(1)
    backend.layersConnectChanges()

    assert backend.layers[0]['thickness_enabled'] == 'True'


class TestSuperphaseLayerEdits:
    def test_added_layer_moved_to_top_becomes_the_superphase(self, project_and_backend):
        project, backend = project_and_backend
        backend.setCurrentAssemblyIndex(0)
        original = project.models[0].sample[0].layers[0]

        backend.addNewLayer()
        added = project.models[0].sample[0].layers[1]
        _assert_only_fixed_layers_disabled(project)
        assert _flags(added) == (True, True)

        backend.setCurrentLayerIndex(1)
        backend.moveSelectedLayerUp()

        assert project.models[0].sample[0].layers[0] is added
        assert _flags(added) == (False, False)
        assert _flags(original) == (True, True)
        _assert_only_fixed_layers_disabled(project)
        _assert_table_matches_parameters(project, backend)

    def test_move_down_hands_the_superphase_to_the_next_layer(self, project_and_backend):
        project, backend = project_and_backend
        backend.setCurrentAssemblyIndex(0)
        backend.addNewLayer()
        original = project.models[0].sample[0].layers[0]

        backend.setCurrentLayerIndex(0)
        backend.moveSelectedLayerDown()

        assert _flags(original) == (True, True)
        _assert_only_fixed_layers_disabled(project)
        _assert_table_matches_parameters(project, backend)

    def test_duplicated_superphase_copy_is_editable(self, project_and_backend):
        project, backend = project_and_backend
        backend.setCurrentAssemblyIndex(0)
        backend.setCurrentLayerIndex(0)

        backend.duplicateSelectedLayer()

        assert len(project.models[0].sample[0].layers) == 2
        _assert_only_fixed_layers_disabled(project)
        _assert_table_matches_parameters(project, backend)

    def test_removing_the_superphase_layer_fixes_its_successor(self, project_and_backend):
        project, backend = project_and_backend
        backend.setCurrentAssemblyIndex(0)
        backend.addNewLayer()
        successor = project.models[0].sample[0].layers[1]

        backend.removeLayer(0)

        assert project.models[0].sample[0].layers[0] is successor
        assert _flags(successor) == (False, False)
        _assert_only_fixed_layers_disabled(project)
        _assert_table_matches_parameters(project, backend)


class TestSubphaseLayerEdits:
    def test_added_layer_becomes_the_subphase(self, project_and_backend):
        project, backend = project_and_backend
        last = len(project.models[0].sample) - 1
        backend.setCurrentAssemblyIndex(last)
        original = project.models[0].sample[last].layers[-1]

        backend.addNewLayer()

        added = project.models[0].sample[last].layers[-1]
        assert added is not original
        assert _flags(added) == (False, True)
        assert _flags(original) == (True, True)
        _assert_only_fixed_layers_disabled(project)
        _assert_table_matches_parameters(project, backend)

    def test_move_up_hands_the_subphase_back(self, project_and_backend):
        project, backend = project_and_backend
        last = len(project.models[0].sample) - 1
        backend.setCurrentAssemblyIndex(last)
        original = project.models[0].sample[last].layers[-1]
        backend.addNewLayer()

        backend.setCurrentLayerIndex(1)
        backend.moveSelectedLayerUp()

        assert project.models[0].sample[last].layers[-1] is original
        assert _flags(original) == (False, True)
        _assert_only_fixed_layers_disabled(project)
        _assert_table_matches_parameters(project, backend)


def test_middle_assembly_table_is_fully_editable(project_and_backend):
    project, backend = project_and_backend
    backend.setCurrentAssemblyIndex(1)
    backend.addNewLayer()

    assert all(row['thickness_enabled'] == 'True' for row in backend.layers)
    assert all(row['roughness_enabled'] == 'True' for row in backend.layers)
    _assert_only_fixed_layers_disabled(project)
