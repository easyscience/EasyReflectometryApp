from types import SimpleNamespace
from unittest.mock import MagicMock

import numpy as np
import pytest
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


def test_plotting_analysis_refresh_skips_when_series_not_registered(qcore_application):
    plotting, _project = _make_plotting()
    plotting._chartRefs['QtCharts']['analysisPage']['measuredSerie'] = None
    plotting._chartRefs['QtCharts']['analysisPage']['calculatedSerie'] = None

    plotting.drawCalculatedAndMeasuredOnAnalysisChart()


def test_plotting_get_model_color_fallback(qcore_application):
    plotting, _project = _make_plotting()

    assert plotting.getModelColor(0) == '#111111'
    assert plotting.getModelColor(100) == '#000000'


# ===========================================================================
# Stub-based unit tests for residual / analysis helper methods.
# These run without a live QCoreApplication because Plotting1d is instantiated
# via __new__ with all internals set directly (no Qt signal machinery needed
# for the pure-Python helper methods under test).
# ===========================================================================

class _DataSet1DStub:
    """Minimal DataSet1D for stub-based tests (no PySide6 required)."""
    def __init__(self, name='', x=None, y=None, ye=None, xe=None):
        self.x = x if x is not None else np.empty(0)
        self.y = y if y is not None else np.empty(0)
        self.ye = ye if ye is not None else np.empty(0)
        self.xe = xe if xe is not None else np.empty(0)

    def data_points(self):
        for i in range(len(self.x)):
            yield (self.x[i], self.y[i],
                   self.ye[i] ** 2 if len(self.ye) > i else 0.0)


def _make_exp_data_stub(q, r, ye=None):
    if ye is None:
        ye = np.zeros_like(r)
    return _DataSet1DStub(name='test', x=q, y=r, ye=ye)


def _make_project_stub(q, r_exp, r_calc, q_min=0.0, q_max=1.0, ye=None):
    proj = MagicMock()
    proj.q_min = q_min
    proj.q_max = q_max
    proj.current_experiment_index = 0
    proj.current_model_index = 0
    proj.experimental_data_for_model_at_index.return_value = _make_exp_data_stub(q, r_exp, ye)
    proj.model_data_for_model_at_index.return_value = _DataSet1DStub(name='calc', x=q, y=r_calc)
    proj.sample_data_for_model_at_index.return_value = _DataSet1DStub(name='sample', x=np.array([q_min, q_max]), y=np.array([1.0, 1.0]))
    proj.models = [MagicMock()]
    return proj


def _make_plotting_stub(project, rq4=False):
    proxy = MagicMock()
    proxy._analysis._selected_experiment_indices = [0]
    p = Plotting1d.__new__(Plotting1d)
    p._project_lib = project
    p._proxy = proxy
    p._plot_rq4 = rq4
    p._x_axis_log = False
    p._sld_x_reversed = False
    p._scale_shown = False
    p._bkg_shown = False
    p._sample_data = {}
    p._model_data = {}
    p._sld_data = {}
    p._residual_range_cache = None
    p._chartRefs = {'QtCharts': {'samplePage': {}, 'experimentPage': {}, 'analysisPage': {}}}
    return p


# ---------------------------------------------------------------------------
# _get_aligned_analysis_values
# ---------------------------------------------------------------------------

