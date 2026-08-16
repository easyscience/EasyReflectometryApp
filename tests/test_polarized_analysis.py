"""Phase 4: magnetism editing, magnetic parameters, polarized fitting and analysis charts.

These run against the real library rather than stubs: the point is that the
calculator ends up in the right state and that each spin channel really gets its
own cross-section, which a stub cannot demonstrate.
"""

import numpy as np
import pytest
from easyreflectometry import Project as RealProject
from easyreflectometry.sample import LayerMagnetism

from EasyReflectometryApp.Backends.Py.logic.fitting import Fitting as FittingLogic
from EasyReflectometryApp.Backends.Py.logic.layers import Layers as LayersLogic
from EasyReflectometryApp.Backends.Py.logic.parameters import Parameters as ParametersLogic
from EasyReflectometryApp.Backends.Py.plotting_1d import Plotting1d


def _project(calculator='refl1d'):
    project = RealProject()
    project.calculator = calculator
    project.default_model()
    project.current_model_index = 0
    # Assembly 1 is the only one with an editable (non superphase/subphase) layer.
    project.current_assembly_index = 1
    return project


def _magnetic_project(rho_m=5.0, theta_m=40.0):
    project = _project()
    layer = project.models[0].sample[1].layers[0]
    layer.magnetism = LayerMagnetism(rho_m=rho_m, theta_m=theta_m)
    project._sync_parameter_states()
    return project


def _write_channels(tmp_path, model_project=None, names=('run_uu.dat', 'run_dd.dat')):
    """Write one plain-text file per channel, detectable by its filename token."""
    q = np.linspace(0.01, 0.2, 20)
    reflectivity = np.exp(-q * 30)
    paths = []
    for name in names:
        path = tmp_path / name
        np.savetxt(path, np.column_stack([q, reflectivity, 0.01 * reflectivity]))
        paths.append(str(path))
    return paths


class TestLayerMagnetismEditing:
    def test_rows_describe_every_layer_of_the_assembly(self):
        logic = LayersLogic(_project())

        rows = logic.magnetism

        assert len(rows) == len(logic.layers)
        assert rows[0]['magnetic'] == 'False'
        # A non-magnetic layer previews what attaching magnetism would create.
        assert float(rows[0]['rho_m']) == 0.0
        assert float(rows[0]['theta_m']) == 270.0

    def test_toggle_on_attaches_magnetism_and_enables_the_calculator(self):
        project = _project()
        logic = LayersLogic(project)

        assert logic.set_magnetic_at_index(0, True) is True

        assert logic.magnetism[0]['magnetic'] == 'True'
        assert project.models[0].has_magnetism is True
        assert project._calculator().include_magnetism is True

    def test_toggle_off_removes_magnetism_and_disables_the_calculator(self):
        project = _project()
        logic = LayersLogic(project)
        logic.set_magnetic_at_index(0, True)

        assert logic.set_magnetic_at_index(0, False) is True

        assert logic.magnetism[0]['magnetic'] == 'False'
        assert project.models[0].has_magnetism is False
        assert project._calculator().include_magnetism is False

    def test_toggling_to_the_current_state_is_a_no_op(self):
        logic = LayersLogic(_project())

        assert logic.set_magnetic_at_index(0, False) is False
        logic.set_magnetic_at_index(0, True)
        assert logic.set_magnetic_at_index(0, True) is False

    def test_attached_magnetism_gets_the_project_default_limits(self):
        project = _project()
        logic = LayersLogic(project)

        logic.set_magnetic_at_index(0, True)

        # `set_magnetic_at_index` runs the project's parameter-state sync, so a
        # freshly attached rho_m is bounded like every other SLD.
        rho_m = logic.magnetism_at_index(0).rho_m
        assert rho_m.min == -1.0
        assert rho_m.max == 10.0

    def test_values_are_written_to_the_parameters(self):
        logic = LayersLogic(_project())
        logic.set_magnetic_at_index(0, True)

        assert logic.set_rho_m_at_index(0, 4.5) is True
        assert logic.set_theta_m_at_index(0, 35.0) is True

        magnetism = logic.magnetism_at_index(0)
        assert magnetism.rho_m.value == 4.5
        assert magnetism.theta_m.value == 35.0
        assert float(logic.magnetism[0]['rho_m']) == 4.5

    def test_values_on_a_non_magnetic_layer_are_ignored(self):
        logic = LayersLogic(_project())

        assert logic.set_rho_m_at_index(0, 4.5) is False
        assert logic.set_theta_m_at_index(0, 35.0) is False
        assert logic.magnetism_at_index(0) is None

    def test_unchanged_and_invalid_values_report_no_change(self):
        logic = LayersLogic(_project())
        logic.set_magnetic_at_index(0, True)
        logic.set_rho_m_at_index(0, 4.5)

        assert logic.set_rho_m_at_index(0, 4.5) is False
        assert logic.set_rho_m_at_index(0, 'not-a-number') is False

    def test_out_of_range_index_is_ignored(self):
        logic = LayersLogic(_project())

        assert logic.set_magnetic_at_index(99, True) is False
        assert logic.set_rho_m_at_index(99, 1.0) is False
        assert logic.magnetism_at_index(99) is None

    def test_calculator_without_magnetism_refuses_and_says_why(self):
        project = _project(calculator='refnx')
        logic = LayersLogic(project)

        assert logic.magnetism_supported is False
        with pytest.raises(NotImplementedError, match='refnx'):
            logic.set_magnetic_at_index(0, True)
        # The refusal must leave the layer untouched, not half-magnetic.
        assert logic.magnetism_at_index(0) is None

    def test_unbound_sample_still_reaches_the_calculator(self):
        """A sample assigned wholesale has no interface on its layers.

        `Layer.magnetism` can then not switch magnetism on by itself, which
        would leave every spin channel uncalculable.
        """
        from easyreflectometry.sample import Layer
        from easyreflectometry.sample import Material
        from easyreflectometry.sample import Multilayer
        from easyreflectometry.sample import Sample

        project = _project()
        project.models[0].sample = Sample(
            Multilayer(Layer(material=Material(sld=0.0, isld=0.0, name='Vac'), thickness=0, roughness=0)),
            Multilayer(Layer(material=Material(sld=8.0, isld=0.0, name='Fe'), thickness=200, roughness=5)),
            Multilayer(Layer(material=Material(sld=2.07, isld=0.0, name='Sub'), thickness=0, roughness=3)),
        )
        logic = LayersLogic(project)

        logic.set_magnetic_at_index(0, True)

        assert project._calculator().include_magnetism is True
        # The magnetic parameter is live on the backend, not just on the model.
        q = np.linspace(0.01, 0.2, 10)
        logic.set_rho_m_at_index(0, 5.0)
        first = project.model_data_for_model_at_index(0, q, channel='pp').y.copy()
        logic.set_rho_m_at_index(0, 1.0)
        assert not np.allclose(first, project.model_data_for_model_at_index(0, q, channel='pp').y)


