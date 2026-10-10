"""Multi-contrast workflow against the real library: pairing, fit scope, contrasts, links, removal."""

import warnings

import numpy as np
import pytest
from easyreflectometry import Project
from easyreflectometry.data import DataSet1D
from easyscience import global_object

from EasyReflectometryApp.Backends.Py.experiment import Experiment
from EasyReflectometryApp.Backends.Py.logic.experiments import Experiments
from EasyReflectometryApp.Backends.Py.logic.fitting import Fitting
from EasyReflectometryApp.Backends.Py.logic.minimizers import Minimizers
from EasyReflectometryApp.Backends.Py.logic.parameters import Parameters
from EasyReflectometryApp.Backends.Py.sample import Sample

Q = np.linspace(0.01, 0.25, 30)


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.map._clear()
    yield
    global_object.map._clear()


@pytest.fixture
def project_and_sample(qcore_application):
    project = Project()
    sample = Sample(project)  # installs the default model: Air | D2O film | Si
    return project, sample


def _contrast(project, sample) -> None:
    """A second model of the same structure with the D2O replaced by H2O (a new palette material)."""
    from easyreflectometry.sample import Material

    project.add_material(Material(sld=-0.56, isld=0.0, name='H2O'))
    rows = sample.contrastCandidates(0)
    d2o = next(index for index, row in enumerate(rows) if row['label'] == 'D2O')
    result = sample.addContrast(0, 'H2O', [{'candidate': d2o, 'material': sample.materialNames.index('H2O')}])
    assert result == {'success': True, 'message': ''}


def _data(project, index, noise=0.01) -> DataSet1D:
    y = project.model_data_for_model_at_index(index, q_range=Q).y
    y = y * (1 + noise * np.random.default_rng(index).standard_normal(Q.size))
    return DataSet1D(name=f'data {index}', x=Q, y=y, ye=(0.02 * y) ** 2, model=project.models[index], auto_background=False)


class TestContrast:
    def test_add_contrast_shares_the_untouched_structure(self, project_and_sample):
        project, sample = project_and_sample
        _contrast(project, sample)
        reference, contrast = project.models
        assert contrast.name == 'H2O'
        assert contrast.sample[0] is reference.sample[0]  # superphase: no D2O in it
        assert contrast.sample[1].layers[0].material.name == 'H2O'
        assert project.current_model_index == 1
        sample.setCurrentModelIndex(1)
        assert sample.assemblies[0]['sharedWith'] == [reference.name]
        assert sample.assemblies[1]['sharedWith'] == []

    def test_the_new_contrast_becomes_the_edited_model(self, project_and_sample):
        project, sample = project_and_sample
        changed = []
        sample.assembliesTableChanged.connect(lambda: changed.append('assemblies'))
        _contrast(project, sample)
        assert sample.currentModelIndex == 1 and 'assemblies' in changed
        assert sample.assemblies[1]['label'] == project.models[1].sample[1].name

    def test_a_tied_shared_parameter_is_not_detached(self, project_and_sample):
        from easyreflectometry.constraints import constrain_equal

        project, sample = project_and_sample
        _contrast(project, sample)
        roughness = project.models[0].sample[2].layers[0].roughness  # substrate, shared
        constrain_equal(roughness, project.models[1].sample[1].layers[0].roughness)
        row = next(row for row in Parameters(project).parameters if row['unique_name'] == roughness.unique_name)
        assert not row['detachable']
        assert sample.detachParameter(roughness.unique_name, 1)['success'] is False
        assert not roughness.independent

    def test_an_empty_formula_keeps_the_reference_formula(self, project_and_sample):
        from easyreflectometry.sample import SurfactantLayer

        project, sample = project_and_sample
        project.models[0].add_assemblies(SurfactantLayer())
        rows = sample.contrastCandidates(0)
        tail = next(index for index, row in enumerate(rows) if row['kind'] == 'formula')
        assert sample.addContrast(0, 'same', [{'candidate': tail, 'formula': ''}])['success']
        assert sample.addContrast(0, 'bad', [{'candidate': tail, 'formula': 'C10H(('}])['success'] is False

    def test_unknown_substitution_is_reported(self, project_and_sample):
        project, sample = project_and_sample
        sample.contrastCandidates(0)
        result = sample.addContrast(0, 'x', [{'candidate': 0, 'formula': 'H2O'}])  # Air is not formula-based
        assert result['success'] is False

    def test_parameters_table_lists_a_shared_parameter_once(self, project_and_sample):
        project, sample = project_and_sample
        _contrast(project, sample)
        rows = Parameters(project).parameters
        names = [row['name'] for row in rows]
        shared = [row for row in rows if row['sharedBy']]
        assert shared and all(row['sharedBy'] == [project.models[0].name, 'H2O'] for row in shared)
        assert len(names) == len(set(names))
        # Only layer parameters can be given to one model alone; materials belong to the palette
        assert {row['detachable'] for row in shared} == {True, False}
        assert not any(row['detachable'] for row in shared if row['name'].endswith('sld'))

    def test_detach_gives_one_model_its_own_copy(self, project_and_sample):
        project, sample = project_and_sample
        _contrast(project, sample)
        roughness = project.models[0].sample[0].layers[0].roughness  # superphase, shared
        assert sample.detachParameter(roughness.unique_name, 1)['success']
        assert project.models[1].sample[0] is not project.models[0].sample[0]
        assert project.models[1].sample[0].layers[0].roughness.independent


