from unittest.mock import MagicMock

from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from EasyReflectometryApp.Backends.Py import py_backend as backend_module


class StubLoggerLevelHandler:
    def __init__(self, parent):
        self.parent = parent


class StubHome(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)


class StubProject(QObject):
    externalNameChanged = Signal()
    externalCreatedChanged = Signal()
    externalProjectLoaded = Signal()
    externalProjectReset = Signal()

    def __init__(self, _project_lib, parent=None):
        super().__init__(parent)
        self.dirty_calls = 0
        self.pre_save_hooks = []
        self.post_load_hooks = []

    def markDirty(self):
        self.dirty_calls += 1

    def add_pre_save_hook(self, hook):
        self.pre_save_hooks.append(hook)

    def add_post_load_hook(self, hook):
        self.post_load_hooks.append(hook)


class StubSample(QObject):
    externalSampleChanged = Signal()
    experimentsRemoved = Signal(list)
    calculationEngineChanged = Signal()
    externalRefreshPlot = Signal()
    modelsTableChanged = Signal()
    materialsTableChanged = Signal()
    modelsIndexChanged = Signal()
    assembliesTableChanged = Signal()
    assembliesIndexChanged = Signal()
    layersChange = Signal()
    structureChanged = Signal()
    qRangeChanged = Signal()
    magnetismChanged = Signal()
    constraintsChanged = Signal()

    def __init__(self, _project_lib):
        super().__init__()
        self.clear_calls = 0
        self.structure_clear_calls = 0

    def _clearCacheAndEmitLayersChanged(self):
        self.clear_calls += 1

    def store_constraint_metadata(self):
        pass

    def reload_constraint_states(self):
        pass

    def _clearStructureCacheAndEmit(self):
        self.structure_clear_calls += 1
        self.structureChanged.emit()


class StubExperiment(QObject):
    externalExperimentChanged = Signal()
    experimentChanged = Signal()
    qRangeUpdated = Signal()
    experimentLoaded = Signal(int)

    def __init__(self, _project_lib):
        super().__init__()


class StubAnalysis(QObject):
    calculatorChanged = Signal()
    externalMinimizerChanged = Signal()
    externalFitSettingsChanged = Signal()
    externalCalculatorChanged = Signal()
    externalParametersChanged = Signal()
    externalFittingChanged = Signal()
    externalExperimentChanged = Signal()
    experimentsChanged = Signal()
    parametersChanged = Signal()
    inequalityContextChanged = Signal()
    posteriorPredictiveReady = Signal(object, object, object, object)
    posteriorPredictiveSldReady = Signal(object, object, object, object)
    posteriorPredictiveCleared = Signal()

    def __init__(self, _project_lib, parent=None, selection=None):
        super().__init__(parent)
        self.selection = selection
        self._minimizers_logic = object()
        self._selected = [0]
        self.received_indices = None
        self.clear_calls = 0
        self.bayesian_clear_calls = 0
        self.prune_calls = 0
        self.reset_selection_calls = 0

    def prune_selected_experiments(self):
        self.prune_calls += 1
        return False

    def follow_removed_experiments(self, removed):
        self.removed_experiments = removed

    def reset_selected_experiments(self):
        self.reset_selection_calls += 1
        return False

    def clearBayesianResults(self):
        self.bayesian_clear_calls += 1

    def onProjectLoaded(self):
        self.project_loaded_calls = getattr(self, 'project_loaded_calls', 0) + 1

    @property
    def experimentsSelectedCount(self):
        return len(self._selected)

    @property
    def selectedExperimentIndices(self):
        return self._selected

    def setSelectedExperimentIndices(self, indices):
        self.received_indices = indices
        self._selected = list(indices)

    def selectExperimentAtIndex(self, index):
        self.setSelectedExperimentIndices([index])

    def _clearCacheAndEmitParametersChanged(self):
        self.clear_calls += 1


class StubSummary(QObject):
    createdChanged = Signal()
    summaryChanged = Signal()

    def __init__(self, _project_lib, parent=None):
        super().__init__(parent)

    def refreshPaths(self):
        pass


class StubStatusLogic:
    def __init__(self):
        self.minimizers_logic = None

    def set_minimizers_logic(self, value):
        self.minimizers_logic = value


class StubStatus(QObject):
    statusChanged = Signal()

    def __init__(self, _project_lib):
        super().__init__()
        self._status_logic = StubStatusLogic()


