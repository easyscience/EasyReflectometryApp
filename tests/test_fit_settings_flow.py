"""Fit settings from the Analysis page to the run the worker executes, and through a save/load.

Uses the real library: these are the gap-1 and gap-3 behaviours (settings
dropped before the first fit, a saved minimizer not shown after a load).
"""

import numpy as np
import pytest
from easyreflectometry import Project as RealProject
from easyscience import AvailableMinimizers
from easyscience import global_object

from EasyReflectometryApp.Backends.Py.analysis import Analysis
from EasyReflectometryApp.Backends.Py.logic.fitting import Fitting
from EasyReflectometryApp.Backends.Py.logic.minimizers import APP_DEFAULT_MINIMIZER
from EasyReflectometryApp.Backends.Py.logic.minimizers import Minimizers
from EasyReflectometryApp.Backends.Py.logic.project import Project as ProjectLogic


@pytest.fixture(autouse=True)
def _clean_map():
    global_object.map._clear()
    yield
    global_object.map._clear()


def _project_with_experiment(tmp_path) -> RealProject:
    project = RealProject()
    project.default_model()
    q = np.linspace(0.01, 0.2, 20)
    reflectivity = np.exp(-q * 30)
    path = tmp_path / 'data.dat'
    np.savetxt(path, np.column_stack([q, reflectivity, 0.01 * reflectivity]))
    project.load_new_experiment(str(path))
    return project


def _index(minimizers: Minimizers, name: str) -> int:
    return minimizers.minimizers_available().index(name)


def test_settings_edited_before_any_fit_reach_the_run(tmp_path):
    project = _project_with_experiment(tmp_path)
    minimizers = Minimizers(project)
    assert project._fitter is None  # nothing has been fitted yet

    minimizers.set_tolerance(1e-4)
    minimizers.set_max_iterations(321)
    prepared = Fitting(project).prepare_threaded_fit(minimizers)

    # A new library project fits with LMFit, whose tolerance travels per call
    assert prepared.call_kwargs() == {'minimizer_kwargs': {'ftol': 1e-4}}
    assert prepared.core_fitter.max_evaluations == 321


def test_nothing_set_means_the_engine_default(tmp_path):
    # The app used to send 1e-6 / 5000 whenever no fitter was cached.
    project = _project_with_experiment(tmp_path)

    prepared = Fitting(project).prepare_threaded_fit(Minimizers(project))

    assert prepared.core_fitter.tolerance is None
    assert prepared.call_kwargs() == {}
    assert prepared.core_fitter.max_evaluations is None


def test_analysis_edits_dirty_the_project_and_invalid_ones_are_reported(tmp_path, qcore_application):
    project = _project_with_experiment(tmp_path)
    analysis = Analysis(project)
    saved, refused = [], []
    analysis.externalFitSettingsChanged.connect(lambda: saved.append(True))
    analysis.prefitCheckFailed.connect(lambda title, message: refused.append(message))

    analysis.setMinimizerTolerance(1e-4)
    assert analysis.minimizerTolerance == 1e-4
    assert saved == [True]

    analysis.setMinimizerTolerance(-1.0)
    assert analysis.minimizerTolerance == 1e-4
    assert saved == [True]
    assert 'Tolerance' in refused[0]

    analysis.resetMinimizerTolerance()
    assert analysis.minimizerTolerance is None
    assert len(saved) == 2

    analysis.setFitObjective('legacy_mask')
    assert project.fit_settings.objective == 'legacy_mask'


def test_a_saved_minimizer_is_shown_after_loading(tmp_path):
    project = _project_with_experiment(tmp_path)
    minimizers = Minimizers(project)
    minimizers.set_minimizer_current_index(_index(minimizers, 'LMFit_cobyla'))
    minimizers.set_tolerance(1e-5)
    project_dict = project.as_dict()

    global_object.map._clear()
    loaded = RealProject()
    loaded.from_dict(project_dict)
    loaded_minimizers = Minimizers(loaded)

    assert loaded_minimizers.minimizer_current_index() == _index(loaded_minimizers, 'LMFit_cobyla')
    assert loaded_minimizers.tolerance == 1e-5


def test_bayesian_choice_survives_a_save():
    project = RealProject()
    project.default_model()
    Minimizers(project).set_minimizer_current_index(0)
    project_dict = project.as_dict()

    global_object.map._clear()
    loaded = RealProject()
    loaded.from_dict(project_dict)

    assert Minimizers(loaded).is_bayesian_selected() is True


def test_new_and_reset_projects_get_the_app_default_but_a_load_keeps_its_own():
    project = RealProject()
    logic = ProjectLogic(project)
    assert project.minimizer is APP_DEFAULT_MINIMIZER

    project.minimizer = AvailableMinimizers.LMFit_powell
    logic.reset()
    assert project.minimizer is APP_DEFAULT_MINIMIZER


def test_differential_evolution_needs_finite_bounds_of_free_parameters(tmp_path, qcore_application):
    project = _project_with_experiment(tmp_path)
    analysis = Analysis(project)
    scale = project.models[0].scale
    scale.fixed = False
    scale.max = np.inf
    analysis._chached_parameters = None

    analysis.setMinimizerCurrentIndex(_index(analysis._minimizers_logic, 'LMFit_differential_evolution'))

    assert analysis.minimizerRequiresFiniteBounds is True
    assert analysis.unboundedFreeParametersCount >= 1
    assert any('does not allow' in error for error in analysis._prefit_errors())


def test_switching_to_a_minimizer_the_settings_do_not_suit_warns_at_once(tmp_path, qcore_application):
    project = _project_with_experiment(tmp_path)
    analysis = Analysis(project)
    refused = []
    analysis.prefitCheckFailed.connect(lambda title, message: refused.append((title, message)))
    analysis.setMinimizerCurrentIndex(_index(analysis._minimizers_logic, 'LMFit_leastsq'))
    analysis.setMinimizerTolerance(0.5)
    assert refused == []

    analysis.setMinimizerCurrentIndex(_index(analysis._minimizers_logic, 'DFO_leastsq'))

    # Allowed (the selection shows DFO-LS), and reported straight away
    assert analysis.minimizerCurrentIndex == _index(analysis._minimizers_logic, 'DFO_leastsq')
    assert len(refused) == 1
    assert refused[0][0] == 'Invalid Minimizer Setting'
    assert 'DFO_leastsq' in refused[0][1] and '0.1 or smaller' in refused[0][1]

    # Once corrected, further switches are quiet
    analysis.setMinimizerTolerance(0.01)
    analysis.setMinimizerCurrentIndex(_index(analysis._minimizers_logic, 'Bumps_simplex'))
    assert len(refused) == 1
