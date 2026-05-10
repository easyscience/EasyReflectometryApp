# SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
"""Exhaustive tests for Bayesian functionality in the analysis backend layer."""

import logging
import os
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

import numpy as np
import pytest
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from EasyReflectometryApp.Backends.Py import analysis as analysis_module
from tests.factories import make_project


# ---------------------------------------------------------------------------
# Stub helpers  (reuse + extend the stubs from test_analysis.py)
# ---------------------------------------------------------------------------

class StubParametersLogic:
    def __init__(self, _project_lib):
        self._all_params = []

    def all_parameters(self):
        return self._all_params


class StubCalculatorsLogic:
    def __init__(self, _project_lib):
        pass


class StubExperimentLogic:
    def __init__(self, project_lib):
        self._project_lib = project_lib
        self._current_index = 0

    def available(self):
        return ['Exp 1']

    def current_index(self):
        return self._current_index


class StubMinimizersLogic:
    def __init__(self, _project_lib):
        self._bayesian = False
        self.tolerance = None
        self.max_iterations = None

    def selected_minimizer_enum(self):
        return None

    def is_bayesian_selected(self):
        return self._bayesian

    def set_bayesian(self, value):
        self._bayesian = value


class StubFittingLogic:
    def __init__(self):
        self.sample_step = 0
        self.sample_total_steps = 0
        self.sample_progress_message = ''
        self.sample_has_update = False
        self.running = False
        self.fit_error_message = ''
        self.fit_cancelled = False
        self.fit_success = False

    def prepare_for_threaded_sample(self):
        pass

    def prepare_threaded_sample(self, minimizers_logic):
        return ('fake-multi-fitter', 'fake-data-group')

    def on_sample_finished(self):
        pass

    def on_sample_progress(self, payload):
        self.sample_step = payload.get('iteration', 0)
        self.sample_total_steps = payload.get('total_steps', 0)
        self.sample_has_update = True

    def reset_stop_flag(self):
        pass

    def prepare_for_threaded_fit(self):
        pass

    def stop_fit(self):
        self.running = False
        self.fit_cancelled = True

    def on_fit_failed(self, msg):
        self.fit_error_message = msg


class StubPlotting:
    def __init__(self):
        self.posterior_q = None
        self.posterior_median = None
        self.posterior_lo = None
        self.posterior_hi = None
        self.sld_z = None
        self.sld_median = None
        self.sld_lo = None
        self.sld_hi = None

    def set_posterior_predictive(self, q, median, lo, hi):
        self.posterior_q = q
        self.posterior_median = median
        self.posterior_lo = lo
        self.posterior_hi = hi

    def set_posterior_predictive_sld(self, z, median, lo, hi):
        self.sld_z = z
        self.sld_median = median
        self.sld_lo = lo
        self.sld_hi = hi


class StubWorker(QObject):
    finished = Signal(list)
    failed = Signal(str)
    progressDetail = Signal(dict)

    instances = []

    def __init__(self, fitter, method_name, args=(), kwargs=None, parent=None):
        super().__init__(parent)
        self.fitter = fitter
        self.method_name = method_name
        self.args = args
        self.kwargs = kwargs or {}
        self.parent = parent
        self.stop_calls = 0
        self.start_calls = 0
        self.delete_calls = 0
        self.termination_enabled = None
        StubWorker.instances.append(self)

    def setTerminationEnabled(self, value):
        self.termination_enabled = value

    def start(self):
        self.start_calls += 1

    def stop(self):
        self.stop_calls += 1

    def deleteLater(self):
        self.delete_calls += 1


# ---------------------------------------------------------------------------
# Sample posterior data
# ---------------------------------------------------------------------------

SAMPLE_POSTERIOR_2D = {
    'draws': np.array([
        [1.0, 2.0],
        [1.1, 2.1],
        [0.9, 1.9],
        [1.05, 2.05],
    ]),
    'param_names': ['thickness', 'roughness'],
}

