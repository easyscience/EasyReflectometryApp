"""Tests for the Polarization backend (manual toggle, separate files per channel)."""

import numpy as np
import pytest

from EasyReflectometryApp.Backends.Py.polarization import Polarization


class _ExpData:
    def __init__(self, x, y, ye):
        self.x = np.asarray(x, dtype=float)
        self.y = np.asarray(y, dtype=float)
        self.ye = np.asarray(ye, dtype=float)


class _ProjectLib:
    def __init__(self, experiments):
        # experiments: dict index -> _ExpData (keys() count is what the backend reads)
        self._experiments = experiments

    def experimental_data_for_model_at_index(self, index):
        return self._experiments[index]


class _Plotting:
    """Records delegated calls and returns identifiable sentinels."""

    def __init__(self):
        self.calls = []

    def getExperimentDataPoints(self, index):
        self.calls.append(('experiment', index))
        return [{'x': float(index), 'y': 1.0, 'errorUpper': 1.1, 'errorLower': 0.9}]

    def getAnalysisDataPoints(self, index):
        self.calls.append(('analysis', index))
        return [{'x': float(index), 'measured': -1.0, 'calculated': -1.0}]

    def getResidualDataPoints(self, index):
        self.calls.append(('residual', index))
        return [{'x': float(index), 'y': 0.0}]

    def getSampleDataPointsForModel(self, index):
        self.calls.append(('sample', index))
        return [{'x': float(index), 'y': -1.0}]

    def getSldDataPointsForModel(self, index):
        self.calls.append(('sld', index))
        return [{'x': 0.0, 'y': 2.0}]


def _make_polarization(num_experiments=4):
    experiments = {}
    for i in range(num_experiments):
        # Distinct measured levels so spin asymmetry is non-trivial.
        x = np.linspace(0.01, 0.3, 20)
        y = np.full_like(x, 0.5 - 0.1 * i)
        ye = np.full_like(x, 0.01)
        experiments[i] = _ExpData(x, y, ye)

    project_lib = _ProjectLib(experiments)
    plotting = _Plotting()
    pol = Polarization(project_lib, plotting)
    return pol, plotting


# --- availability ---------------------------------------------------------------

def test_not_available_until_toggled_on(qcore_application):
    pol, _ = _make_polarization(num_experiments=4)
    assert pol.available is False
    pol.setPolarized(True)
    assert pol.available is True
    assert pol.polarized is True


def test_not_available_when_no_experiments_even_if_toggled(qcore_application):
    pol, _ = _make_polarization(num_experiments=0)
    pol.setPolarized(True)
    assert pol.available is False


# --- channel mapping ------------------------------------------------------------

def test_channel_enabled_reflects_loaded_file_count(qcore_application):
    pol, _ = _make_polarization(num_experiments=2)
    channels = pol.channels
    keys = [c['key'] for c in channels]
    assert keys == ['pp', 'mm', 'pm', 'mp']
    enabled = {c['key']: c['enabled'] for c in channels}
    assert enabled == {'pp': True, 'mm': True, 'pm': False, 'mp': False}


def test_toggle_on_defaults_visible_to_available_channels(qcore_application):
    pol, _ = _make_polarization(num_experiments=3)
    pol.setPolarized(True)
    assert sorted(pol.visibleChannelKeys) == ['mm', 'pm', 'pp']


# --- data delegation ------------------------------------------------------------

def test_experiment_channel_data_maps_key_to_loaded_file(qcore_application):
    pol, plotting = _make_polarization(num_experiments=4)
    pol.getExperimentChannelDataPoints(0, 'pm')  # pm -> index 2
    assert ('experiment', 2) in plotting.calls


def test_unavailable_channel_returns_empty(qcore_application):
    pol, plotting = _make_polarization(num_experiments=2)
    assert pol.getExperimentChannelDataPoints(0, 'mp') == []  # mp -> index 3, not loaded
    assert plotting.calls == []


def test_analysis_and_residual_channel_data_delegate_by_index(qcore_application):
    pol, plotting = _make_polarization(num_experiments=4)
    pol.getAnalysisChannelDataPoints(0, 'mm')  # -> index 1
    pol.getPolarizationResidualDataPoints(0, 'mp')  # -> index 3
    assert ('analysis', 1) in plotting.calls
    assert ('residual', 3) in plotting.calls


def test_sld_component_nuclear_delegates_magnetic_empty(qcore_application):
    pol, plotting = _make_polarization(num_experiments=4)
    assert pol.getSldComponentDataPoints(0, 'nuclear') == [{'x': 0.0, 'y': 2.0}]
    assert pol.getSldComponentDataPoints(0, 'magnetic') == []


def test_magnetic_sld_component_unavailable(qcore_application):
    pol, _ = _make_polarization(num_experiments=4)
    components = {c['key']: c['available'] for c in pol.sldComponents}
    assert components == {'nuclear': True, 'magnetic': False}


# --- visibility setters emit displayChanged ------------------------------------

@pytest.mark.parametrize(
    'action',
    [
        lambda p: p.setChannelVisible('pm', True),
        lambda p: p.setVisibleChannelKeys(['pp']),
        lambda p: p.setStaggerEnabled(True),
        lambda p: p.setStaggerFactor(1.5),
        lambda p: p.setPolarized(True),
    ],
)
def test_setters_emit_display_changed(action, qcore_application):
    pol, _ = _make_polarization(num_experiments=4)
    fired = []
    pol.displayChanged.connect(lambda: fired.append(True))
    action(pol)
    assert fired == [True]


def test_set_stagger_values_round_trip(qcore_application):
    pol, _ = _make_polarization(num_experiments=4)
    pol.setStaggerEnabled(True)
    pol.setStaggerFactor(2.0)
    assert pol.staggerEnabled is True
    assert pol.staggerFactor == 2.0


# --- spin asymmetry -------------------------------------------------------------

def test_spin_asymmetry_matches_formula(qcore_application):
    pol, _ = _make_polarization(num_experiments=2)
    result = pol.getSpinAsymmetryDataPoints(0)
    # pp level = 0.5, mm level = 0.4 -> SA = (0.5-0.4)/(0.5+0.4)
    expected = (0.5 - 0.4) / (0.5 + 0.4)
    assert len(result['x']) > 0
    assert result['measured'][0] == pytest.approx(expected)
    assert all(s >= 0 for s in result['sigma'])


def test_spin_asymmetry_empty_without_two_channels(qcore_application):
    pol, _ = _make_polarization(num_experiments=1)
    result = pol.getSpinAsymmetryDataPoints(0)
    assert result == {'x': [], 'measured': [], 'sigma': [], 'calculated': []}