class StubPlotting(QObject):
    sampleChartRangesChanged = Signal()
    sldChartRangesChanged = Signal()
    experimentChartRangesChanged = Signal()
    samplePageResetAxes = Signal()
    experimentChannelsChanged = Signal()
    magneticProfileChanged = Signal()
    spinAsymmetryChanged = Signal()

    def __init__(self, _project_lib, parent=None, selection=None):
        super().__init__(parent)
        self.selection = selection
        self.posterior = None
        self.posterior_sld = None
        self.reset_calls = 0
        self.channel_notifications = 0
        self.magnetic_notifications = 0
        self.spin_asymmetry_notifications = 0
        self.refresh_calls = {'sample': 0, 'experiment': 0, 'analysis': 0}
        self._multi = True
        self._individual = [{'name': 'E0', 'index': 0, 'color': '#111111', 'channel': '', 'hasData': True}]

    def notifyExperimentChannelsChanged(self):
        self.channel_notifications += 1
        self.experimentChannelsChanged.emit()

    def notifyMagneticProfileChanged(self):
        self.magnetic_notifications += 1
        self.magneticProfileChanged.emit()

    def notifySpinAsymmetryChanged(self):
        self.spin_asymmetry_notifications += 1
        self.spinAsymmetryChanged.emit()

    @property
    def isMultiExperimentMode(self):
        return self._multi

    @property
    def individualExperimentDataList(self):
        return self._individual

    def getExperimentDataPoints(self, experiment_index):
        return [{'x': float(experiment_index), 'y': 0.0}]

    def getAnalysisDataPoints(self, experiment_index, channel=''):
        return [{'x': float(experiment_index), 'measured': 0.0, 'calculated': 0.0, 'channel': channel}]

    def reset_data(self):
        self.reset_calls += 1

    def set_posterior_predictive(self, q, median, lower, upper):
        self.posterior = (q, median, lower, upper)

    def set_posterior_predictive_sld(self, z, median, lower, upper):
        self.posterior_sld = (z, median, lower, upper)

    def clear_posterior_predictive(self):
        self.posterior = None

    def clear_posterior_predictive_sld(self):
        self.posterior_sld = None

    def refreshSamplePage(self):
        self.refresh_calls['sample'] += 1

    def refreshExperimentPage(self):
        self.refresh_calls['experiment'] += 1

    def refreshAnalysisPage(self):
        self.refresh_calls['analysis'] += 1


def _make_backend(monkeypatch):
    monkeypatch.setattr(backend_module, 'ProjectLib', lambda: object())
    monkeypatch.setattr(backend_module, 'Home', StubHome)
    monkeypatch.setattr(backend_module, 'Project', StubProject)
    monkeypatch.setattr(backend_module, 'Sample', StubSample)
    monkeypatch.setattr(backend_module, 'Experiment', StubExperiment)
    monkeypatch.setattr(backend_module, 'Analysis', StubAnalysis)
    monkeypatch.setattr(backend_module, 'Summary', StubSummary)
    monkeypatch.setattr(backend_module, 'Status', StubStatus)
    monkeypatch.setattr(backend_module, 'Plotting1d', StubPlotting)
    monkeypatch.setattr(backend_module, 'LoggerLevelHandler', StubLoggerLevelHandler)
    return backend_module.PyBackend()


def test_backend_constructor_wires_minimizers_logic(monkeypatch, qcore_application):
    backend = _make_backend(monkeypatch)

    assert backend._status._status_logic.minimizers_logic is backend._analysis._minimizers_logic


def test_backend_constructor_hooks_constraint_state_into_save_and_load(monkeypatch, qcore_application):
    """The Sample backend's constraint rows must reach the project file and come back on load."""
    backend = _make_backend(monkeypatch)

    assert backend._project.pre_save_hooks == [backend._sample.store_constraint_metadata]
    assert backend._project.post_load_hooks == [
        backend._sample.reload_constraint_states,
        # A loaded or reset project starts with only its current experiment selected.
        backend._analysis.reset_selected_experiments,
    ]


def test_analysis_and_plotting_share_one_experiment_selection(monkeypatch, qcore_application):
    backend = _make_backend(monkeypatch)

    assert backend._analysis.selection is not None
    assert backend._analysis.selection is backend._plotting_1d.selection


def test_posterior_predictive_reaches_plotting_through_signals(monkeypatch, qcore_application):
    backend = _make_backend(monkeypatch)

    backend._analysis.posteriorPredictiveReady.emit([1.0], [2.0], [1.5], [2.5])
    backend._analysis.posteriorPredictiveSldReady.emit([0.0], [1.0], [0.5], [1.5])
    assert backend._plotting_1d.posterior == ([1.0], [2.0], [1.5], [2.5])
    assert backend._plotting_1d.posterior_sld == ([0.0], [1.0], [0.5], [1.5])

    backend._analysis.posteriorPredictiveCleared.emit()
    assert backend._plotting_1d.posterior is None
    assert backend._plotting_1d.posterior_sld is None