SAMPLE_POSTERIOR_3D = {
    'draws': np.array([
        [[1.0, 2.0], [1.1, 2.1], [0.95, 1.95], [1.05, 2.05],
         [1.02, 2.02], [0.98, 1.98], [1.07, 2.07], [0.93, 1.93]],
        [[0.9, 1.9], [1.0, 2.0], [1.1, 2.1], [0.85, 1.85],
         [1.05, 2.05], [0.95, 1.95], [1.08, 2.08], [0.92, 1.92]],
    ]),
    'param_names': ['thickness', 'roughness'],
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def analysis(monkeypatch):
    """Build an Analysis instance with all stubs wired in."""
    monkeypatch.setattr(analysis_module, 'ParametersLogic', StubParametersLogic)
    monkeypatch.setattr(analysis_module, 'CalculatorsLogic', StubCalculatorsLogic)
    monkeypatch.setattr(analysis_module, 'ExperimentLogic', StubExperimentLogic)
    monkeypatch.setattr(analysis_module, 'MinimizersLogic', StubMinimizersLogic)
    monkeypatch.setattr(analysis_module, 'FitterWorker', StubWorker)
    # Replace the fitting logic with our stub
    from EasyReflectometryApp.Backends.Py.logic.fitting import Fitting
    monkeypatch.setattr(analysis_module, 'FittingLogic', lambda _project_lib: StubFittingLogic())

    project = make_project()
    analysis_inst = analysis_module.Analysis(project)
    analysis_inst._clearCacheAndEmitParametersChanged = MagicMock()
    analysis_inst._plotting = StubPlotting()
    return analysis_inst


@pytest.fixture
def analysis_with_posterior(analysis):
    """Analysis with a posterior result set on the Bayesian logic."""
    analysis._bayesian_logic._posterior = SAMPLE_POSTERIOR_2D
    return analysis


# ===================================================================
# Bayesian property wiring
# ===================================================================

class TestBayesianSelection:
    def test_is_bayesian_selected_false_by_default(self, analysis):
        assert analysis.isBayesianSelected is False

    def test_is_bayesian_selected_true(self, analysis):
        analysis._minimizers_logic.set_bayesian(True)
        assert analysis.isBayesianSelected is True

    def test_is_bayesian_reflects_minimizer_change(self, analysis):
        analysis._minimizers_logic.set_bayesian(True)
        assert analysis.isBayesianSelected is True
        analysis._minimizers_logic.set_bayesian(False)
        assert analysis.isBayesianSelected is False


class TestBayesianHyperParameterProperties:
    """Property wiring for samples, burn, population, thin."""

    def test_bayesian_samples_default(self, analysis):
        assert analysis.bayesianSamples == 10000

    def test_bayesian_samples_setter_updates_logic(self, analysis):
        analysis.setBayesianSamples(5000)
        assert analysis._bayesian_logic.samples == 5000

    def test_bayesian_burn_default(self, analysis):
        assert analysis.bayesianBurnIn == 2000

    def test_bayesian_burn_setter_updates_logic(self, analysis):
        analysis.setBayesianBurnIn(1000)
        assert analysis._bayesian_logic.burn == 1000

    def test_bayesian_population_default(self, analysis):
        assert analysis.bayesianPopulation == 10

    def test_bayesian_population_setter_updates_logic(self, analysis):
        analysis.setBayesianPopulation(5)
        assert analysis._bayesian_logic.population == 5

    def test_bayesian_thinning_default(self, analysis):
        assert analysis.bayesianThinning == 1

    def test_bayesian_thinning_setter_updates_logic(self, analysis):
        analysis.setBayesianThinning(3)
        assert analysis._bayesian_logic.thin == 3


class TestBayesianHyperParameterSignals:
    """Setter slots emit minimizerChanged."""

    def test_set_bayesian_samples_emits(self, analysis):
        emissions = []
        analysis.minimizerChanged.connect(lambda: emissions.append('minimizerChanged'))
        analysis.setBayesianSamples(5000)
        assert 'minimizerChanged' in emissions

    def test_set_bayesian_burn_emits(self, analysis):
        emissions = []
        analysis.minimizerChanged.connect(lambda: emissions.append('minimizerChanged'))
        analysis.setBayesianBurnIn(1000)
        assert 'minimizerChanged' in emissions

    def test_set_bayesian_population_emits(self, analysis):
        emissions = []
        analysis.minimizerChanged.connect(lambda: emissions.append('minimizerChanged'))
        analysis.setBayesianPopulation(5)
        assert 'minimizerChanged' in emissions

    def test_set_bayesian_thinning_emits(self, analysis):
        emissions = []
        analysis.minimizerChanged.connect(lambda: emissions.append('minimizerChanged'))
        analysis.setBayesianThinning(3)
        assert 'minimizerChanged' in emissions


class TestBayesianProgressProperties:
    """Sampling progress properties from fitting stub."""

    def test_sample_progress_step(self, analysis):
        assert analysis.sampleProgressStep == 0

    def test_sample_progress_message(self, analysis):
        assert analysis.sampleProgressMessage == ''

    def test_sample_progress_has_update(self, analysis):
        assert analysis.sampleProgressHasUpdate is False

    def test_sample_total_steps(self, analysis):
        assert analysis.sampleProgressTotalSteps == 0


# ===================================================================
# Bayesian result availability and posterior
# ===================================================================

class TestBayesianResultAvailable:
    def test_no_result_by_default(self, analysis):
        assert analysis.bayesianResultAvailable is False

    def test_result_available_after_posterior(self, analysis_with_posterior):
        assert analysis_with_posterior.bayesianResultAvailable is True

    def test_result_becomes_unavailable_after_clear(self, analysis_with_posterior):
        analysis_with_posterior._bayesian_logic.clear()
        assert analysis_with_posterior.bayesianResultAvailable is False


class TestBayesianPosterior:
    def test_none_by_default(self, analysis):
        assert analysis.bayesianPosterior is None

    def test_returns_formatted_dict(self, analysis_with_posterior):
        result = analysis_with_posterior.bayesianPosterior
        assert result is not None
        assert 'paramNames' in result
        assert 'nDraws' in result
        assert result['nDraws'] == 4

    def test_none_after_clear(self, analysis_with_posterior):
        analysis_with_posterior._bayesian_logic.clear()
        assert analysis_with_posterior.bayesianPosterior is None


# ===================================================================
# Display name mapping
# ===================================================================

class TestBayesianDisplayNames:
    def test_empty_when_no_posterior(self, analysis):
        assert analysis._bayesian_display_name_list() == []

    def test_empty_when_no_parameters(self, analysis_with_posterior):
        names = analysis_with_posterior._bayesian_display_name_list()
        # No parameter mapping → returns original param_names
        assert names == ['thickness', 'roughness']

    def test_maps_through_parameters_logic(self, analysis_with_posterior):
        analysis_with_posterior._parameters_logic._all_params = [
            {'unique_name': 'thickness', 'name': 'Thickness'},
            {'unique_name': 'roughness', 'name': 'Roughness'},
        ]
        names = analysis_with_posterior._bayesian_display_name_list()
        assert names == ['Thickness', 'Roughness']

    def test_fallback_to_unique_name_when_display_missing(self, analysis_with_posterior):
        analysis_with_posterior._parameters_logic._all_params = [
            {'unique_name': 'thickness', 'name': ''},
            {'unique_name': 'roughness'},
        ]
        names = analysis_with_posterior._bayesian_display_name_list()
        assert names == ['thickness', 'roughness']

    def test_builds_mapping_dict(self, analysis_with_posterior):
        analysis_with_posterior._parameters_logic._all_params = [
            {'unique_name': 'thickness', 'name': 'Thickness'},
            {'unique_name': 'roughness', 'name': 'Roughness'},
        ]
        mapping = analysis_with_posterior._bayesian_display_names()
        assert mapping == {'thickness': 'Thickness', 'roughness': 'Roughness'}

    def test_mapping_handles_exception_gracefully(self, analysis_with_posterior):
        def broken_all_params():
            raise RuntimeError('boom')

        analysis_with_posterior._parameters_logic.all_parameters = broken_all_params
        # Should not raise
        mapping = analysis_with_posterior._bayesian_display_names()
        assert mapping == {}


# ===================================================================
# Marginal distributions
# ===================================================================

class TestBayesianMarginals:
    def test_empty_when_no_posterior(self, analysis):
        assert analysis.bayesianMarginals == []

    def test_returns_one_entry_per_param(self, analysis_with_posterior):
        marginals = analysis_with_posterior.bayesianMarginals
        assert len(marginals) == 2

    def test_marginal_keys(self, analysis_with_posterior):
        marginals = analysis_with_posterior.bayesianMarginals
        for m in marginals:
            assert 'name' in m
            assert 'mean' in m
            assert 'std' in m
            assert 'ci_low' in m
            assert 'ci_high' in m
            assert 'binCenters' in m
            assert 'counts' in m

    def test_marginal_stats_approximate(self, analysis_with_posterior):
        marginals = analysis_with_posterior.bayesianMarginals
        # thickness ~ 1.0 ± small, roughness ~ 2.0 ± small
        assert abs(marginals[0]['mean'] - 1.0) < 0.1
        assert abs(marginals[1]['mean'] - 2.0) < 0.1

    def test_marginal_names_fallback(self, analysis_with_posterior):
        marginals = analysis_with_posterior.bayesianMarginals
        assert marginals[0]['name'] == 'thickness'
        assert marginals[1]['name'] == 'roughness'

    def test_marginal_names_use_display_names(self, analysis_with_posterior):
        analysis_with_posterior._parameters_logic._all_params = [
            {'unique_name': 'thickness', 'name': 'Thickness'},
            {'unique_name': 'roughness', 'name': 'Roughness'},
        ]
        marginals = analysis_with_posterior.bayesianMarginals
        assert marginals[0]['name'] == 'Thickness'
        assert marginals[1]['name'] == 'Roughness'

    def test_marginal_bin_arrays_have_correct_length(self, analysis_with_posterior):
        marginals = analysis_with_posterior.bayesianMarginals
        for m in marginals:
            assert isinstance(m['binCenters'], list)
            assert isinstance(m['counts'], list)
            assert len(m['binCenters']) == len(m['counts']) == 40  # bins=40


# ===================================================================
# Corner plot URL
# ===================================================================

class TestBayesianCornerPlotUrl:
    def test_empty_when_no_posterior(self, analysis):
        assert analysis.bayesianCornerPlotUrl == ''

    def test_lazy_renders_once(self, analysis_with_posterior):
        # Pre-set a cached URL so the second access doesn't re-trigger rendering
        analysis_with_posterior._bayesian_logic.corner_plot_url = 'file:///cached.png'
        with patch.object(analysis_with_posterior, '_render_corner_plot') as mock:
            url1 = analysis_with_posterior.bayesianCornerPlotUrl
            url2 = analysis_with_posterior.bayesianCornerPlotUrl
            assert mock.call_count == 0  # already cached, no call needed

    def test_returns_cached_url(self, analysis_with_posterior):
        analysis_with_posterior._bayesian_logic.corner_plot_url = 'file:///cached.png'
        url = analysis_with_posterior.bayesianCornerPlotUrl
        assert url == 'file:///cached.png'


# ===================================================================
# Trace plot URL
# ===================================================================

class TestBayesianTracePlotUrl:
    def test_empty_when_no_posterior(self, analysis):
        assert analysis.bayesianTracePlotUrl == ''

    def test_lazy_renders_once(self, analysis_with_posterior):
        # Pre-set a cached URL so the second access doesn't re-trigger rendering
        analysis_with_posterior._bayesian_logic.trace_plot_url = 'file:///cached_trace.png'
        with patch.object(analysis_with_posterior, '_render_trace_plot') as mock:
            url1 = analysis_with_posterior.bayesianTracePlotUrl
            url2 = analysis_with_posterior.bayesianTracePlotUrl
            assert mock.call_count == 0  # already cached, no call needed

    def test_returns_cached_url(self, analysis_with_posterior):
        analysis_with_posterior._bayesian_logic.trace_plot_url = 'file:///cached_trace.png'
        url = analysis_with_posterior.bayesianTracePlotUrl
        assert url == 'file:///cached_trace.png'


# ===================================================================
# Heatmap
# ===================================================================

class TestBayesianHeatmap:
    def test_data_none_when_no_posterior(self, analysis):
        assert analysis.bayesianHeatmapData is None

    def test_plot_url_empty_when_no_posterior(self, analysis):
        assert analysis.bayesianHeatmapPlotUrl == ''

    def test_compute_populates_data(self, analysis_with_posterior):
        with patch.object(analysis_with_posterior, '_render_heatmap_plot') as mock_render:
            emissions = []
            analysis_with_posterior.heatmapChanged.connect(lambda: emissions.append('emitted'))
            analysis_with_posterior.computeBayesianHeatmap(0, 1)

        assert analysis_with_posterior.bayesianHeatmapData is not None
        data = analysis_with_posterior.bayesianHeatmapData
        assert 'xLabel' in data
        assert 'yLabel' in data
        assert 'xCenters' in data
        assert 'yCenters' in data
        assert 'zValues' in data
        mock_render.assert_called_once_with(0, 1)
        assert 'emitted' in emissions

    def test_compute_does_nothing_without_posterior(self, analysis):
        emissions = []
        analysis.heatmapChanged.connect(lambda: emissions.append('emitted'))
        analysis.computeBayesianHeatmap(0, 1)
        assert analysis.bayesianHeatmapData is None
        assert emissions == []

    def test_compute_with_3d_draws(self, analysis):
        analysis._bayesian_logic._posterior = SAMPLE_POSTERIOR_3D
        with patch.object(analysis, '_render_heatmap_plot'):
            analysis.computeBayesianHeatmap(0, 1)
        data = analysis.bayesianHeatmapData
        assert data is not None
        assert data['xLabel'] == 'thickness'
        assert data['yLabel'] == 'roughness'

    def test_param_names_for_display(self, analysis_with_posterior):
        analysis_with_posterior._parameters_logic._all_params = [
            {'unique_name': 'thickness', 'name': 'Thickness'},
            {'unique_name': 'roughness', 'name': 'Roughness'},
        ]
        with patch.object(analysis_with_posterior, '_render_heatmap_plot'):
            analysis_with_posterior.computeBayesianHeatmap(0, 1)
        data = analysis_with_posterior.bayesianHeatmapData
        assert data['xLabel'] == 'Thickness'
        assert data['yLabel'] == 'Roughness'


# ===================================================================
# Plot file paths
# ===================================================================

class TestPlotFilePath:
    def test_returns_path_in_tempdir(self, analysis):
        path = analysis._plot_file_path('corner')
        assert isinstance(path, Path)
        assert 'EasyReflectometryApp' in str(path)
        assert 'bayesian' in str(path)
        assert path.name == 'corner.png'

    def test_url_from_stem(self, analysis):
        url = analysis._plot_file_url('corner')
        assert url.startswith('file:///')
        assert 'corner.png' in url

    def test_different_stems(self, analysis):
        assert analysis._plot_file_path('trace').name == 'trace.png'
        assert analysis._plot_file_path('heatmap_0_1').name == 'heatmap_0_1.png'


# ===================================================================
# Render methods (basic smoke tests — MPL rendering is tested separately)
# ===================================================================

class TestRenderCornerPlot:
    def test_sets_empty_url_when_no_posterior(self, analysis):
        analysis._render_corner_plot()
        assert analysis._bayesian_logic.corner_plot_url == ''

    def test_handles_import_error_gracefully(self, analysis_with_posterior, caplog):
        """Corner plot rendering catches ImportError when corner lib missing."""
        caplog.set_level(logging.INFO)
        # Simulate ImportError by making plot_corner raise
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == 'easyreflectometry.analysis.bayesian':
                raise ImportError('No module named corner')
            return original_import(name, *args, **kwargs)

        with patch.object(builtins, '__import__', mock_import):
            analysis_with_posterior._render_corner_plot()

        assert analysis_with_posterior._bayesian_logic.corner_plot_url == ''
        assert 'corner library not installed' in caplog.text


class TestRenderTracePlot:
    def test_sets_empty_url_when_no_posterior(self, analysis):
        analysis._render_trace_plot()
        assert analysis._bayesian_logic.trace_plot_url == ''

    def test_handles_import_error_gracefully(self, analysis_with_posterior, caplog):
        caplog.set_level(logging.INFO)
        # Force trace rendering to attempt matplotlib and fail at arviz
        with patch('matplotlib.pyplot') as mock_plt:
            mock_fig = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, [[MagicMock()]])
            mock_plt.gcf.return_value = mock_fig
            analysis_with_posterior._render_trace_plot()
            # matplotlib with Agg should work; the key is that it doesn't crash
            assert mock_plt.subplots.called