class TestMagneticParametersInTheTable:
    def test_named_and_grouped_like_the_other_layer_parameters(self):
        logic = ParametersLogic(_magnetic_project())

        rows = {row['name']: row for row in logic.all_parameters()}

        # Not 'EasyLayerMagnetism rho_m': the assembly names it, and the model
        # prefix distinguishes the same layer in different models.
        assert 'Model D2O rho_m' in rows
        assert 'Model D2O theta_m' in rows
        assert rows['Model D2O rho_m']['group'] == 'D2O'
        assert rows['Model D2O rho_m']['value'] == 5.0
        assert rows['Model D2O theta_m']['value'] == 40.0

    def test_magnetic_parameters_are_fittable_and_enabled(self):
        logic = ParametersLogic(_magnetic_project())

        rows = {row['name']: row for row in logic.all_parameters()}

        assert rows['Model D2O rho_m']['enabled'] is True
        assert rows['Model D2O rho_m']['min'] == -1.0
        assert rows['Model D2O rho_m']['max'] == 10.0
        assert rows['Model D2O theta_m']['min'] == 0.0
        assert rows['Model D2O theta_m']['max'] == 360.0

    def test_magnetic_filter_keyword_selects_them(self):
        logic = ParametersLogic(_magnetic_project())

        logic.set_name_filter_criteria('magnetic')

        assert sorted(row['name'] for row in logic.parameters) == ['Model D2O rho_m', 'Model D2O theta_m']

    def test_they_are_not_mistaken_for_experiment_parameters(self):
        logic = ParametersLogic(_magnetic_project())

        logic.set_name_filter_criteria('model')

        assert 'Model D2O rho_m' in [row['name'] for row in logic.parameters]


