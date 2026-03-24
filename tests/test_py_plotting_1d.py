from types import SimpleNamespace

import numpy as np
from PySide6.QtCore import QObject

from EasyReflectometryApp.Backends.Py.plotting_1d import Plotting1d


class FakeSeries:
    def __init__(self):
        self.clears = 0
        self.points = []

    def clear(self):
        self.clears += 1
        self.points.clear()

    def append(self, x, y):
        self.points.append((x, y))


class FakeData:
    def __init__(self, x=None, y=None, ye=None, model=None):
        self.x = np.asarray([] if x is None else x)
        self.y = np.asarray([] if y is None else y)
        self.ye = np.asarray([] if ye is None else ye)
        self.model = model

    def data_points(self):
        if self.ye.size > 0:
            return list(zip(self.x, self.y, self.ye, strict=False))
        return list(zip(self.x, self.y, strict=False))


class FakeProject:
    def __init__(self):
        self.current_model_index = 0
        self.current_experiment_index = 0
        self.q_min = 0.01
        self.q_max = 0.5
        self.models = [
            SimpleNamespace(color='#111111', scale=SimpleNamespace(value=0.0), background=SimpleNamespace(value=0.0)),
            SimpleNamespace(color='#222222', scale=SimpleNamespace(value=2.0), background=SimpleNamespace(value=1e-6)),
        ]
        self._experiments = {0: object(), 1: object()}
        self._sample = {
            0: FakeData(x=[0.1, 0.2], y=[1.0, 2.0]),
            1: FakeData(x=[0.05, 0.4], y=[3.0, 4.0]),
        }
        self._sld = {
            0: FakeData(x=[1.0, 2.0], y=[-0.5, 0.5]),
            1: FakeData(x=[1.5, 3.0], y=[-1.0, 1.0]),
        }
        self._exp = {
            0: FakeData(x=[0.1, 0.2], y=[1e-6, 1e-5], ye=[1e-8, 1e-8], model=self.models[0]),
            1: FakeData(x=[0.15, 0.3], y=[2e-6, 3e-5], ye=[1e-8, 1e-8], model=self.models[1]),
        }

    def sample_data_for_model_at_index(self, index):
        return self._sample[index]

    def model_data_for_model_at_index(self, index, q_values=None):
        if q_values is None:
            return FakeData(x=[0.1, 0.2], y=[1e-6, 2e-6])
        return FakeData(x=q_values, y=np.ones_like(q_values) * 2e-6)

    def sld_data_for_model_at_index(self, index):
        return self._sld[index]

    def experimental_data_for_model_at_index(self, index):
        return self._exp[index]


class FakeAnalysisProxy:
    def __init__(self, selected):
        self._selected_experiment_indices = selected

    def get_concatenated_experiment_data(self):
        return FakeData(x=[0.1, 0.2, 0.3], y=[1e-6, 2e-6, 3e-6], ye=[1e-8, 1e-8, 1e-8])

    def get_individual_experiment_data_list(self):
        return [
            {'name': 'E0', 'color': '#111111', 'index': 0, 'data': FakeData(x=[0.1], y=[1e-6], ye=[1e-8])},
            {'name': 'E1', 'color': '#222222', 'index': 1, 'data': FakeData(x=[0.2], y=[2e-6], ye=[1e-8])},
        ]


class FakeBackendParent(QObject):
    def __init__(self, selected):
        super().__init__()
        self._analysis = FakeAnalysisProxy(selected)


def _make_plotting(selected=None):
    project = FakeProject()
    proxy = FakeBackendParent([0] if selected is None else selected)
    plotting = Plotting1d(project, parent=proxy)
    plotting._chartRefs['QtCharts']['experimentPage']['measuredSerie'] = FakeSeries()
    plotting._chartRefs['QtCharts']['experimentPage']['errorUpperSerie'] = FakeSeries()
    plotting._chartRefs['QtCharts']['experimentPage']['errorLowerSerie'] = FakeSeries()
    plotting._chartRefs['QtCharts']['analysisPage']['measuredSerie'] = FakeSeries()
    plotting._chartRefs['QtCharts']['analysisPage']['calculatedSerie'] = FakeSeries()
    return plotting, project