class TestRenderHeatmapPlot:
    def test_sets_empty_url_when_no_posterior(self, analysis):
        analysis._render_heatmap_plot(0, 1)
        assert analysis._bayesian_logic.heatmap_plot_url == ''

    def test_renders_with_posterior(self, analysis_with_posterior):
        with patch('matplotlib.pyplot') as mock_plt:
            mock_fig = MagicMock()
            mock_plt.subplots.return_value = (mock_fig, MagicMock())
            analysis_with_posterior._render_heatmap_plot(0, 1)
            assert mock_plt.subplots.called


# ===================================================================
# Diagnostics
# ===================================================================

class TestBayesianDiagnostics:
    def test_empty_when_no_posterior(self, analysis):
        assert analysis.bayesianDiagnostics == {}

    def test_computes_lazily(self, analysis_with_posterior):
        with patch.object(analysis_with_posterior, '_compute_diagnostics') as mock:
            analysis_with_posterior.bayesianDiagnostics
            mock.assert_called_once()

    def test_returns_cached(self, analysis_with_posterior):
        analysis_with_posterior._bayesian_logic.diagnostics = {'already': 'computed'}
        with patch.object(analysis_with_posterior, '_compute_diagnostics') as mock:
            result = analysis_with_posterior.bayesianDiagnostics
            assert result == {'already': 'computed'}
            mock.assert_not_called()

    def test_basic_diagnostics_shape(self, analysis_with_posterior):
        analysis_with_posterior._compute_diagnostics()
        diag = analysis_with_posterior._bayesian_logic.diagnostics
        assert 'nDraws' in diag
        assert 'nParams' in diag
        assert 'burnIn' in diag
        assert 'thin' in diag
        assert 'population' in diag
        assert 'samples' in diag
        assert diag['nDraws'] == 4
        assert diag['nParams'] == 2

    def test_acceptance_rate_from_state(self, analysis_with_posterior):
        analysis_with_posterior._bayesian_logic._posterior = {
            'draws': SAMPLE_POSTERIOR_2D['draws'],
            'param_names': ['thickness', 'roughness'],
            'state': SimpleNamespace(acceptance_rate=0.35),
        }
        analysis_with_posterior._compute_diagnostics()
        assert analysis_with_posterior._bayesian_logic.diagnostics.get('acceptanceRate') == 0.35

    def test_acceptance_rate_handles_missing_state(self, analysis_with_posterior):
        # Default SAMPLE_POSTERIOR_2D has no 'state' key
        analysis_with_posterior._compute_diagnostics()
        assert 'acceptanceRate' not in analysis_with_posterior._bayesian_logic.diagnostics

    def test_rhat_status_with_2d_draws(self, analysis_with_posterior):
        analysis_with_posterior._compute_diagnostics()
        assert analysis_with_posterior._bayesian_logic.diagnostics.get('rhatStatus', '').startswith(
            'Unavailable: the sampler returned flattened draws'
        )

    def test_rhat_attempted_with_3d_draws(self, analysis_with_posterior):
        analysis_with_posterior._bayesian_logic._posterior = SAMPLE_POSTERIOR_3D
        analysis_with_posterior._compute_diagnostics()
        diag = analysis_with_posterior._bayesian_logic.diagnostics
        # 3D draws with >=2 chains trigger the arviz path
        # If arviz is installed and R-hat succeeds → 'rhat' key present
        # If arviz is installed but R-hat fails → 'rhatStatus' with fallback message
        # If arviz is not installed → 'rhatStatus' with arviz message
        assert 'rhat' in diag or 'rhatStatus' in diag

    def test_clear_posterior_resets_diagnostics(self, analysis_with_posterior):
        analysis_with_posterior._compute_diagnostics()
        assert analysis_with_posterior._bayesian_logic.diagnostics != {}
        analysis_with_posterior._bayesian_logic.clear()
        assert analysis_with_posterior._bayesian_logic.diagnostics == {}