class TestPolarizedFitting:
    def _polarized_project(self, tmp_path):
        project = _project()
        paths = _write_channels(tmp_path)
        project.load_polarized_experiment({'pp': paths[0], 'mm': paths[1]})
        LayersLogic(project).set_magnetic_at_index(0, True)
        return project

    def test_channels_become_separate_fit_datasets(self, tmp_path):
        project = self._polarized_project(tmp_path)
        logic = FittingLogic(project)

        fitter, x_data, y_data, weights, method = logic.prepare_threaded_fit(_StubMinimizers())

        assert logic.fit_error_message == ''
        # One dataset per measured channel, not one per experiment.
        assert len(x_data) == 2
        assert len(y_data) == 2
        assert len(weights) == 2
        assert method is None

    def test_mixed_polarized_and_ordinary_experiments(self, tmp_path):
        project = self._polarized_project(tmp_path)
        plain = _write_channels(tmp_path, names=('plain.dat',))[0]
        project.load_new_experiment(plain)
        logic = FittingLogic(project)

        _fitter, x_data, _y, _w, _m = logic.prepare_threaded_fit(_StubMinimizers())

        # Two channels of the polarized experiment plus the ordinary one.
        assert len(x_data) == 3

    def test_simultaneous_channel_fit_recovers_the_magnetic_sld(self):
        """The whole chain: magnetism from the Sample page, fit from the Analysis page."""
        from easyreflectometry.data import DataSet1D
        from easyreflectometry.data import PolarizedDataSet

        project = _project()
        model = project.models[0]
        layer = model.sample[1].layers[0]
        layer.material.sld.value = 8.024
        layer.thickness.value = 200.0
        layer.roughness.value = 0.0
        model.sample[0].layers[0].material.sld.value = 0.0
        model.sample[2].layers[0].roughness.value = 0.0
        model.background.value = 0.0

        layers_logic = LayersLogic(project)
        layers_logic.set_magnetic_at_index(0, True)
        magnetism = layers_logic.magnetism_at_index(0)

        # Synthesise the truth with rho_m = 5, then start the fit away from it.
        layers_logic.set_rho_m_at_index(0, 5.0)
        q = np.linspace(0.01, 0.25, 60)
        truth = {
            channel: project.model_data_for_model_at_index(0, q, channel=channel).y.copy()
            for channel in ('pp', 'mm')
        }
        layers_logic.set_rho_m_at_index(0, 2.0)
        magnetism.rho_m.fixed = False
        magnetism.rho_m.bounds = (0.0, 8.0)

        project._experiments = {
            0: PolarizedDataSet(
                name='synthetic',
                channels={
                    channel: DataSet1D(name=channel, x=q, y=values, ye=(0.01 * values) ** 2)
                    for channel, values in truth.items()
                },
                model=model,
            )
        }

        logic = FittingLogic(project)
        fitter, x_data, y_data, weights, _method = logic.prepare_threaded_fit(_StubMinimizers())
        results = fitter.fit(x_data, y_data, weights=weights)

        assert all(result.success for result in results)
        assert magnetism.rho_m.value == pytest.approx(5.0, abs=0.05)

    def test_synchronous_start_stop_fits_every_channel(self, tmp_path):
        """The single-experiment path routes polarized data to `fit_polarized`."""
        project = self._polarized_project(tmp_path)
        logic = FittingLogic(project)

        logic.start_stop()

        assert logic.fit_error_message == ''
        # One FitResults per measured channel, not one for the experiment.
        assert len(logic.last_fit_results) == 2
        assert logic.fit_finished is True

    def test_bayesian_sampling_still_refuses_polarized_data(self, tmp_path):
        """Out of scope for now — but the message must say so, not fail obscurely."""
        project = self._polarized_project(tmp_path)
        logic = FittingLogic(project)

        with pytest.raises(ValueError, match='Bayesian sampling'):
            logic.collect_all_experiments_datagroup()


