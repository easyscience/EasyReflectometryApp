"""Wiring tests for polarization controls in the Experiment tab.

These mirror the lightweight QML text-assertion style used by
``test_qml_fitting_progress_ui.py``: the .qml sources are read as text and the
polarization wiring contract is asserted. They guard the GUI track of
POLARIZATION_IMPL_GUI.md (mock data fn, BackendWrapper guard, sidebar selector,
and the channel-aware ExperimentView mode incl. the §3.2.8 stagger-conflict rule).
"""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'EasyReflectometryApp'

MOCK_POLARIZATION = APP / 'Backends' / 'Mock' / 'Polarization.qml'
BACKEND_WRAPPER = APP / 'Gui' / 'Globals' / 'BackendWrapper.qml'
EXPERIMENT_SIDEBAR_BASIC = APP / 'Gui' / 'Pages' / 'Experiment' / 'Sidebar' / 'Basic' / 'Layout.qml'
EXPERIMENT_POLARIZATION_GROUP = APP / 'Gui' / 'Pages' / 'Experiment' / 'Sidebar' / 'Basic' / 'Groups' / 'Polarization.qml'
EXPERIMENT_SIDEBAR_ADVANCED = APP / 'Gui' / 'Pages' / 'Experiment' / 'Sidebar' / 'Advanced' / 'Layout.qml'
EXPERIMENT_VIEW = APP / 'Gui' / 'Pages' / 'Experiment' / 'MainContent' / 'ExperimentView.qml'
ANALYSIS_SIDEBAR_ADVANCED = APP / 'Gui' / 'Pages' / 'Analysis' / 'Sidebar' / 'Advanced' / 'Layout.qml'


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


# --- Mock backend data contract -------------------------------------------------

def test_mock_exposes_experiment_channel_data_points_with_error_bounds():
    qml = _read(MOCK_POLARIZATION)
    assert 'function getExperimentChannelDataPoints(experimentIndex, channelKey)' in qml
    # Must emit the {x, y, errorUpper, errorLower} shape consumed by ExperimentView.
    assert "'errorUpper'" in qml
    assert "'errorLower'" in qml


# --- BackendWrapper guarded slot ------------------------------------------------

def test_backend_wrapper_guards_experiment_channel_data_points():
    qml = _read(BACKEND_WRAPPER)
    assert 'function plottingGetExperimentChannelDataPoints(experimentIndex, channelKey)' in qml
    assert 'activeBackend.polarization.getExperimentChannelDataPoints(experimentIndex, channelKey)' in qml
    # The new slot must be inside a try/catch like its siblings.
    block = qml.split('function plottingGetExperimentChannelDataPoints', 1)[1].split('function ', 1)[0]
    assert 'try {' in block
    assert 'catch (e)' in block
    assert 'return []' in block


# --- Experiment sidebar ---------------------------------------------------------

def test_experiment_sidebar_mounts_channel_selector_only():
    qml = _read(EXPERIMENT_SIDEBAR_ADVANCED)
    assert 'GuiComponents.PolarizationChannelSelector {}' in qml
    assert 'import Gui.Components as GuiComponents' in qml
    # No SLD profile in the Experiment tab -> no SLD component selector.
    assert 'SldComponentSelector' not in qml


# --- Manual 'Polarized' toggle --------------------------------------------------

def test_experiment_basic_sidebar_mounts_polarization_toggle():
    qml = _read(EXPERIMENT_SIDEBAR_BASIC)
    assert 'Groups.Polarization' in qml


def test_polarization_toggle_group_wires_setpolarized():
    qml = _read(EXPERIMENT_POLARIZATION_GROUP)
    assert 'Globals.BackendWrapper.polarizationPolarized' in qml
    assert 'Globals.BackendWrapper.polarizationSetPolarized(checked)' in qml


def test_backend_wrapper_exposes_polarized_passthroughs():
    qml = _read(BACKEND_WRAPPER)
    assert 'property bool polarizationPolarized' in qml
    assert 'function polarizationSetPolarized(value)' in qml
    assert 'activeBackend.polarization.setPolarized(value)' in qml


# --- ExperimentView polarization mode -------------------------------------------

def test_experiment_view_defines_polarization_mode_gated_on_measured_channels():
    qml = _read(EXPERIMENT_VIEW)
    assert 'property bool isPolarizationMode:' in qml
    assert 'Globals.BackendWrapper.polarizationAvailable' in qml
    # Gate narrowly: requires at least one channel with measured data (Issue #5),
    # and uses the correct index property (not the non-existent plottingCurrentExperimentIndex).
    assert 'polarizationGetExperimentChannels(' in qml
    assert 'analysisExperimentsCurrentIndex' in qml
    assert 'plottingCurrentExperimentIndex' not in qml
    assert '.hasMeasured' in qml


def test_experiment_view_uses_channel_aware_data_source():
    qml = _read(EXPERIMENT_VIEW)
    assert 'plottingGetExperimentChannelDataPoints(seriesSet.expIndex, seriesSet.channelKey)' in qml


def test_experiment_view_has_polarization_signal_connections():
    qml = _read(EXPERIMENT_VIEW)
    assert 'function onPolarizationDisplayChanged()' in qml
    assert 'function onPolarizationDataChanged()' in qml
    assert 'function refreshDynamicSeriesData()' in qml


def test_experiment_view_staggers_all_three_series_uniformly():
    """Issue #11: measured + both error bounds must share the same per-channel offset."""
    qml = _read(EXPERIMENT_VIEW)
    assert 'function staggeredY(value, channelIndex)' in qml
    assert 'staggeredY(channelPoint.y, seriesSet.channelIndex)' in qml
    assert 'staggeredY(channelPoint.errorUpper, seriesSet.channelIndex)' in qml
    assert 'staggeredY(channelPoint.errorLower, seriesSet.channelIndex)' in qml


@pytest.mark.parametrize(
    'guard_context',
    [
        'onUseStaggeredPlottingChanged',
        'onStaggeringFactorChanged',
    ],
)
def test_experiment_view_suppresses_multi_experiment_stagger_in_polarization_mode(guard_context):
    """§3.2.8: the existing multi-experiment stagger watchers early-return in polarization mode."""
    qml = _read(EXPERIMENT_VIEW)
    # The handler body must start with an isPolarizationMode early-return.
    body = qml.split(guard_context, 1)[1]
    # Look within the first part of the handler (before the legacy multi-experiment logic).
    head = body[: body.find('isMultiExperimentMode')]
    assert 'isPolarizationMode) return' in head


def test_experiment_view_has_polarization_legend():
    qml = _read(EXPERIMENT_VIEW)
    assert 'Polarization channels:' in qml
    assert 'visiblePolarizationChannels()' in qml


def test_experiment_view_rebuilds_series_on_mode_change():
    qml = _read(EXPERIMENT_VIEW)
    assert 'onIsPolarizationModeChanged:' in qml


# --- Regression: Analysis sidebar unchanged -------------------------------------

def test_analysis_sidebar_still_has_both_selectors():
    qml = _read(ANALYSIS_SIDEBAR_ADVANCED)
    assert 'GuiComponents.PolarizationChannelSelector {}' in qml
    assert 'GuiComponents.SldComponentSelector {}' in qml