class TestGetAlignedAnalysisValues:
    def test_returns_correct_q_count(self):
        q = np.array([0.05, 0.10, 0.15, 0.20])
        r_exp = np.array([1e-1, 1e-2, 1e-3, 1e-4])
        r_calc = np.array([1.1e-1, 1.1e-2, 1.1e-3, 1.1e-4])
        proj = _make_project_stub(q, r_exp, r_calc, q_min=0.0, q_max=0.25)
        p = _make_plotting_stub(proj)

        result = p._get_aligned_analysis_values(0)
        assert len(result) == len(q)

    def test_filters_outside_q_range(self):
        q = np.array([0.01, 0.05, 0.10, 0.50])
        r_exp = np.array([1e-1, 1e-2, 1e-3, 1e-4])
        r_calc = np.array([1.1e-1, 1.1e-2, 1.1e-3, 1.1e-4])
        proj = _make_project_stub(q, r_exp, r_calc, q_min=0.02, q_max=0.40)
        p = _make_plotting_stub(proj)

        result = p._get_aligned_analysis_values(0)
        returned_q = [pt['q'] for pt in result]
        assert 0.01 not in returned_q
        assert 0.50 not in returned_q
        assert 0.05 in returned_q
        assert 0.10 in returned_q

    def test_keys_present(self):
        q = np.array([0.05, 0.10])
        r_exp = np.array([1e-2, 1e-3])
        r_calc = np.array([1.1e-2, 1.1e-3])
        proj = _make_project_stub(q, r_exp, r_calc)
        p = _make_plotting_stub(proj)

        result = p._get_aligned_analysis_values(0)
        for pt in result:
            assert 'q' in pt
            assert 'measured' in pt
            assert 'calculated' in pt
            assert 'sigma' in pt

    def test_linear_space_no_log(self):
        q = np.array([0.10])
        r_exp = np.array([1e-2])
        r_calc = np.array([2e-2])
        proj = _make_project_stub(q, r_exp, r_calc)
        p = _make_plotting_stub(proj)

        result = p._get_aligned_analysis_values(0)
        assert len(result) == 1
        assert pytest.approx(result[0]['measured'], rel=1e-6) == 1e-2
        assert pytest.approx(result[0]['calculated'], rel=1e-6) == 2e-2

    def test_rq4_applied_in_linear_space(self):
        q = np.array([0.10])
        r_exp = np.array([1e-2])
        r_calc = np.array([2e-2])
        proj = _make_project_stub(q, r_exp, r_calc)
        p = _make_plotting_stub(proj, rq4=True)

        result = p._get_aligned_analysis_values(0)
        expected_meas = 1e-2 * (0.10 ** 4)
        expected_calc = 2e-2 * (0.10 ** 4)
        assert pytest.approx(result[0]['measured'], rel=1e-6) == expected_meas
        assert pytest.approx(result[0]['calculated'], rel=1e-6) == expected_calc


# ---------------------------------------------------------------------------
# getAnalysisDataPoints
# ---------------------------------------------------------------------------

class TestGetAnalysisDataPoints:
    def test_applies_log10(self):
        q = np.array([0.10])
        r_exp = np.array([1e-2])
        r_calc = np.array([2e-2])
        proj = _make_project_stub(q, r_exp, r_calc)
        p = _make_plotting_stub(proj)

        result = p.getAnalysisDataPoints(0)
        assert len(result) == 1
        assert pytest.approx(result[0]['measured'], rel=1e-6) == np.log10(1e-2)
        assert pytest.approx(result[0]['calculated'], rel=1e-6) == np.log10(2e-2)

    def test_returns_empty_on_error(self):
        proj = MagicMock()
        proj.experimental_data_for_model_at_index.side_effect = RuntimeError('boom')
        proj.q_min = 0.0
        proj.q_max = 1.0
        p = _make_plotting_stub(proj)
        assert p.getAnalysisDataPoints(0) == []


# ---------------------------------------------------------------------------
# getResidualDataPoints
# ---------------------------------------------------------------------------

class TestGetResidualDataPoints:
    def test_residual_is_calc_minus_meas(self):
        """Normalized residual = (calc − meas) / sigma when sigma is given."""
        q = np.array([0.10])
        r_exp = np.array([1e-2])
        r_calc = np.array([3e-2])
        ye = np.array([1e-3])  # sigma = 1e-3
        proj = _make_project_stub(q, r_exp, r_calc, ye=ye)
        p = _make_plotting_stub(proj)

        result = p.getResidualDataPoints(0)
        assert len(result) == 1
        expected = (3e-2 - 1e-2) / 1e-3  # 20.0
        assert pytest.approx(result[0]['y'], rel=1e-6) == expected

    def test_residual_rq4_mode(self):
        """Normalized residual is invariant under the rq4 transform because
        sigma scales the same way as (calc - meas), so the q^4 factor cancels.
        """
        q = np.array([0.10])
        r_exp = np.array([1e-2])
        r_calc = np.array([3e-2])
        ye = np.array([1e-3])
        proj = _make_project_stub(q, r_exp, r_calc, ye=ye)
        p_linear = _make_plotting_stub(proj, rq4=False)
        p_rq4 = _make_plotting_stub(proj, rq4=True)

        res_linear = p_linear.getResidualDataPoints(0)
        res_rq4 = p_rq4.getResidualDataPoints(0)
        assert pytest.approx(res_rq4[0]['y'], rel=1e-6) == res_linear[0]['y']

    def test_residual_zero_when_identical(self):
        q = np.array([0.05, 0.10, 0.15])
        r = np.array([1e-1, 1e-2, 1e-3])
        ye = np.array([0.01, 0.001, 0.0001])
        proj = _make_project_stub(q, r, r.copy(), ye=ye)
        p = _make_plotting_stub(proj)

        result = p.getResidualDataPoints(0)
        for pt in result:
            assert pytest.approx(pt['y'], abs=1e-12) == 0.0

    def test_residual_x_matches_q(self):
        q = np.array([0.05, 0.10, 0.15])
        r_exp = np.array([1e-1, 1e-2, 1e-3])
        r_calc = np.array([1.1e-1, 1.1e-2, 1.1e-3])
        proj = _make_project_stub(q, r_exp, r_calc)
        p = _make_plotting_stub(proj)

        result = p.getResidualDataPoints(0)
        returned_x = [pt['x'] for pt in result]
        assert returned_x == pytest.approx(list(q), rel=1e-6)

    def test_returns_empty_on_error(self):
        proj = MagicMock()
        proj.experimental_data_for_model_at_index.side_effect = RuntimeError('boom')
        proj.q_min = 0.0
        proj.q_max = 1.0
        p = _make_plotting_stub(proj)
        assert p.getResidualDataPoints(0) == []