class TestAnalysisChartChannels:
    def _project_with_channels(self, tmp_path, magnetic=True):
        project = _project()
        paths = _write_channels(tmp_path, names=('run_uu.dat', 'run_dd.dat', 'run_ud.dat'))
        project.load_polarized_experiment({'pp': paths[0], 'mm': paths[1], 'pm': paths[2]})
        if magnetic:
            layers_logic = LayersLogic(project)
            layers_logic.set_magnetic_at_index(0, True)
            layers_logic.set_rho_m_at_index(0, 5.0)
            layers_logic.set_theta_m_at_index(0, 40.0)
        return project

    def test_each_channel_gets_its_own_calculated_curve(self, qcore_application, tmp_path):
        plotting = Plotting1d(project_lib=self._project_with_channels(tmp_path), parent=None)

        pp_points = plotting.getAnalysisDataPoints(0, 'pp')
        mm_points = plotting.getAnalysisDataPoints(0, 'mm')

        assert pp_points and mm_points
        assert all(point['hasCalculated'] for point in pp_points)
        # pp sees rho + rhoM and mm sees rho - rhoM: the curves must differ.
        assert [point['calculated'] for point in pp_points] != [point['calculated'] for point in mm_points]

    def test_channel_without_a_cross_section_is_flagged(self, qcore_application, tmp_path):
        """A spin-flip channel of a non-magnetic model has no curve to draw."""
        plotting = Plotting1d(project_lib=self._project_with_channels(tmp_path, magnetic=False), parent=None)

        points = plotting.getAnalysisDataPoints(0, 'pm')

        assert points, 'measured points must still be reported'
        assert all(point['hasCalculated'] is False for point in points)
        # ... and a residual of zero would look like a perfect fit, so: nothing.
        assert plotting.getResidualDataPoints(0, 'pm') == []

    def test_without_a_channel_the_old_behaviour_is_kept(self, qcore_application, tmp_path):
        plotting = Plotting1d(project_lib=self._project_with_channels(tmp_path), parent=None)

        flat = plotting.getAnalysisDataPoints(0)

        # Falls back to the first visible channel, as before Phase 4.
        assert flat == plotting.getAnalysisDataPoints(0, 'pp')

    def test_analysis_switches_to_channel_series_for_a_polarized_experiment(self, qcore_application, tmp_path):
        project = self._project_with_channels(tmp_path)
        plotting = Plotting1d(project_lib=project, parent=None)
        plotting._proxy = type('P', (), {'_analysis': type('A', (), {'_selected_experiment_indices': [0]})()})()

        assert plotting.analysisUsesChannelSeries is True

    def test_ordinary_experiment_keeps_the_single_series_path(self, qcore_application, tmp_path):
        project = _project()
        project.load_new_experiment(_write_channels(tmp_path, names=('plain.dat',))[0])
        plotting = Plotting1d(project_lib=project, parent=None)
        plotting._proxy = type('P', (), {'_analysis': type('A', (), {'_selected_experiment_indices': [0]})()})()

        assert plotting.analysisUsesChannelSeries is False


class TestSampleBackendSlots:
    def test_slots_emit_and_report_failure(self, qcore_application):
        from EasyReflectometryApp.Backends.Py.sample import Sample

        backend = Sample(project_lib=_project())
        changed = []
        backend.magnetismChanged.connect(lambda: changed.append(True))

        backend.setLayerMagneticAtIndex(0, True)
        backend.setLayerRhoMAtIndex(0, 3.0)
        backend.setLayerThetaMAtIndex(0, 45.0)

        assert backend.magnetismSupported is True
        assert backend.layersMagnetism[0]['magnetic'] == 'True'
        assert float(backend.layersMagnetism[0]['rho_m']) == 3.0
        assert len(changed) == 3

    def test_unsupported_calculator_offers_the_engine_that_can(self, qcore_application):
        """The Analysis page may not even be reachable yet: ask, do not point at it."""
        from EasyReflectometryApp.Backends.Py.sample import Sample

        backend = Sample(project_lib=_project(calculator='refnx'))
        failures = []
        requests = []
        backend.magnetismFailed.connect(failures.append)
        backend.magnetismNeedsEngine.connect(lambda index, engine: requests.append((index, engine)))

        backend.setLayerMagneticAtIndex(0, True)

        # Nothing has changed yet — the UI confirms first.
        assert backend.magnetismSupported is False
        assert requests == [(0, 'refl1d')]
        assert failures == []
        assert backend.layersMagnetism[0]['magnetic'] == 'False'

    def test_confirmed_switch_changes_the_engine_and_attaches_magnetism(self, qcore_application):
        from EasyReflectometryApp.Backends.Py.sample import Sample

        backend = Sample(project_lib=_project(calculator='refnx'))
        engine_changes = []
        backend.calculationEngineChanged.connect(lambda: engine_changes.append(True))

        backend.enableMagnetismWithEngineAtIndex(0, 'refl1d')

        assert backend.magnetismSupported is True
        assert backend.calculationEngines[backend.calculationEngineIndex] == 'refl1d'
        assert backend.layersMagnetism[0]['magnetic'] == 'True'
        assert engine_changes == [True]

    def test_engine_that_cannot_carry_the_magnetism_is_refused(self, qcore_application):
        """Binding a magnetic layer to refnx raises deep in the library."""
        from EasyReflectometryApp.Backends.Py.sample import Sample

        backend = Sample(project_lib=_project(calculator='refl1d'))
        backend.setLayerMagneticAtIndex(0, True)
        failures = []
        backend.magnetismFailed.connect(failures.append)

        backend.setCalculationEngineIndex(backend.calculationEngines.index('refnx'))

        assert len(failures) == 1 and 'refnx' in failures[0]
        assert backend.calculationEngines[backend.calculationEngineIndex] == 'refl1d'
        assert backend.layersMagnetism[0]['magnetic'] == 'True'


class _StubMinimizers:
    tolerance = None
    max_iterations = None

    @staticmethod
    def selected_minimizer_enum():
        return None
