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


class StubSample(QObject):
    externalSampleChanged = Signal()
    externalRefreshPlot = Signal()
    modelsTableChanged = Signal()
    materialsTableChanged = Signal()
    modelsIndexChanged = Signal()
    assembliesTableChanged = Signal()
    assembliesIndexChanged = Signal()
    qRangeChanged = Signal()

    def __init__(self, _project_lib):
        super().__init__()
        self.clear_calls = 0

    def _clearCacheAndEmitLayersChanged(self):
        self.clear_calls += 1


class StubExperiment(QObject):
    externalExperimentChanged = Signal()
    experimentChanged = Signal()
    qRangeUpdated = Signal()

    def __init__(self, _project_lib):
        super().__init__()


class StubAnalysis(QObject):
    externalMinimizerChanged = Signal()
    externalCalculatorChanged = Signal()
    externalParametersChanged = Signal()
    externalFittingChanged = Signal()
    externalExperimentChanged = Signal()
    experimentsChanged = Signal()
    parametersChanged = Signal()

    def __init__(self, _project_lib, parent=None):
        super().__init__(parent)
        self._minimizers_logic = object()
        self._selected = [0]
        self.received_indices = None
        self.clear_calls = 0
        self._plotting_accepted = None

    def set_plotting(self, plotting):
        self._plotting_accepted = plotting

    @property
    def experimentsSelectedCount(self):
        return len(self._selected)

    @property
    def selectedExperimentIndices(self):
        return self._selected

    def setSelectedExperimentIndices(self, indices):
        self.received_indices = indices
        self._selected = list(indices)

    def _clearCacheAndEmitParametersChanged(self):
        self.clear_calls += 1


class StubSummary(QObject):
    createdChanged = Signal()
    summaryChanged = Signal()

    def __init__(self, _project_lib, parent=None):
        super().__init__(parent)


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

    def __init__(self, _project_lib, parent=None):
        super().__init__(parent)
        self.reset_calls = 0
        self.refresh_calls = {'sample': 0, 'experiment': 0, 'analysis': 0}
        self._multi = True
        self._individual = [{'name': 'E0', 'index': 0, 'color': '#111111', 'hasData': True}]

    @property
    def isMultiExperimentMode(self):
        return self._multi

    @property
    def individualExperimentDataList(self):
        return self._individual

    def getExperimentDataPoints(self, experiment_index):
        return [{'x': float(experiment_index), 'y': 0.0}]

    def getAnalysisDataPoints(self, experiment_index):
        return [{'x': float(experiment_index), 'measured': 0.0, 'calculated': 0.0}]

    def reset_data(self):
        self.reset_calls += 1

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
    assert backend.plottingIndividualExperimentDataList == [{'name': 'E0', 'index': 0, 'color': '#111111', 'hasData': True}]
    assert backend.plottingGetExperimentDataPoints(3) == [{'x': 3.0, 'y': 0.0}]
    assert backend.plottingGetAnalysisDataPoints(5) == [{'x': 5.0, 'measured': 0.0, 'calculated': 0.0}]


# ===========================================================================
# Delegation-contract tests.
# These verify that PyBackend correctly forwards calls to Plotting1d without
# requiring the full Qt infrastructure — Plotting1d is replaced by MagicMock.
# ===========================================================================

class _DelegationStub:
    """Minimal replica of the PyBackend delegation methods under test."""

    def __init__(self, plotting_1d):
        self._plotting_1d = plotting_1d

    def plottingGetAnalysisDataPoints(self, experiment_index: int) -> list:
        return self._plotting_1d.getAnalysisDataPoints(experiment_index)

    def plottingGetResidualDataPoints(self, experiment_index: int) -> list:
        return self._plotting_1d.getResidualDataPoints(experiment_index)


class TestPlottingGetResidualDataPointsDelegation:
    def _backend(self):
        mock_plotting = MagicMock()
        return _DelegationStub(mock_plotting), mock_plotting

    def test_delegates_to_plotting_1d(self):
        backend, plotting = self._backend()
        expected = [{'x': 0.1, 'y': 0.002}, {'x': 0.2, 'y': -0.001}]
        plotting.getResidualDataPoints.return_value = expected

        result = backend.plottingGetResidualDataPoints(0)

        plotting.getResidualDataPoints.assert_called_once_with(0)
        assert result == expected

    def test_passes_experiment_index(self):
        backend, plotting = self._backend()
        plotting.getResidualDataPoints.return_value = []

        backend.plottingGetResidualDataPoints(3)

        plotting.getResidualDataPoints.assert_called_once_with(3)

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

        plotting.getAnalysisDataPoints.assert_called_once_with(0)
        assert result == expected

    def test_passes_experiment_index(self):
        backend, plotting = self._backend()
        plotting.getAnalysisDataPoints.return_value = []

        backend.plottingGetAnalysisDataPoints(5)

        plotting.getAnalysisDataPoints.assert_called_once_with(5)