# ---------------------------------------------------------------------------
# _get_residual_range
# ---------------------------------------------------------------------------

class TestGetResidualRange:
    def test_fallback_when_no_data(self):
        proj = MagicMock()
        proj.experimental_data_for_model_at_index.side_effect = RuntimeError('no data')
        proj.q_min = 0.0
        proj.q_max = 1.0
        proj.models = []
        p = _make_plotting_stub(proj)
        rng = p._get_residual_range()
        assert rng == (0.0, 1.0, -1.0, 1.0)

    def test_x_range_matches_q_domain(self):
        q = np.array([0.05, 0.10, 0.20])
        r_exp = np.array([1e-1, 1e-2, 1e-3])
        r_calc = np.array([1.1e-1, 1.1e-2, 1.1e-3])
        proj = _make_project_stub(q, r_exp, r_calc)
        p = _make_plotting_stub(proj)

        rng = p._get_residual_range()
        assert pytest.approx(rng[0], rel=1e-6) == 0.0
        assert pytest.approx(rng[1], rel=1e-6) == 1.0

    def test_x_range_uses_full_analysis_domain_when_experiment_is_subset(self):
        q = np.array([0.10, 0.20, 0.30])
        r_exp = np.array([1e-1, 1e-2, 1e-3])
        r_calc = np.array([1.1e-1, 1.1e-2, 1.1e-3])
        proj = _make_project_stub(q, r_exp, r_calc, q_min=0.0, q_max=1.0)
        p = _make_plotting_stub(proj)

        rng = p._get_residual_range()
        residual_points = p.getResidualDataPoints(0)

        assert pytest.approx(rng[0], rel=1e-6) == 0.0
        assert pytest.approx(rng[1], rel=1e-6) == 1.0
        assert [point['x'] for point in residual_points] == pytest.approx([0.10, 0.20, 0.30], rel=1e-6)

    def test_y_range_has_margin(self):
        q = np.array([0.10])
        r_exp = np.array([1e-2])
        r_calc = np.array([3e-2])
        ye = np.array([1e-3])
        proj = _make_project_stub(q, r_exp, r_calc, ye=ye)
        p = _make_plotting_stub(proj)

        rng = p._get_residual_range()
        normalized_residual = (3e-2 - 1e-2) / 1e-3  # 20.0
        assert rng[2] < normalized_residual
        assert rng[3] > normalized_residual

    def test_rq4_affects_range(self):
        """Normalized residual range is identical in linear and rq4 modes."""
        q = np.array([0.10])
        r_exp = np.array([1e-2])
        r_calc = np.array([3e-2])
        ye = np.array([1e-3])
        proj = _make_project_stub(q, r_exp, r_calc, ye=ye)

        p_linear = _make_plotting_stub(proj, rq4=False)
        p_rq4 = _make_plotting_stub(proj, rq4=True)

        rng_linear = p_linear._get_residual_range()
        rng_rq4 = p_rq4._get_residual_range()
        assert pytest.approx(rng_linear, rel=1e-6) == rng_rq4