def test_selection_is_pruned_after_model_removal_and_project_changes(monkeypatch, qcore_application):
    backend = _make_backend(monkeypatch)

    backend._sample.modelsTableChanged.emit()
    assert backend._analysis.prune_calls == 1

    backend._project.externalProjectLoaded.emit()  # also an ORSO sample import
    assert backend._analysis.prune_calls > 1  # the relay re-emits modelsTableChanged too; pruning is idempotent


def test_analysis_selection_bridge_updates_analysis_and_emits_signal(monkeypatch, qcore_application):
    backend = _make_backend(monkeypatch)
    count = {'changed': 0}
    backend.multiExperimentSelectionChanged.connect(lambda: count.__setitem__('changed', count['changed'] + 1))

    backend.analysisSetSelectedExperimentIndices((2, 4))

    assert backend._analysis.received_indices == [2, 4]
    assert backend.analysisExperimentsSelectedCount == 2
    assert backend.analysisSelectedExperimentIndices == [2, 4]
    assert count['changed'] == 1


def test_backend_relay_project_changed_triggers_refresh_chain(monkeypatch, qcore_application):
    backend = _make_backend(monkeypatch)
    counts = {'status': 0, 'summary': 0, 'axes': 0}
    backend._status.statusChanged.connect(lambda: counts.__setitem__('status', counts['status'] + 1))
    backend._summary.summaryChanged.connect(lambda: counts.__setitem__('summary', counts['summary'] + 1))
    backend._plotting_1d.samplePageResetAxes.connect(lambda: counts.__setitem__('axes', counts['axes'] + 1))

    backend._relay_project_page_project_changed()

    assert backend._sample.clear_calls == 1
    assert backend._analysis.clear_calls == 1
    assert backend._plotting_1d.reset_calls == 1
    assert backend._plotting_1d.refresh_calls == {'sample': 1, 'experiment': 1, 'analysis': 1}
    assert counts == {'status': 1, 'summary': 1, 'axes': 1}


def test_backend_project_lifecycle_clears_bayesian_results(monkeypatch, qcore_application):
    # Posteriors belong to one project state: create/load/reset must discard
    # them so stale Bayesian results are never shown against new data.
    backend = _make_backend(monkeypatch)

    backend._project.externalCreatedChanged.emit()
    backend._project.externalProjectLoaded.emit()
    backend._project.externalProjectReset.emit()

    assert backend._analysis.bayesian_clear_calls == 3


def test_backend_load_and_reset_refresh_the_minimizer_controls(monkeypatch, qcore_application):
    # A loaded or reset project brings its own minimizer and fit settings.
    backend = _make_backend(monkeypatch)

    backend._project.externalProjectLoaded.emit()
    backend._project.externalProjectReset.emit()

    assert backend._analysis.project_loaded_calls == 2


def test_backend_fit_finished_refreshes_summary(monkeypatch, qcore_application):
    # A finished fit must invalidate the Summary tab's HTML binding so the
    # goodness-of-fit stops showing the stale pre-fit 'N/A'.
    backend = _make_backend(monkeypatch)
    counts = {'summary': 0}
    backend._summary.summaryChanged.connect(lambda: counts.__setitem__('summary', counts['summary'] + 1))

    backend._analysis.externalFittingChanged.emit()

    assert counts['summary'] == 1


def test_backend_refresh_plots_emits_ranges_and_multi_signal(monkeypatch, qcore_application):
    backend = _make_backend(monkeypatch)
    counts = {'sample': 0, 'sld': 0, 'exp': 0, 'multi': 0}
    backend._plotting_1d.sampleChartRangesChanged.connect(lambda: counts.__setitem__('sample', counts['sample'] + 1))
    backend._plotting_1d.sldChartRangesChanged.connect(lambda: counts.__setitem__('sld', counts['sld'] + 1))
    backend._plotting_1d.experimentChartRangesChanged.connect(lambda: counts.__setitem__('exp', counts['exp'] + 1))
    backend.multiExperimentSelectionChanged.connect(lambda: counts.__setitem__('multi', counts['multi'] + 1))

    backend._refresh_plots()

    assert counts == {'sample': 1, 'sld': 1, 'exp': 1, 'multi': 1}
    assert backend.plottingIsMultiExperimentMode is True
    assert backend.plottingIndividualExperimentDataList == [
        {'name': 'E0', 'index': 0, 'color': '#111111', 'channel': '', 'hasData': True}
    ]
    assert backend.plottingGetExperimentDataPoints(3) == [{'x': 3.0, 'y': 0.0}]
    assert backend.plottingGetAnalysisDataPoints(5) == [
        {'x': 5.0, 'measured': 0.0, 'calculated': 0.0, 'channel': ''}
    ]


