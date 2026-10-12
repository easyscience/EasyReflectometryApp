"""Removing an experiment through the Analysis backend, against the real library.

The selection and the current experiment are positions in the ordered experiment
list, while the library looks an experiment up by its key. These tests pin down
that after a removal the two still name the same data: what is selected is what
is plotted, under its own name.
"""

import numpy as np
import pytest
from easyreflectometry import Project
from easyreflectometry.data import DataSet1D
from easyscience import global_object

from EasyReflectometryApp.Backends.Py.analysis import Analysis
from EasyReflectometryApp.Backends.Py.plotting_1d import Plotting1d
from EasyReflectometryApp.Backends.Py.sample import Sample


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.map._clear()
    yield
    global_object.map._clear()


@pytest.fixture
def backends(qcore_application):
    project = Project()
    Sample(project)  # installs the default model
    project._experiments = {
        i: DataSet1D(
            name=f'E{i}',
            x=np.array([0.01, 0.02]),
            y=np.array([float(i + 1), float(i + 1)]),
            ye=np.array([0.1, 0.1]),
            model=project.models[0],
        )
        for i in range(3)
    }
    analysis = Analysis(project)
    plotting = Plotting1d(project, selection=analysis.selection)
    return project, analysis, plotting


def _plotted(plotting):
    return [(row['name'], row['data'].name, float(row['data'].y[0])) for row in plotting.individual_experiment_data_list]


def test_removing_the_first_experiment_keeps_the_selected_data_and_names(backends):
    project, analysis, plotting = backends
    analysis.setSelectedExperimentIndices([1, 2])
    assert _plotted(plotting) == [('E1', 'E1', 2.0), ('E2', 'E2', 3.0)]

    analysis.removeExperiment(0)

    assert analysis.selectedExperimentIndices == [0, 1]
    assert analysis.experimentsAvailable == ['E1', 'E2']
    assert _plotted(plotting) == [('E1', 'E1', 2.0), ('E2', 'E2', 3.0)]
    # The current experiment (single-experiment path) resolves too.
    assert project.current_experiment_index == 0
    assert project.experimental_data_for_model_at_index(project.current_experiment_index).name == 'E1'


def test_removing_a_middle_experiment_with_a_single_selection(backends):
    project, analysis, plotting = backends
    analysis.setSelectedExperimentIndices([2])

    analysis.removeExperiment(1)

    assert analysis.selectedExperimentIndices == [1]
    assert project.current_experiment_index == 1
    assert plotting.experiment_data.name == 'E2'
    assert _plotted(plotting) == [('E2', 'E2', 3.0)]


def test_removing_the_selected_experiment_selects_the_first_remaining_one(backends):
    project, analysis, plotting = backends
    analysis.setSelectedExperimentIndices([2])

    analysis.removeExperiment(2)

    assert analysis.selectedExperimentIndices == [0]
    assert plotting.experiment_data.name == 'E0'
    assert sorted(project._experiments) == [0, 1]