class TestLinkModels:
    def test_ties_geometry_but_not_material_slds(self, project_and_sample):
        project, sample = project_and_sample
        project.models.duplicate_model(0)
        result = sample.constrainModelsParameters([0, 1], False)
        assert result['tied'] > 0 and result['messages'] == []
        follower, reference = project.models[1], project.models[0]
        film = follower.sample[1].layers[0]
        assert list(film.thickness.dependency_map.values()) == [reference.sample[1].layers[0].thickness]
        assert film.material.sld.independent

    def test_removing_a_linked_row_restores_the_parameter(self, project_and_sample):
        project, sample = project_and_sample
        project.models.duplicate_model(0)
        film = project.models[1].sample[1].layers[0]
        film.thickness.value = 120.0
        sample.constrainModelsParameters([0, 1], False)
        index = next(i for i, row in enumerate(sample.constraintsList) if row.get('uniqueName') == film.thickness.unique_name)

        sample.removeConstraintByIndex(index)

        assert film.thickness.independent
        assert film.thickness.value == pytest.approx(120.0)

    def test_different_layouts_are_reported(self, project_and_sample):
        project, sample = project_and_sample
        sample.addNewModel()  # Air | SiO2 | Si, one layer fewer than the default
        project.models[1].add_assemblies()
        result = sample.constrainModelsParameters([0, 1], False)
        assert result['tied'] == 0 and 'layout' in result['messages'][0]


class TestExperiments:
    def test_pairing_inclusion_and_removal(self, project_and_sample):
        project, sample = project_and_sample
        project.models.duplicate_model(0)
        project.experiments = {0: _data(project, 0), 1: _data(project, 0)}
        logic = Experiments(project)

        assert logic.set_model_on_experiment(1, 1)
        assert logic.model_indices() == [0, 1]
        assert logic.set_included_in_fit(0, False)
        assert logic.included_in_fit() == [False, True]

        assert sample.removeModel(1, 0) == []  # its experiment moves to the remaining model
        assert logic.model_indices() == [0, 0]
        logic.remove_experiment(0)
        assert [experiment.name for experiment in project.experiments.values()] == ['data 0']

    def test_removing_a_model_with_its_experiments_moves_the_selection(self, qcore_application):
        from EasyReflectometryApp.Backends.Py.py_backend import PyBackend

        backend = PyBackend()
        project = backend._project_lib
        project.models.duplicate_model(0)
        project.experiments = {0: _data(project, 1), 1: _data(project, 0), 2: _data(project, 0)}
        backend.analysis.setSelectedExperimentIndices([1, 2])

        assert backend.sample.removeModel(1, -1) == [0]

        # The two remaining experiments are still the selected ones, now at 0 and 1
        assert backend.analysis.selectedExperimentIndices == [0, 1]
        assert [experiment.name for experiment in project.experiments.values()] == ['data 0', 'data 0']

    def test_a_file_that_cannot_be_read_is_reported(self, project_and_sample, tmp_path):
        project, _ = project_and_sample
        broken = tmp_path / 'broken.ort'
        broken.write_text('# ORSO reflectivity data file | not really\nnonsense')
        backend = Experiment(project)
        failures = []
        backend.loadFailed.connect(failures.append)
        backend.load(str(broken))
        assert failures and 'broken.ort' in failures[0]
        assert project.experiments == {}


def test_a_two_contrast_fit_is_recorded_per_dataset(project_and_sample):
    project, sample = project_and_sample
    _contrast(project, sample)
    for model in project.models:
        model.scale.fixed = False
    project.experiments = {0: _data(project, 0), 1: _data(project, 1)}
    logic = Fitting(project)

    prepared = logic.prepare_threaded_fit(Minimizers(project))
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        results = prepared.execute()
    logic.on_fit_finished(results)
    logic.record_on_project(results)

    assert logic.fit_n_pars == 2
    assert [row['name'] for row in logic.fit_dataset_rows] == ['data 0', 'data 1']
    assert sum(row['share'] for row in logic.fit_dataset_rows) == pytest.approx(1.0)