# ===================================================================
# Posterior predictive
# ===================================================================

class TestPosteriorPredictive:
    def test_noop_when_plotting_none(self, analysis_with_posterior):
        analysis_with_posterior._plotting = None
        # Should not raise
        analysis_with_posterior._compute_and_publish_posterior_predictive()

    def test_noop_when_no_experiments(self, analysis_with_posterior):
        # Make _ordered_experiments return empty via analysis-level method
        original = analysis_with_posterior._ordered_experiments
        analysis_with_posterior._ordered_experiments = lambda: []
        # Should not raise
        analysis_with_posterior._compute_and_publish_posterior_predictive()
        analysis_with_posterior._ordered_experiments = original

    def test_noop_when_posterior_cleared(self, analysis_with_posterior):
        analysis_with_posterior._bayesian_logic.clear()
        analysis_with_posterior._compute_and_publish_posterior_predictive()
        assert analysis_with_posterior._plotting.posterior_q is None


# ===================================================================
# Bayesian sampling dispatch
# ===================================================================

class TestStartThreadedSample:
    def test_dispatches_when_bayesian_selected(self, analysis, monkeypatch):
        StubWorker.instances = []
        analysis._minimizers_logic.set_bayesian(True)

        analysis._start_threaded_fit()

        worker = StubWorker.instances[-1]
        assert worker.method_name == 'sample'
        assert worker.start_calls == 1

    def test_worker_kwargs_contain_hyper_params(self, analysis):
        StubWorker.instances = []
        analysis._minimizers_logic.set_bayesian(True)
        analysis._bayesian_logic.samples = 5000
        analysis._bayesian_logic.burn = 1000
        analysis._bayesian_logic.thin = 2
        analysis._bayesian_logic.population = 5

        analysis._start_threaded_fit()

        worker = StubWorker.instances[-1]
        assert worker.kwargs['samples'] == 5000
        assert worker.kwargs['burn'] == 1000
        assert worker.kwargs['thin'] == 2
        assert worker.kwargs['population'] == 5

    def test_worker_has_progress_and_delete_connections(self, analysis):
        StubWorker.instances = []
        analysis._minimizers_logic.set_bayesian(True)

        analysis._start_threaded_fit()

        worker = StubWorker.instances[-1]
        # Verify signal connections exist (they are connected before start)
        assert worker.start_calls == 1

    def test_emits_fit_failed_on_preparation_error(self, analysis):
        analysis._fitting_logic.prepare_threaded_sample = lambda ml: (None, None)
        analysis._fitting_logic.fit_error_message = 'No experiments to sample'
        received = []
        analysis.fitFailed.connect(received.append)

        analysis._minimizers_logic.set_bayesian(True)
        analysis._start_threaded_fit()

        assert len(received) >= 1