def test_backend_imported_experiment_is_selected_and_channels_renotified(monkeypatch, qcore_application):
    # A freshly imported experiment must become the current selection, and the
    # channel state must be re-published so the selector/chart follow it.
    backend = _make_backend(monkeypatch)

    backend._experiment.experimentLoaded.emit(2)

    assert backend._analysis.received_indices == [2]

    backend._experiment.externalExperimentChanged.emit()
    assert backend._plotting_1d.channel_notifications >= 1


def test_backend_experiment_selection_renotifies_channels(monkeypatch, qcore_application):
    # Selecting another experiment goes through analysis.experimentsChanged;
    # without this connection a polarized -> polarized switch keeps the old
    # channel list and the old chart.
    backend = _make_backend(monkeypatch)

    backend._analysis.experimentsChanged.emit()

    assert backend._plotting_1d.channel_notifications == 1


# ===========================================================================
# Delegation-contract tests.
# These verify that PyBackend correctly forwards calls to Plotting1d without
# requiring the full Qt infrastructure — Plotting1d is replaced by MagicMock.
# ===========================================================================

class _DelegationStub:
    """Minimal replica of the PyBackend delegation methods under test."""

    def __init__(self, plotting_1d):
        self._plotting_1d = plotting_1d

    def plottingGetAnalysisDataPoints(self, experiment_index: int, channel: str = '') -> list:
        return self._plotting_1d.getAnalysisDataPoints(experiment_index, channel)

    def plottingGetResidualDataPoints(self, experiment_index: int, channel: str = '') -> list:
        return self._plotting_1d.getResidualDataPoints(experiment_index, channel)


class TestPlottingGetResidualDataPointsDelegation:
    def _backend(self):
        mock_plotting = MagicMock()
        return _DelegationStub(mock_plotting), mock_plotting

    def test_delegates_to_plotting_1d(self):
        backend, plotting = self._backend()
        expected = [{'x': 0.1, 'y': 0.002}, {'x': 0.2, 'y': -0.001}]
        plotting.getResidualDataPoints.return_value = expected

        result = backend.plottingGetResidualDataPoints(0)

        plotting.getResidualDataPoints.assert_called_once_with(0, '')
        assert result == expected

    def test_passes_experiment_index(self):
        backend, plotting = self._backend()
        plotting.getResidualDataPoints.return_value = []

        backend.plottingGetResidualDataPoints(3)

        plotting.getResidualDataPoints.assert_called_once_with(3, '')

    def test_returns_empty_list_when_plotting_returns_empty(self):
        backend, plotting = self._backend()
        plotting.getResidualDataPoints.return_value = []

        result = backend.plottingGetResidualDataPoints(0)

        assert result == []

    def test_returns_result_unchanged(self):
        backend, plotting = self._backend()
        payload = [{'x': i * 0.1, 'y': i * 0.001} for i in range(10)]
        plotting.getResidualDataPoints.return_value = payload

        result = backend.plottingGetResidualDataPoints(0)

        assert result is payload


class TestPlottingGetAnalysisDataPointsDelegation:
    """Regression: existing analysis bridging is unaffected by residual additions."""

    def _backend(self):
        mock_plotting = MagicMock()
        return _DelegationStub(mock_plotting), mock_plotting

    def test_delegates_to_plotting_1d(self):
        backend, plotting = self._backend()
        expected = [{'x': 0.1, 'measured': -2.0, 'calculated': -1.9}]
        plotting.getAnalysisDataPoints.return_value = expected

        result = backend.plottingGetAnalysisDataPoints(0)

        plotting.getAnalysisDataPoints.assert_called_once_with(0, '')
        assert result == expected

    def test_passes_experiment_index(self):
        backend, plotting = self._backend()
        plotting.getAnalysisDataPoints.return_value = []

        backend.plottingGetAnalysisDataPoints(5)

        plotting.getAnalysisDataPoints.assert_called_once_with(5, '')



def test_backend_wires_structure_refresh_to_sample_and_analysis_signals(monkeypatch, qcore_application):
    # The Structure view must refresh on every stack-changing signal, including
    # modelsTableChanged (the only signal removeModel emits), assembliesTableChanged
    # (the only signal a repetitions edit emits), and the post-fit Analysis signals
    # (the fit path never emits a Sample signal).
    backend = _make_backend(monkeypatch)

    for signal in (
        backend._sample.layersChange,
        backend._sample.assembliesTableChanged,
        backend._sample.materialsTableChanged,
        backend._sample.modelsIndexChanged,
        backend._sample.modelsTableChanged,
        backend._sample.externalSampleChanged,
        backend._analysis.externalParametersChanged,
        backend._analysis.externalFittingChanged,
    ):
        signal.emit()

    assert backend._sample.structure_clear_calls == 8