def test_plotting_mode_and_axis_toggles_emit_signals(qcore_application):
    plotting, _project = _make_plotting()
    counts = {'plot': 0, 'axis': 0, 'sld': 0, 'ref': 0}
    plotting.plotModeChanged.connect(lambda: counts.__setitem__('plot', counts['plot'] + 1))
    plotting.axisTypeChanged.connect(lambda: counts.__setitem__('axis', counts['axis'] + 1))
    plotting.sldAxisReversedChanged.connect(lambda: counts.__setitem__('sld', counts['sld'] + 1))
    plotting.referenceLineVisibilityChanged.connect(lambda: counts.__setitem__('ref', counts['ref'] + 1))

    assert plotting.plotRQ4 is False
    assert plotting.yMainAxisTitle == 'R(q)'
    plotting.togglePlotRQ4()
    assert plotting.plotRQ4 is True
    assert plotting.yMainAxisTitle == 'R(q)×q⁴'

    assert plotting.xAxisType == 'linear'
    plotting.toggleXAxisType()
    assert plotting.xAxisType == 'log'

    assert plotting.sldXDataReversed is False
    plotting.reverseSldXData()
    assert plotting.sldXDataReversed is True

    assert plotting.scaleShown is False
    assert plotting.bkgShown is False
    plotting.flipScaleShown()
    plotting.flipBkgShown()
    assert plotting.scaleShown is True
    assert plotting.bkgShown is True
    assert counts == {'plot': 1, 'axis': 1, 'sld': 1, 'ref': 2}


def test_plotting_reference_lines_use_defaults_and_visibility(qcore_application):
    plotting, _project = _make_plotting()

    assert plotting.getBackgroundData() == []
    assert plotting.getScaleData() == []

    plotting.flipBkgShown()
    plotting.flipScaleShown()
    bkg = plotting.getBackgroundData()
    scale = plotting.getScaleData()

    assert len(bkg) == 2
    assert len(scale) == 2
    assert bkg[0]['y'] == -10.0
    assert scale[0]['y'] == 0.0

    bkg_analysis = plotting.getBackgroundDataForAnalysis()
    scale_analysis = plotting.getScaleDataForAnalysis()
    assert len(bkg_analysis) == 2
    assert len(scale_analysis) == 2


def test_plotting_empty_range_fallbacks_and_experiment_min_y(qcore_application):
    plotting, project = _make_plotting()
    project._sample = {0: FakeData(), 1: FakeData()}
    project._sld = {0: FakeData(), 1: FakeData()}
    project._exp = {0: FakeData(x=[0.1, 0.2], y=[0.0, -1.0], ye=[0.0, 0.0])}

    assert plotting.sampleMinX == 0.0
    assert plotting.sampleMaxX == 1.0
    assert plotting.sampleMinY == -10.0
    assert plotting.sampleMaxY == 0.0

    assert plotting.sldMinX == 0.0
    assert plotting.sldMaxX == 1.0
    assert plotting.sldMinY == -1.0
    assert plotting.sldMaxY == 1.0

    assert plotting.experimentMinY == -10.0


def test_plotting_multi_experiment_mode_refreshes_via_signal(qcore_application):
    plotting, _project = _make_plotting(selected=[0, 1])
    count = {'changed': 0}
    plotting.experimentDataChanged.connect(lambda: count.__setitem__('changed', count['changed'] + 1))

    assert plotting.isMultiExperimentMode is True
    assert len(plotting.individualExperimentDataList) == 2

    plotting.drawMeasuredOnExperimentChart()
    plotting.drawCalculatedAndMeasuredOnAnalysisChart()

    assert count['changed'] == 2


def test_plotting_get_model_color_fallback(qcore_application):
    plotting, _project = _make_plotting()

    assert plotting.getModelColor(0) == '#111111'
    assert plotting.getModelColor(100) == '#000000'