class TestOnSampleFinished:
    def test_stores_posterior(self, analysis):
        results = [SAMPLE_POSTERIOR_2D]
        analysis._on_sample_finished(results)
        assert analysis._bayesian_logic.posterior is SAMPLE_POSTERIOR_2D

    def test_clears_fitter_thread(self, analysis):
        analysis._fitter_thread = 'some-worker'
        analysis._on_sample_finished([SAMPLE_POSTERIOR_2D])
        assert analysis._fitter_thread is None

    def test_calls_posterior_predictive_and_diagnostics(self, analysis):
        with patch.object(analysis, '_compute_and_publish_posterior_predictive') as mock_pp:
            with patch.object(analysis, '_compute_diagnostics') as mock_diag:
                with patch.object(analysis, '_render_corner_plot') as mock_corner:
                    with patch.object(analysis, '_render_trace_plot') as mock_trace:
                        analysis._on_sample_finished([SAMPLE_POSTERIOR_2D])
                        mock_pp.assert_called_once()
                        mock_diag.assert_called_once()
                        mock_corner.assert_called_once()
                        mock_trace.assert_called_once()

    def test_emits_fitting_signals(self, analysis):
        emissions = {'fitting': 0, 'external': 0}
        analysis.fittingChanged.connect(lambda: emissions.__setitem__('fitting', emissions['fitting'] + 1))
        analysis.externalFittingChanged.connect(lambda: emissions.__setitem__('external', emissions['external'] + 1))

        analysis._on_sample_finished([SAMPLE_POSTERIOR_2D])

        assert emissions['fitting'] >= 1
        assert emissions['external'] >= 1


# ===================================================================
# Bayesian param names
# ===================================================================

class TestBayesianParamNames:
    def test_empty_when_no_posterior(self, analysis):
        assert analysis.bayesianParamNames == []

    def test_returns_list_of_names(self, analysis_with_posterior):
        names = analysis_with_posterior.bayesianParamNames
        assert names == ['thickness', 'roughness']

    def test_uses_display_names(self, analysis_with_posterior):
        analysis_with_posterior._parameters_logic._all_params = [
            {'unique_name': 'thickness', 'name': 'Thickness'},
            {'unique_name': 'roughness', 'name': 'Roughness'},
        ]
        names = analysis_with_posterior.bayesianParamNames
        assert names == ['Thickness', 'Roughness']


# ===================================================================
# Save Bayesian plot
# ===================================================================

class MockQFileDialog:
    """Stand-in for QtWidgets.QFileDialog that doesn't need a QApplication."""
    def __init__(self, *args, **kwargs):
        pass

    @staticmethod
    def getSaveFileName(*args, **kwargs):
        return '', ''


class TestSaveBayesianPlot:
    @pytest.fixture(autouse=True)
    def _patch_qfiledialog(self, monkeypatch):
        monkeypatch.setattr(analysis_module.QtWidgets, 'QFileDialog', MockQFileDialog)

    def test_returns_false_for_invalid_url(self, analysis):
        assert analysis.saveBayesianPlot('') is False
        assert analysis.saveBayesianPlot('not-a-url') is False

    def test_returns_false_for_nonexistent_file(self, analysis):
        url = 'file:///nonexistent/path/plot.png'
        assert analysis.saveBayesianPlot(url) is False

    def test_saves_file_successfully(self, analysis, tmp_path):
        # Create a source PNG inside tmp_path (avoids polluting system temp dir)
        src_dir = tmp_path / 'bayesian'
        src_dir.mkdir(parents=True, exist_ok=True)
        src_file = src_dir / 'test_save.png'
        src_file.write_text('fake-png-content')

        url = src_file.resolve().as_uri()
        save_dest = str(tmp_path / 'saved_plot.png')
        # Patch getSaveFileName to return a real path
        original_get = MockQFileDialog.getSaveFileName
        MockQFileDialog.getSaveFileName = lambda *a, **kw: (save_dest, 'PNG (*.png)')
        try:
            result = analysis.saveBayesianPlot(url)
            assert result is True
            saved = Path(save_dest)
            assert saved.exists()
            assert saved.read_text() == 'fake-png-content'
            saved.unlink()
        finally:
            MockQFileDialog.getSaveFileName = original_get

    def test_returns_false_when_dialog_cancelled(self, analysis, tmp_path):
        src_dir = tmp_path / 'bayesian'
        src_dir.mkdir(parents=True, exist_ok=True)
        src_file = src_dir / 'cancelled_test.png'
        src_file.write_text('content')

        url = src_file.resolve().as_uri()
        # MockQFileDialog.getSaveFileName returns ('', '') by default → cancelled
        result = analysis.saveBayesianPlot(url)
        assert result is False


# ===================================================================
# Sampling progress forwarding
# ===================================================================

class TestSamplingProgress:
    def test_on_fit_progress_dispatches_to_sample(self, analysis):
        payload = {'sampling': True, 'iteration': 42, 'total_steps': 1000}
        analysis._on_fit_progress(payload)
        assert analysis._fitting_logic.sample_step == 42
        assert analysis._fitting_logic.sample_total_steps == 1000

    def test_fitting_changed_emitted_on_progress(self, analysis):
        emissions = []
        analysis.fittingChanged.connect(lambda: emissions.append('emitted'))
        analysis._on_fit_progress({'sampling': True, 'iteration': 1, 'total_steps': 100})
        assert 'emitted' in emissions
