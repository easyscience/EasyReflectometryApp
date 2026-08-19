import inspect

import numpy as np

# Registers the QtCharts wrapper types with shiboken: without this, a series
# passed in from QML arrives as a bare QObject (no append/replaceNp methods)
# and every one-call series fill silently falls back to the slow path.
import PySide6.QtCharts  # noqa: F401
from EasyApplication.Logic.Logging import console
from easyreflectometry import Project as ProjectLib
from easyreflectometry.data import DataSet1D
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .helpers import IO
from .logic.experiments import CHANNEL_COLORS
from .logic.experiments import CHANNEL_LABELS
from .logic.experiments import experiment_channel_values
from .logic.experiments import flatten_polarized

PLOT_BACKEND = 'QtCharts'


class Plotting1d(QObject):
    chartRefsChanged = Signal()
    sldChartRangesChanged = Signal()
    sampleChartRangesChanged = Signal()
    experimentChartRangesChanged = Signal()
    experimentDataChanged = Signal()
    samplePageDataChanged = Signal()  # Signal for QML to refresh sample page charts
    samplePageResetAxes = Signal()  # Signal for QML to reset chart axes after data load

    # New signals for plot mode properties
    plotModeChanged = Signal()
    axisTypeChanged = Signal()
    sldAxisReversedChanged = Signal()
    referenceLineVisibilityChanged = Signal()

    # Posterior predictive signal
    posteriorPredictiveDataChanged = Signal()
    posteriorPredictiveSldDataChanged = Signal()

    # Polarized-experiment channel selection.
    # channelSelectionChanged: the visible-channel set changed.
    # experimentChannelsChanged: the current experiment (and therefore its
    #   polarization state and channel list) changed. QML properties depending
    #   on the current experiment must be notified by this one; it is emitted
    #   from PyBackend whenever experiment selection/addition/removal happens.
    channelSelectionChanged = Signal()
    experimentChannelsChanged = Signal()

    # Magnetic depth profiles (Phase 5a).
    # magneticProfileChanged: which magnetic curves are drawn, or whether any
    #   model is magnetic at all, changed — the SLD chart rebuilds its series.
    magneticProfileChanged = Signal()
    # Spin asymmetry (Phase 5b/5c): availability or content of the SA charts.
    spinAsymmetryChanged = Signal()

    # Class-level default so instances constructed without __init__ (test stubs)
    # still have a channel selection; setChannelVisible replaces it per instance.
    _visible_channels: frozenset = frozenset({'pp', 'pm', 'mp', 'mm'})
    # Magnetic SLD curves drawn on top of the nuclear profile. The spin-up and
    # spin-down potentials are on by default: where a layer is non-magnetic they
    # collapse onto the nuclear curve, so a weakly magnetic sample still looks
    # like the familiar chart. rho_m/theta_m are parameter views and are opt-in.
    _visible_sld_curves: frozenset = frozenset({'spin_up', 'spin_down'})
    # Why the magnetic profiles of a magnetic model could not be computed
    # ('' = no failure). Class-level default for test stubs without __init__.
    _magnetic_profile_error: str = ''
    # Cached result of the library channel-API check (None = not checked yet).
    _channel_api_error = None

    def __init__(self, project_lib: ProjectLib, parent=None):
        super().__init__(parent)
        self._project_lib = project_lib
        self._proxy = parent
        self._currentLib1d = 'QtCharts'
        self._sample_data = {}
        self._model_data = {}
        self._sld_data = {}

        # Plot mode state
        self._plot_rq4 = False
        self._x_axis_log = False
        self._sld_x_reversed = False
        self._scale_shown = False
        self._bkg_shown = False
        self._residual_range_cache = None

        # Spin channels shown for polarized experiments (channel-value strings).
        self._visible_channels = frozenset({'pp', 'pm', 'mp', 'mm'})
        # Magnetic profile curves shown on the SLD chart (both pages share it).
        self._visible_sld_curves = frozenset({'spin_up', 'spin_down'})
        # Spin asymmetry per experiment index; cleared with the other plot data.
        self._spin_asymmetry_cache: dict = {}
        # Magnetic depth profiles per model index; a refl1d evaluation each, and
        # every chart refresh reads them several times.
        self._magnetic_profile_cache: dict = {}
        self._magnetic_profile_error = ''

        # Posterior predictive state
        self._posterior_q: list = []
        self._posterior_median: list = []
        self._posterior_lower: list = []
        self._posterior_upper: list = []

        # Posterior predictive SLD state
        self._posterior_sld_z: list = []
        self._posterior_sld_median: list = []
        self._posterior_sld_lower: list = []
        self._posterior_sld_upper: list = []
        self._chartRefs = {
            'QtCharts': {
                'samplePage': {
                    'sampleSerie': None,
                    'sldSerie': None,
                },
                'experimentPage': {
                    'measuredSerie': None,
                    'errorUpperSerie': None,
                    'errorLowerSerie': None,
                },
                'analysisPage': {
                    'calculatedSerie': None,
                    'measuredSerie': None,
                    'sldSerie': None,
                },
            }
        }

    def reset_data(self):
        self._sample_data = {}
        self._model_data = {}
        self._sld_data = {}
        self._residual_range_cache = None
        self._spin_asymmetry_cache = {}
        self._magnetic_profile_cache = {}
        console.debug(IO.formatMsg('sub', 'Sample and SLD data cleared'))

    def _apply_rq4(self, x, y):
        """Apply R(q)×q⁴ transformation if enabled.

        Works with both numpy arrays and scalar values.
        """
        if self._plot_rq4:
            return y * (x**4)
        return y

    def _qtcharts_series_ref(self, page: str, serie: str):
        return self._chartRefs['QtCharts'].get(page, {}).get(serie)

    def _clear_qtcharts_series(self, page: str, *series_names: str) -> bool:
        missing_series = []
        for series_name in series_names:
            series_ref = self._qtcharts_series_ref(page, series_name)
            if series_ref is None:
                missing_series.append(series_name)
                continue
            series_ref.clear()

        if missing_series:
            console.debug(
                IO.formatMsg(
                    'sub',
                    f'{page} series unavailable',
                    ', '.join(missing_series),
                    'skipping redraw',
                )
            )
            return False

        return True

    # R(q)×q⁴ mode
    @Property(bool, notify=plotModeChanged)
    def plotRQ4(self) -> bool:
        """Return whether R(q)×q⁴ mode is enabled."""
        return self._plot_rq4

    @Slot()
    def togglePlotRQ4(self) -> None:
        """Toggle R(q)×q⁴ plotting mode."""
        self._plot_rq4 = not self._plot_rq4
        self.plotModeChanged.emit()
        # Refresh all charts with new mode
        self.sampleChartRangesChanged.emit()
        self.experimentChartRangesChanged.emit()
        self.samplePageDataChanged.emit()
        # Notify QML to re-read posterior predictive properties
        # so transforms are re-applied with the new RQ4 setting.
        self.posteriorPredictiveDataChanged.emit()

    @Property(str, notify=plotModeChanged)
    def yMainAxisTitle(self) -> str:
        """Return Y-axis title based on current plot mode."""
        return 'R(q)×q⁴' if self._plot_rq4 else 'R(q)'

    # X-axis type (log/linear)
    @Property(bool, notify=axisTypeChanged)
    def xAxisLog(self) -> bool:
        """Return whether X-axis is logarithmic."""
        return self._x_axis_log

    @Slot()
    def toggleXAxisType(self) -> None:
        """Toggle between linear and logarithmic X-axis."""
        self._x_axis_log = not self._x_axis_log
        self.axisTypeChanged.emit()

    @Property(str, notify=axisTypeChanged)
    def xAxisType(self) -> str:
        """Return X-axis type as string for QML."""
        return 'log' if self._x_axis_log else 'linear'

    # SLD X-axis reversal
    @Property(bool, notify=sldAxisReversedChanged)
    def sldXDataReversed(self) -> bool:
        """Return whether SLD X-axis is reversed."""
        return self._sld_x_reversed

    @Slot()
    def reverseSldXData(self) -> None:
        """Toggle SLD X-axis reversal."""
        self._sld_x_reversed = not self._sld_x_reversed
        self.sldAxisReversedChanged.emit()
        self.sldChartRangesChanged.emit()

    # Reference line visibility
    @Property(bool, notify=referenceLineVisibilityChanged)
    def scaleShown(self) -> bool:
        """Return whether scale reference line is shown."""
        return self._scale_shown

    @Slot()
    def flipScaleShown(self) -> None:
        """Toggle scale line visibility."""
        self._scale_shown = not self._scale_shown
        self.referenceLineVisibilityChanged.emit()

    @Property(bool, notify=referenceLineVisibilityChanged)
    def bkgShown(self) -> bool:
        """Return whether background reference line is shown."""
        return self._bkg_shown

    @Slot()
    def flipBkgShown(self) -> None:
        """Toggle background line visibility."""
        self._bkg_shown = not self._bkg_shown
        self.referenceLineVisibilityChanged.emit()

    def _get_reference_line_data(self, param_attr: str, default_log: float, use_analysis_range: bool) -> list:
        """Build a horizontal reference line for the given model parameter.

        :param param_attr: Model attribute name ('background' or 'scale')
        :param default_log: Default log10 value if parameter <= 0
        :param use_analysis_range: If True, use sample/analysis x-range; if False, use experimental data x-range
        """
        try:
            model_idx = self._project_lib.current_model_index
            model = self._project_lib.models[model_idx]

            if use_analysis_range:
                x_min, x_max = self._get_all_models_sample_range()[0:2]
                if x_min == float('inf') or x_max == float('-inf'):
                    return []
            else:
                exp_idx = self._project_lib.current_experiment_index
                exp_data = flatten_polarized(
                    self._project_lib.experimental_data_for_model_at_index(exp_idx), self._visible_channels
                )
                if exp_data.x is None or len(exp_data.x) == 0:
                    return []
                x_min, x_max = float(exp_data.x[0]), float(exp_data.x[-1])

            param_value = getattr(model, param_attr).value
            y_log = float(np.log10(param_value)) if param_value > 0 else default_log
            return [{'x': float(x_min), 'y': y_log}, {'x': float(x_max), 'y': y_log}]
        except (IndexError, AttributeError, TypeError) as e:
            console.debug(f'Error getting {param_attr} reference line data: {e}')
            return []

    @Slot(result='QVariantList')
    def getBackgroundData(self) -> list:
        """Return background reference line data for the Experiment chart."""
        if not self._bkg_shown:
            return []
        return self._get_reference_line_data('background', -10.0, use_analysis_range=False)

    @Slot(result='QVariantList')
    def getScaleData(self) -> list:
        """Return scale reference line data for the Experiment chart."""
        if not self._scale_shown:
            return []
        return self._get_reference_line_data('scale', 0.0, use_analysis_range=False)

    @Slot(result='QVariantList')
    def getBackgroundDataForAnalysis(self) -> list:
        """Return background reference line data for the Analysis chart (sample x-range)."""
        if not self._bkg_shown:
            return []
        return self._get_reference_line_data('background', -10.0, use_analysis_range=True)

    @Slot(result='QVariantList')
    def getScaleDataForAnalysis(self) -> list:
        """Return scale reference line data for the Analysis chart (sample x-range)."""
        if not self._scale_shown:
            return []
        return self._get_reference_line_data('scale', 0.0, use_analysis_range=True)

    @property
    def sample_data(self) -> DataSet1D:
        idx = self._project_lib.current_model_index
        if idx in self._sample_data and self._sample_data[idx] is not None:
            return self._sample_data[idx]
        try:
            data = self._project_lib.sample_data_for_model_at_index(idx)
        except IndexError:
            data = DataSet1D(
                name='Sample Data empty',
                x=np.empty(0),
                y=np.empty(0),
            )
        self._sample_data[idx] = data
        return data

    @property
    def model_data(self) -> DataSet1D:
        idx = self._project_lib.current_model_index
        if idx in self._model_data and self._model_data[idx] is not None:
            return self._model_data[idx]
        try:
            data = self._project_lib.model_data_for_model_at_index(idx)
        except IndexError:
            data = DataSet1D(
                name='Model Data empty',
                x=np.empty(0),
                y=np.empty(0),
            )
        self._model_data[idx] = data
        return data

    @property
    def sld_data(self) -> DataSet1D:
        idx = self._project_lib.current_model_index
        if idx in self._sld_data and self._sld_data[idx] is not None:
            return self._sld_data[idx]
        try:
            data = self._project_lib.sld_data_for_model_at_index(idx)
        except IndexError:
            data = DataSet1D(
                name='SLD Data empty',
                x=np.empty(0),
                y=np.empty(0),
            )
        self._sld_data[idx] = data
        return data

    @property
    def experiment_data(self) -> DataSet1D:
        try:
            # Check if multi-experiment selection is enabled
            if hasattr(self._proxy, '_analysis') and hasattr(self._proxy._analysis, '_selected_experiment_indices'):
                selected_indices = self._proxy._analysis._selected_experiment_indices
                if len(selected_indices) > 1:
                    # Return concatenated data for multiple experiments (legacy support)
                    return self._proxy._analysis.get_concatenated_experiment_data()
            # Default single experiment behavior. Polarized experiments are
            # flattened to the first visible channel here; the experiment page
            # uses the channel-aware slots for full per-channel display.
            current_index = self._project_lib.current_experiment_index
            data = flatten_polarized(
                self._project_lib.experimental_data_for_model_at_index(current_index), self._visible_channels
            )
        except IndexError:
            data = DataSet1D(
                name='Experiment Data empty',
                x=np.empty(0),
                y=np.empty(0),
                ye=np.empty(0),
                xe=np.empty(0),
            )
        return data

    @property
    def is_multi_experiment_mode(self) -> bool:
        """Check if multiple experiments are selected."""
        try:
            if hasattr(self._proxy, '_analysis') and hasattr(self._proxy._analysis, '_selected_experiment_indices'):
                return len(self._proxy._analysis._selected_experiment_indices) > 1
        except Exception:  # noqa: S110
            pass
        return False

    @property
    def individual_experiment_data_list(self) -> list:
        """Get individual experiment data for multi-experiment plotting."""
        return self._individual_experiment_data_list(expand_channels=False)

    @property
    def individual_experiment_channel_data_list(self) -> list:
        """Like `individual_experiment_data_list`, one entry per visible spin channel."""
        return self._individual_experiment_data_list(expand_channels=True)

    def _individual_experiment_data_list(self, expand_channels: bool) -> list:
        try:
            if hasattr(self._proxy, '_analysis'):
                return self._proxy._analysis.get_individual_experiment_data_list(expand_channels=expand_channels)
        except Exception as e:
            console.debug(f'Error getting individual experiment data: {e}')
        return []

    # Sample
    @Property(float, notify=sampleChartRangesChanged)
    def sampleMaxX(self):
        return self._get_all_models_sample_range()[1]

    @Property(float, notify=sampleChartRangesChanged)
    def sampleMinX(self):
        return self._get_all_models_sample_range()[0]

    @Property(float, notify=sampleChartRangesChanged)
    def sampleMaxY(self):
        return self._get_all_models_sample_range()[3]

    @Property(float, notify=sampleChartRangesChanged)
    def sampleMinY(self):
        return self._get_all_models_sample_range()[2]

    def _get_all_models_sample_range(self):
        """Get combined X/Y ranges for all models' sample data."""
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        for idx in range(len(self._project_lib.models)):
            try:
                data = self._project_lib.sample_data_for_model_at_index(idx)
                if data.x.size > 0:
                    min_x = min(min_x, data.x.min())
                    max_x = max(max_x, data.x.max())
                if data.y.size > 0:
                    valid_mask = data.y > 0
                    valid_y = data.y[valid_mask]
                    if valid_y.size > 0:
                        valid_y = self._apply_rq4(data.x[valid_mask], valid_y)
                        min_y = min(min_y, np.log10(valid_y.min()))
                        max_y = max(max_y, np.log10(valid_y.max()))
            except (IndexError, ValueError):
                continue

        # Fallback to current model if no valid data found
        if min_x == float('inf'):
            min_x = self.sample_data.x.min() if self.sample_data.x.size > 0 else 0.0
        if max_x == float('-inf'):
            max_x = self.sample_data.x.max() if self.sample_data.x.size > 0 else 1.0
        if min_y == float('inf'):
            valid_y = self.sample_data.y[self.sample_data.y > 0] if self.sample_data.y.size > 0 else np.array([])
            min_y = np.log10(valid_y.min()) if valid_y.size > 0 else -10.0
        if max_y == float('-inf'):
            valid_y = self.sample_data.y[self.sample_data.y > 0] if self.sample_data.y.size > 0 else np.array([])
            max_y = np.log10(valid_y.max()) if valid_y.size > 0 else 0.0

        return (min_x, max_x, min_y, max_y)

    # SLD
    @Property(float, notify=sldChartRangesChanged)
    def sldMaxX(self):
        return self._get_all_models_sld_range()[1]

    @Property(float, notify=sldChartRangesChanged)
    def sldMinX(self):
        return self._get_all_models_sld_range()[0]

    @Property(float, notify=sldChartRangesChanged)
    def sldMaxY(self):
        return self._get_all_models_sld_range()[3]

    @Property(float, notify=sldChartRangesChanged)
    def sldMinY(self):
        return self._get_all_models_sld_range()[2]

    def _get_all_models_theta_range(self) -> tuple:
        """(min, max) of theta_m over the magnetic models, for its own axis."""
        values = []
        for idx in range(len(self._project_lib.models)):
            profile = self._magnetic_sld_profiles(idx).get('theta_m')
            if profile is not None and profile.y.size > 0:
                values.extend([float(profile.y.min()), float(profile.y.max())])
        if not values:
            return (0.0, 360.0)
        low, high = min(values), max(values)
        if high - low < 1e-6:
            # A single-valued angle (every layer at the same theta_m, the usual
            # case) would collapse the axis.
            return (max(0.0, low - 10.0), min(360.0, high + 10.0))
        return (low, high)

    @Property(float, notify=magneticProfileChanged)
    def sldThetaMinY(self) -> float:
        return self._get_all_models_theta_range()[0]

    @Property(float, notify=magneticProfileChanged)
    def sldThetaMaxY(self) -> float:
        return self._get_all_models_theta_range()[1]

    def _get_all_models_sld_range(self):
        """Get combined X/Y ranges for all models' SLD data."""
        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        for idx in range(len(self._project_lib.models)):
            try:
                datasets = [self._project_lib.sld_data_for_model_at_index(idx)]
                # The magnetic curves are drawn on the same axes and rho + rhoM
                # exceeds rho, so they must be part of the range or they end up
                # silently clipped. theta_m lives on its own right-hand axis.
                profiles = self._magnetic_sld_profiles(idx)
                datasets += [
                    profiles[curve]
                    for curve in self._visible_sld_curves
                    if curve in profiles and curve != 'theta_m'
                ]
                for data in datasets:
                    if data.x.size > 0:
                        min_x = min(min_x, data.x.min())
                        max_x = max(max_x, data.x.max())
                    if data.y.size > 0:
                        min_y = min(min_y, data.y.min())
                        max_y = max(max_y, data.y.max())
            except (IndexError, ValueError):
                continue

        # Fallback to current model if no valid data found
        if min_x == float('inf'):
            min_x = self.sld_data.x.min() if self.sld_data.x.size > 0 else 0.0
        if max_x == float('-inf'):
            max_x = self.sld_data.x.max() if self.sld_data.x.size > 0 else 1.0
        if min_y == float('inf'):
            min_y = self.sld_data.y.min() if self.sld_data.y.size > 0 else -1.0
        if max_y == float('-inf'):
            max_y = self.sld_data.y.max() if self.sld_data.y.size > 0 else 1.0

        return (min_x, max_x, min_y, max_y)

    # Experiment ranges
    def _experiment_range_datasets(self) -> list:
        """Datasets the experiment chart actually draws for the current selection.

        A polarized experiment shows one series per visible measured channel,
        and channel files need not share a q grid — so the axes must span all of
        them, not just the flattened first one. Multi-experiment selection keeps
        using the concatenated data.
        """
        try:
            if self.is_multi_experiment_mode:
                return [self.experiment_data]
            current_index = self._project_lib.current_experiment_index
            experiment = self._project_lib.experimental_data_for_model_at_index(current_index)
            channels = [
                channel for channel in experiment_channel_values(experiment) if channel in self._visible_channels
            ]
            if channels:
                return [experiment[channel] for channel in channels]
        except (IndexError, KeyError, AttributeError) as e:
            console.debug(f'Falling back to the flat experiment data for chart ranges: {e}')
        return [self.experiment_data]

    @Property(float, notify=experimentChartRangesChanged)
    def experimentMaxX(self):
        values = [data.x.max() for data in self._experiment_range_datasets() if data.x.size > 0]
        return max(values) if values else 1.0

    @Property(float, notify=experimentChartRangesChanged)
    def experimentMinX(self):
        values = [data.x.min() for data in self._experiment_range_datasets() if data.x.size > 0]
        return min(values) if values else 0.0

    @Property(float, notify=experimentChartRangesChanged)
    def experimentMaxY(self):
        values = []
        for data in self._experiment_range_datasets():
            if data.y.size == 0:
                continue
            y_values = self._apply_rq4(data.x, data.y)
            y_values = y_values[y_values > 0]
            if y_values.size > 0:
                values.append(np.log10(y_values.max()))
        return max(values) if values else 1.0

    @Property(float, notify=experimentChartRangesChanged)
    def experimentMinY(self):
        values = []
        for data in self._experiment_range_datasets():
            if data.y.size == 0:
                continue
            positive = data.y > 0
            valid_y = self._apply_rq4(data.x[positive], data.y[positive])
            # Filter again after transformation to avoid log of zero/negative
            valid_y = valid_y[valid_y > 0]
            if valid_y.size > 0:
                values.append(np.log10(valid_y.min()))
        return min(values) if values else -10.0

    # Residual ranges
    def _invalidate_residual_range_cache(self):
        """Clear the cached residual range so it is recomputed on next access."""
        self._residual_range_cache = None

    @staticmethod
    def _compute_residual(calculated: float, measured: float, sigma: float) -> float:
        """Compute residual value for a single data point.

        Uses a three-tier fallback: (calc−meas)/σ, then /meas,
        then plain difference when both are unavailable.
        """
        if sigma > 0.0:
            return (calculated - measured) / sigma
        if measured > 0.0:
            return (calculated - measured) / measured
        return calculated - measured

    def _get_residual_range(self) -> tuple:
        """Return (min_x, max_x, min_y, max_y) for the residual chart.

        X range matches the full analysis chart domain so residuals line up
        vertically with the reflectivity chart above, even when an experiment
        covers only part of the model q-range. Y range is computed from
        residual values across all currently selected experiments, with a
        10 % margin. Safe fallback values are returned when data is empty.

        The result is cached until invalidated by ``_invalidate_residual_range_cache``.
        """
        if self._residual_range_cache is not None:
            return self._residual_range_cache

        min_x, max_x = float('inf'), float('-inf')
        min_y, max_y = float('inf'), float('-inf')

        try:
            analysis_min_x, analysis_max_x = self._get_all_models_sample_range()[0:2]
            if analysis_min_x != float('inf') and analysis_max_x != float('-inf'):
                min_x = analysis_min_x
                max_x = analysis_max_x
        except Exception as e:
            console.debug(f'Error getting analysis x range for residuals: {e}')

        try:
            indices = []
            if self.is_multi_experiment_mode:
                indices = list(self._proxy._analysis._selected_experiment_indices)
            else:
                indices = [self._project_lib.current_experiment_index]

            for exp_idx in indices:
                try:
                    # A polarized experiment draws one residual curve per visible
                    # spin channel (see ResidualsView.qml); the range must cover
                    # every one of them, not just the flattened first channel.
                    experiment = self._project_lib.experimental_data_for_model_at_index(exp_idx)
                    channels = [
                        channel for channel in experiment_channel_values(experiment)
                        if channel in self._visible_channels
                    ]
                    for channel in channels or ['']:
                        aligned = self._get_aligned_analysis_values(exp_idx, channel)
                        for item in aligned:
                            if not item['has_calculated']:
                                # No cross-section to compare against: ResidualsView
                                # does not draw a point here either.
                                continue
                            q = item['q']
                            residual = self._compute_residual(
                                item['calculated'], item['measured'], item['sigma'])
                            if min_x == float('inf'):
                                min_x = q
                            else:
                                min_x = min(min_x, q)
                            if max_x == float('-inf'):
                                max_x = q
                            else:
                                max_x = max(max_x, q)
                            min_y = min(min_y, residual)
                            max_y = max(max_y, residual)
                except Exception as e:
                    console.debug(f'Residual range error for experiment {exp_idx}: {e}')
                    continue
        except Exception as e:
            console.debug(f'Error computing residual range: {e}')

        if min_x == float('inf'):
            result = (0.0, 1.0, -1.0, 1.0)
        else:
            y_margin = max(abs(min_y), abs(max_y)) * 0.10 or 0.1
            result = (min_x, max_x, min_y - y_margin, max_y + y_margin)

        self._residual_range_cache = result
        return result

    @Property(float, notify=sampleChartRangesChanged)
    def residualMinX(self) -> float:
        return self._get_residual_range()[0]

    @Property(float, notify=sampleChartRangesChanged)
    def residualMaxX(self) -> float:
        return self._get_residual_range()[1]

    @Property(float, notify=sampleChartRangesChanged)
    def residualMinY(self) -> float:
        return self._get_residual_range()[2]

    @Property(float, notify=sampleChartRangesChanged)
    def residualMaxY(self) -> float:
        return self._get_residual_range()[3]

    @Property('QVariant', notify=chartRefsChanged)
    def chartRefs(self):
        return self._chartRefs

    @Property(str)
    def calcSerieColor(self):
        return '#00FF00'
        # return self._calcSerieColor

    @Property(bool, notify=experimentDataChanged)
    def isMultiExperimentMode(self) -> bool:
        """Return whether multiple experiments are selected for plotting."""
        return self.is_multi_experiment_mode

    @Property('QVariantList', notify=experimentDataChanged)
    def individualExperimentDataList(self) -> list:
        """Return list of individual experiment data for multi-experiment plotting."""
        return self._qml_experiment_data_list(self.individual_experiment_data_list)

    @Property('QVariantList', notify=experimentChannelsChanged)
    def individualExperimentChannelDataList(self) -> list:
        """Multi-experiment list with polarized experiments split per visible channel.

        Used by the experiment and analysis charts, which draw one series per
        channel; each row's `channel` selects the matching per-channel points.
        """
        return self._qml_experiment_data_list(self.individual_experiment_channel_data_list)

    @Property(bool, notify=experimentChannelsChanged)
    def analysisUsesChannelSeries(self) -> bool:
        """Whether the analysis chart must draw one series per spin channel.

        True as soon as any selected experiment is polarized: its measured data
        and calculated curve exist per channel, so the single measured/
        calculated pair of the ordinary path cannot represent it.
        """
        try:
            selected = getattr(self._proxy._analysis, '_selected_experiment_indices', None) or []
            return any(self._project_lib.experiment_is_polarized_at_index(index) for index in selected)
        except Exception as exception:  # noqa: BLE001 - a chart flag must never raise into QML
            console.debug(f'Error resolving analysis channel mode: {exception}')
            return False

    @staticmethod
    def _qml_experiment_data_list(data_list: list) -> list:
        # Convert to QML-friendly format
        qml_data_list = []
        for exp_data in data_list:
            qml_data_list.append(
                {
                    'name': exp_data['name'],
                    'color': exp_data['color'],
                    'index': exp_data['index'],
                    # Spin channel of a polarized experiment ('' when unpolarized);
                    # QML fetches the matching per-channel points with it.
                    'channel': exp_data.get('channel', ''),
                    'hasData': exp_data['data'].x.size > 0,
                }
            )
        return qml_data_list

    @Slot(str, str, 'QVariant')
    def setQtChartsSerieRef(self, page: str, serie: str, ref: QObject):
        self._chartRefs['QtCharts'][page][serie] = ref
        console.debug(IO.formatMsg('sub', f'{serie} on {page}: {ref}'))

    @Slot(int, result='QVariantList')
    def getSampleDataPointsForModel(self, model_index: int) -> list:
        """Get sample data points for a specific model for plotting."""
        try:
            data = self._project_lib.sample_data_for_model_at_index(model_index)
            points = []
            for point in data.data_points():
                x_val = float(point[0])
                y_val = float(point[1])
                if y_val > 0:
                    y_val = self._apply_rq4(x_val, y_val)
                y_log = float(np.log10(y_val)) if y_val > 0 else -10.0
                points.append({'x': x_val, 'y': y_log})
            return points
        except Exception as e:
            console.debug(f'Error getting sample data points for model {model_index}: {e}')
            return []

    @Slot(int, result='QVariantList')
    def getSldDataPointsForModel(self, model_index: int) -> list:
        """Get SLD data points for a specific model for plotting."""
        try:
            data = self._project_lib.sld_data_for_model_at_index(model_index)
            points = []
            for point in data.data_points():
                points.append({'x': float(point[0]), 'y': float(point[1])})
            return points
        except Exception as e:
            console.debug(f'Error getting SLD data points for model {model_index}: {e}')
            return []

    # One-call fills for QML-owned series: a JS append() loop crosses the
    # QML/C++ boundary and re-signals per point; replaceNp() repaints once.
    @Slot('QVariant', int)
    def fillSampleSeriesForModel(self, series, model_index: int) -> None:
        """Fill a QML-owned series with a model's reflectivity in one call."""
        if series is None:
            return
        points = self.getSampleDataPointsForModel(model_index)
        self._replace_series_points(series, ((point['x'], point['y']) for point in points))

    @Slot('QVariant', int)
    def fillSldSeriesForModel(self, series, model_index: int) -> None:
        """Fill a QML-owned series with a model's nuclear SLD profile in one call."""
        if series is None:
            return
        points = self.getSldDataPointsForModel(model_index)
        self._replace_series_points(series, ((point['x'], point['y']) for point in points))

    @Slot('QVariant', int, str, int)
    def fillMagneticSldSegmentSeries(self, series, model_index: int, curve: str, segment: int) -> None:
        """Fill a QML-owned series with one piece of a magnetic curve in one call."""
        if series is None:
            return
        points = self.getMagneticSldSegment(model_index, curve, segment)
        self._replace_series_points(series, ((point['x'], point['y']) for point in points))

    # Magnetic depth profiles (Phase 5a)
    MAGNETIC_SLD_CURVES = ('spin_up', 'spin_down', 'rho_m', 'theta_m')

    def _magnetic_sld_profiles(self, model_index: int) -> dict:
        """Magnetic profiles of one model, or {} when it has none.

        A non-magnetic model, a calculator without magnetism, or a model index
        that no longer exists are all "nothing to draw" — the chart simply keeps
        the nuclear curve it draws today.

        Cached per model: one chart refresh reads the curves and four range
        properties, and each miss is a full refl1d profile evaluation. The cache
        is dropped with the other plot data and on every magnetic notification,
        so a parameter change is picked up immediately.
        """
        cache = getattr(self, '_magnetic_profile_cache', None)
        if cache is None:
            cache = self._magnetic_profile_cache = {}
        if model_index in cache:
            return cache[model_index]

        try:
            has_magnetism = bool(self._project_lib.model_has_magnetism_at_index(model_index))
        except AttributeError:
            has_magnetism = False
        if not has_magnetism:
            profiles = {}
        else:
            try:
                profiles = self._project_lib.magnetic_sld_data_for_model_at_index(model_index)
                self._magnetic_profile_error = ''
            except (IndexError, KeyError, ValueError, NotImplementedError, AttributeError) as e:
                # A magnetic model without curves is a real problem, and the GUI
                # user cannot read this log — record it for the sidebar too.
                console.error(f'No magnetic SLD profile for model {model_index}: {e}')
                self._magnetic_profile_error = str(e)
                profiles = {}
        cache[model_index] = profiles
        return profiles

    @Slot(int, result=bool)
    def modelHasMagnetism(self, model_index: int) -> bool:
        """Whether a model carries magnetism (drives the magnetic curves and controls)."""
        try:
            return bool(self._project_lib.model_has_magnetism_at_index(model_index))
        except AttributeError:
            return False

    @Property(bool, notify=magneticProfileChanged)
    def anyModelHasMagnetism(self) -> bool:
        """Whether any model is magnetic — the capability gate for the magnetic UI."""
        try:
            return any(self.modelHasMagnetism(index) for index in range(len(self._project_lib.models)))
        except (TypeError, AttributeError):
            return False

    @Slot(int, str, result='QVariantList')
    def getMagneticSldDataPointsForModel(self, model_index: int, curve: str) -> list:
        """Points of one magnetic profile curve of a model, [] when not applicable.

        `curve` is one of 'spin_up', 'spin_down', 'rho_m', 'theta_m'.
        """
        if curve not in self.MAGNETIC_SLD_CURVES:
            console.error(f'Unknown magnetic SLD curve {curve!r}.')
            return []
        profiles = self._magnetic_sld_profiles(model_index)
        data = profiles.get(curve)
        if data is None:
            return []
        return [{'x': float(x), 'y': float(y)} for x, y in zip(data.x, data.y)]

    def _magnetic_sld_segments(self, model_index: int, curve: str) -> list:
        """One point list per contiguous piece of a magnetic curve.

        `theta_m` exists only where there is a moment, so a sample with two
        magnetic layers separated by a spacer produces two pieces. Drawing them
        as one series would connect the ends with a line across the spacer,
        implying a moment rotation where there is no moment at all.
        """
        if curve not in self.MAGNETIC_SLD_CURVES:
            console.error(f'Unknown magnetic SLD curve {curve!r}.')
            return []
        data = self._magnetic_sld_profiles(model_index).get(curve)
        if data is None or data.x.size == 0:
            return []

        x = np.asarray(data.x, dtype=float)
        y = np.asarray(data.y, dtype=float)
        # The profile is on a uniform z grid; a gap is a step much larger than
        # the usual one.
        steps = np.diff(x)
        breaks = np.flatnonzero(steps > 2.0 * np.median(steps)) + 1 if steps.size else np.array([], dtype=int)
        return [
            [{'x': float(px), 'y': float(py)} for px, py in zip(piece_x, piece_y)]
            for piece_x, piece_y in zip(np.split(x, breaks), np.split(y, breaks))
            if piece_x.size > 0
        ]

    @Slot(int, str, result='QVariantList')
    def getMagneticSldSegmentsForModel(self, model_index: int, curve: str) -> list:
        """The pieces of one magnetic curve, as lists of points."""
        return self._magnetic_sld_segments(model_index, curve)

    @Slot(int, str, int, result='QVariantList')
    def getMagneticSldSegment(self, model_index: int, curve: str, segment: int) -> list:
        """Points of one piece of a magnetic curve ([] when it does not exist)."""
        segments = self._magnetic_sld_segments(model_index, curve)
        if 0 <= segment < len(segments):
            return segments[segment]
        return []

    @Property('QVariantList', notify=magneticProfileChanged)
    def visibleSldCurves(self) -> list:
        """Magnetic profile curves the user asked to see."""
        return [curve for curve in self.MAGNETIC_SLD_CURVES if curve in self._visible_sld_curves]

    @Property(str, notify=magneticProfileChanged)
    def magneticProfileError(self) -> str:
        """Why a magnetic model has no curves ('' when everything computed)."""
        return self._magnetic_profile_error

    @Slot(str, result=bool)
    def sldCurveVisible(self, curve: str) -> bool:
        """Whether one magnetic profile curve is shown."""
        return curve in self._visible_sld_curves

    @Slot(str, bool)
    def setSldCurveVisible(self, curve: str, visible: bool) -> None:
        """Show or hide one magnetic profile curve on both SLD tabs.

        The spin-up and spin-down potentials are a pair: they are only
        meaningful together, so one checkbox toggles both.
        """
        curves = {'spin_up', 'spin_down'} if curve in ('spin_up', 'spin_down') else {curve}
        unknown = curves - set(self.MAGNETIC_SLD_CURVES)
        if unknown:
            console.error(f'Unknown magnetic SLD curve(s) {sorted(unknown)}.')
            return

        visible_curves = set(self._visible_sld_curves)
        visible_curves |= curves if visible else set()
        visible_curves -= set() if visible else curves
        if visible_curves != set(self._visible_sld_curves):
            self._visible_sld_curves = frozenset(visible_curves)
            self.magneticProfileChanged.emit()
            self.sldChartRangesChanged.emit()

    # Spin asymmetry (Phase 5b/5c)
    def _spin_asymmetry(self, experiment_index: int = None) -> dict:
        """SA of an experiment as ``{measured, calculated, masked_points}``, or {}.

        Empty when the experiment has no pp/mm pair — the charts are hidden in
        that case, so this is "nothing to draw", not an error.
        """
        if experiment_index is None:
            experiment_index = self._project_lib.current_experiment_index
        cached = getattr(self, '_spin_asymmetry_cache', None)
        if cached is None:
            cached = self._spin_asymmetry_cache = {}
        if experiment_index in cached:
            return cached[experiment_index]

        try:
            result = self._project_lib.spin_asymmetry_for_experiment_at_index(experiment_index)
        except (IndexError, KeyError, ValueError) as e:
            console.debug(f'No spin asymmetry for experiment {experiment_index}: {e}')
            result = {}
        except Exception as e:
            console.error(f'Failed to compute the spin asymmetry of experiment {experiment_index}: {e!r}')
            result = {}
        cached[experiment_index] = result
        return result

    @Property(bool, notify=spinAsymmetryChanged)
    def spinAsymmetryAvailable(self) -> bool:
        """Whether the current experiment measured both pp and mm, so SA exists."""
        try:
            return bool(
                self._project_lib.experiment_supports_spin_asymmetry_at_index(
                    self._project_lib.current_experiment_index
                )
            )
        except (IndexError, KeyError, AttributeError):
            return False

    @Property(bool, notify=spinAsymmetryChanged)
    def spinAsymmetryCalculatedAvailable(self) -> bool:
        """Whether a model SA curve can be drawn (needs a magnetic model)."""
        return self._spin_asymmetry().get('calculated') is not None

    @Property(int, notify=spinAsymmetryChanged)
    def spinAsymmetryMaskedPoints(self) -> int:
        """Measured points dropped because SA was noise over noise there."""
        return int(self._spin_asymmetry().get('masked_points', 0))

    @Property(int, notify=spinAsymmetryChanged)
    def spinAsymmetryOutOfOverlapPoints(self) -> int:
        """Measured points dropped because the two channels do not cover the same q."""
        return int(self._spin_asymmetry().get('out_of_overlap_points', 0))

    @Slot(int, result='QVariantList')
    def getSpinAsymmetryPoints(self, experiment_index: int) -> list:
        """Measured SA points with error bounds, ready for QML series."""
        data = self._spin_asymmetry(experiment_index).get('measured')
        if data is None or data.x.size == 0:
            return []
        # ye holds variances; the chart needs one standard deviation.
        sigma = np.sqrt(np.clip(np.asarray(data.ye, dtype=float), 0.0, None))
        if sigma.size != data.y.size:
            sigma = np.zeros_like(data.y)
        return [
            {
                'x': float(x),
                'y': float(y),
                'errorUpper': float(y + error),
                'errorLower': float(y - error),
            }
            for x, y, error in zip(data.x, data.y, sigma)
        ]

    @Slot(int, result='QVariantList')
    def getSpinAsymmetryCalculatedPoints(self, experiment_index: int) -> list:
        """Model SA points, [] when the model is not magnetic."""
        data = self._spin_asymmetry(experiment_index).get('calculated')
        if data is None or data.x.size == 0:
            return []
        return [{'x': float(x), 'y': float(y)} for x, y in zip(data.x, data.y)]

    def _spin_asymmetry_range(self) -> tuple:
        """(min_x, max_x, min_y, max_y) over the drawn SA curves."""
        result = self._spin_asymmetry()
        measured = result.get('measured')
        if measured is None or measured.x.size == 0:
            return (0.0, 1.0, -1.0, 1.0)
        sigma = np.sqrt(np.clip(np.asarray(measured.ye, dtype=float), 0.0, None))
        if sigma.size != measured.y.size:
            sigma = np.zeros_like(measured.y)
        min_y = float(np.min(measured.y - sigma))
        max_y = float(np.max(measured.y + sigma))
        calculated = result.get('calculated')
        if calculated is not None and calculated.y.size > 0:
            min_y = min(min_y, float(np.min(calculated.y)))
            max_y = max(max_y, float(np.max(calculated.y)))
        # SA lies in [-1, 1] only while both reflectivities are positive, which
        # background-subtracted data need not be. Start from that window so a
        # normal dataset always gets the same, comparable axis, but expand it
        # rather than drawing retained points off-canvas.
        return (
            float(np.min(measured.x)),
            float(np.max(measured.x)),
            min(-1.05, min_y),
            max(1.05, max_y),
        )

    @Property(float, notify=spinAsymmetryChanged)
    def spinAsymmetryMinX(self) -> float:
        return self._spin_asymmetry_range()[0]

    @Property(float, notify=spinAsymmetryChanged)
    def spinAsymmetryMaxX(self) -> float:
        return self._spin_asymmetry_range()[1]

    @Property(float, notify=spinAsymmetryChanged)
    def spinAsymmetryMinY(self) -> float:
        return self._spin_asymmetry_range()[2]

    @Property(float, notify=spinAsymmetryChanged)
    def spinAsymmetryMaxY(self) -> float:
        return self._spin_asymmetry_range()[3]

    @Slot()
    def notifySpinAsymmetryChanged(self) -> None:
        """Recompute the spin asymmetry and tell QML.

        Connected to everything that changes the data or the model: the SA
        depends on both the measured channels and (for the model curve) every
        fitted parameter.
        """
        self._spin_asymmetry_cache = {}
        self.spinAsymmetryChanged.emit()

    @Slot()
    def notifyMagneticProfileChanged(self) -> None:
        """Recompute the magnetic profiles and tell QML.

        Connected to the sample/parameter change relays: making a layer magnetic
        (or removing its magnetism) adds or removes curves and changes the SLD
        y-range, and moving rho_m/theta_m changes the curves themselves.
        """
        self._magnetic_profile_cache = {}
        self.magneticProfileChanged.emit()
        self.sldChartRangesChanged.emit()

    @Slot(int, result=str)
    def getModelColor(self, model_index: int) -> str:
        """Get the color for a specific model."""
        try:
            return str(self._project_lib.models[model_index].color)
        except (IndexError, AttributeError):
            return '#000000'

    @Property(int, notify=sampleChartRangesChanged)
    def modelCount(self) -> int:
        """Return the number of models."""
        return len(self._project_lib.models)

    def _measured_points_from_dataset(self, data) -> list:
        """Log-space measured points with error bands from one flat dataset."""
        points = []
        for point in data.data_points():
            q = point[0]
            r = point[1]
            if r <= 0:
                continue
            error_var = point[2]
            error_lower_linear = max(r - np.sqrt(error_var), 1e-10)
            r_val = self._apply_rq4(q, r)
            error_upper = self._apply_rq4(q, r + np.sqrt(error_var))
            error_lower = self._apply_rq4(q, error_lower_linear)
            points.append(
                {
                    'x': float(q),
                    'y': float(np.log10(r_val)),
                    'errorUpper': float(np.log10(error_upper)),
                    'errorLower': float(np.log10(error_lower)),
                }
            )
        return points

    @Slot(int, result='QVariantList')
    def getExperimentDataPoints(self, experiment_index: int) -> list:
        """Get data points for a specific experiment for plotting.

        For a polarized experiment this returns the first visible channel;
        per-channel series use `getExperimentChannelDataPoints` instead.
        """
        try:
            data = flatten_polarized(
                self._project_lib.experimental_data_for_model_at_index(experiment_index), self._visible_channels
            )
        except (IndexError, KeyError) as e:
            # Expected: no experiment loaded at this index.
            console.debug(f'No experiment data for index {experiment_index}: {e}')
            return []
        except Exception as e:
            # Anything else is a defect or an incompatible library, not "no data".
            console.error(f'Failed to read experiment {experiment_index}: {e!r}')
            return []
        return self._measured_points_from_dataset(data)

    @Slot(int, str, result='QVariantList')
    def getExperimentChannelDataPoints(self, experiment_index: int, channel: str) -> list:
        """Get data points of one spin channel of a polarized experiment."""
        try:
            self._require_channel_api()
            data = self._project_lib.experimental_data_for_model_at_index(experiment_index, channel=channel)
        except (IndexError, KeyError) as e:
            # Expected: no experiment at this index, or the channel was not measured.
            console.debug(f'No {channel} channel data for index {experiment_index}: {e}')
            return []
        except Exception as e:
            # A TypeError here means the library predates the channel argument;
            # silently returning [] would draw an empty chart instead.
            console.error(f'Failed to read {channel} channel of experiment {experiment_index}: {e!r}')
            return []
        return self._measured_points_from_dataset(data)

    def _require_channel_api(self) -> None:
        """Fail loudly when the installed library has no per-channel experiment API.

        The app and `easyreflectometry` must ship the same polarized API; an
        older library would otherwise turn every polarized chart into an empty
        one with no visible cause. Both halves are checked: the polarization
        predicate and the accessor's `channel` argument.
        """
        if self._channel_api_error is None:
            self._channel_api_error = self._check_channel_api()
        if self._channel_api_error:
            raise RuntimeError(self._channel_api_error)

    def _check_channel_api(self) -> str:
        """Return an error message when the library lacks the channel API, '' otherwise."""
        missing = 'The installed easyreflectometry library does not provide the per-channel experiment API'
        advice = (
            'Polarized data cannot be displayed; please install a library version that '
            'supports polarized experiments.'
        )
        if not hasattr(self._project_lib, 'experiment_is_polarized_at_index'):
            return f'{missing} (experiment_is_polarized_at_index is missing). {advice}'
        accessor = getattr(self._project_lib, 'experimental_data_for_model_at_index', None)
        try:
            parameters = inspect.signature(accessor).parameters
        except (TypeError, ValueError):  # builtins/C callables: assume it is fine
            return ''
        accepts_channel = 'channel' in parameters or any(
            parameter.kind is inspect.Parameter.VAR_KEYWORD for parameter in parameters.values()
        )
        if not accepts_channel:
            return f'{missing} (experimental_data_for_model_at_index has no channel argument). {advice}'
        return ''

    @Slot(int, result='QVariantList')
    def getExperimentChannels(self, experiment_index: int) -> list:
        """Measured channels of an experiment as ``{channel, label, color, visible}`` rows.

        Empty for unpolarized experiments.
        """
        return [
            {
                'channel': channel,
                'label': CHANNEL_LABELS[channel],
                'color': CHANNEL_COLORS[channel],
                'visible': channel in self._visible_channels,
            }
            for channel in self._measured_channels(experiment_index)
        ]

    def _measured_channels(self, experiment_index: int = None) -> list:
        """Measured channel values of an experiment ([] when unpolarized or missing)."""
        if experiment_index is None:
            experiment_index = self._project_lib.current_experiment_index
        try:
            experiment = self._project_lib.experimental_data_for_model_at_index(experiment_index)
        except (IndexError, KeyError):
            return []
        return experiment_channel_values(experiment)

    @Property(bool, notify=experimentChannelsChanged)
    def currentExperimentIsPolarized(self) -> bool:
        """Whether the current experiment carries per-channel (polarized) data."""
        return bool(self._measured_channels())

    @Property('QVariantList', notify=experimentChannelsChanged)
    def experimentChannelList(self) -> list:
        """Channel rows of the current experiment for the channel selector UI."""
        return self.getExperimentChannels(self._project_lib.current_experiment_index)

    @Slot()
    def notifyExperimentChannelsChanged(self) -> None:
        """Tell QML the current experiment (and so its channel state) changed.

        Connected to every path that can change the current experiment —
        selection, load, removal, project open — so `currentExperimentIsPolarized`
        and `experimentChannelList` never keep a previous experiment's value.
        The visible-channel set is renormalized first, so a selection made on a
        previous experiment cannot leave the new one with nothing to draw.
        """
        if self._renormalize_visible_channels():
            self.channelSelectionChanged.emit()
        self.experimentChannelsChanged.emit()

    def _renormalize_visible_channels(self) -> bool:
        """Keep at least one measured channel of the current experiment visible.

        The selection is global (one selector for the whole app), so hiding
        channels on one experiment can leave another experiment with none of its
        measured channels selected — an empty chart the user cannot fix, because
        the last-visible guard only runs while *hiding*. When that happens, all
        measured channels of the new current experiment are switched back on.

        Returns True when the visible set changed.
        """
        measured = self._measured_channels()
        if not measured or any(channel in self._visible_channels for channel in measured):
            return False
        self._visible_channels = self._visible_channels | frozenset(measured)
        console.debug(f'No visible channel for the current experiment; showing {", ".join(measured)} again.')
        return True

    @Slot(str, bool)
    def setChannelVisible(self, channel: str, visible: bool) -> None:
        """Show or hide one spin channel on the experiment/analysis charts.

        At least one *measured* channel of the current experiment always stays
        visible: a two-channel pp/mm experiment must not be blanked by hiding
        pp and mm just because unmeasured pm/mp are still in the global set.
        """
        visible_channels = set(self._visible_channels)
        if visible:
            visible_channels.add(channel)
        else:
            measured = self._measured_channels()
            if measured:
                still_visible = [name for name in measured if name in visible_channels and name != channel]
                if not still_visible:
                    console.debug(f'Refusing to hide {channel}: it is the last visible measured channel.')
                    # The checkbox has already toggled itself; re-publish the
                    # channel rows so it rebinds to the unchanged state.
                    self.experimentChannelsChanged.emit()
                    return
            elif len(visible_channels) <= 1:
                # Unpolarized/no experiment: keep the old global invariant.
                self.experimentChannelsChanged.emit()
                return
            visible_channels.discard(channel)

        if visible_channels != set(self._visible_channels):
            self._visible_channels = frozenset(visible_channels)
            self.channelSelectionChanged.emit()
            self.experimentChannelsChanged.emit()
            self.experimentDataChanged.emit()

    def _get_experiment_model_index(self, experiment_index: int, exp_data=None) -> int:
        """Resolve the model index used by a given experiment."""
        if exp_data is not None and hasattr(exp_data, 'model') and exp_data.model is not None:
            for idx, model in enumerate(self._project_lib.models):
                if model is exp_data.model:
                    return idx
        if experiment_index < len(self._project_lib.models):
            return experiment_index
        return 0

    def _get_aligned_analysis_values(self, experiment_index: int, channel: str = '') -> list[dict]:
        """Return measured, calculated and sigma values aligned on experiment q points.

        With `channel`, both the measured points and the calculated curve come
        from that spin channel — the calculated curve must be the channel's own
        cross-section, not the channel-agnostic one. Without it a polarized
        experiment falls back to its first visible channel.
        """
        experiment = self._project_lib.experimental_data_for_model_at_index(experiment_index)
        if channel:
            exp_data = experiment[channel]
        else:
            exp_data = flatten_polarized(experiment, self._visible_channels)
        q_values = np.asarray(getattr(exp_data, 'x', np.empty(0)), dtype=float)
        measured_values = np.asarray(getattr(exp_data, 'y', np.empty(0)), dtype=float)
        sigma_values = np.asarray(getattr(exp_data, 'ye', np.zeros_like(measured_values)), dtype=float)

        if q_values.size == 0 or measured_values.size == 0:
            return []

        q_mask = (q_values >= self._project_lib.q_min) & (q_values <= self._project_lib.q_max)
        q_filtered = q_values[q_mask]
        measured_filtered = measured_values[q_mask]
        variance_filtered = sigma_values[q_mask] if sigma_values.size else np.zeros_like(measured_filtered)
        # ye holds variances (sigma**2), same convention as prepare_threaded_fit
        # and getSpinAsymmetryPoints; convert to one standard deviation here so
        # every consumer of 'sigma' (residuals, report error bars) agrees.
        sigma_filtered = np.sqrt(np.clip(variance_filtered, 0.0, None))

        model_index = self._get_experiment_model_index(experiment_index, exp_data)
        if channel:
            # A channel curve must be that channel's own cross-section: if it
            # cannot be computed (e.g. spin-flip on a non-magnetic model), show
            # the measured points alone rather than another channel's curve.
            try:
                calc_data = self._project_lib.model_data_for_model_at_index(model_index, q_filtered, channel=channel)
            except Exception as exception:  # noqa: BLE001 - any backend refusal means "no curve"
                console.debug(f'No calculated curve for channel {channel}: {exception}')
                calc_data = None
        else:
            try:
                calc_data = self._project_lib.model_data_for_model_at_index(model_index, q_filtered)
            except TypeError:
                calc_data = self._project_lib.model_data_for_model_at_index(model_index)

        calc_values = np.asarray(getattr(calc_data, 'y', np.empty(0)), dtype=float)
        calc_q_values = np.asarray(getattr(calc_data, 'x', np.empty(0)), dtype=float)
        has_calculated = calc_values.size > 0

        if calc_values.size == q_filtered.size:
            calculated_filtered = calc_values
        elif calc_values.size == 0:
            calculated_filtered = measured_filtered.copy()
        elif calc_q_values.size == calc_values.size and calc_values.size > 1:
            calculated_filtered = np.interp(q_filtered, calc_q_values, calc_values)
        elif calc_values.size == 1:
            calculated_filtered = np.full_like(measured_filtered, calc_values[0], dtype=float)
        else:
            calculated_filtered = np.resize(calc_values, q_filtered.size)

        measured_filtered = self._apply_rq4(q_filtered, measured_filtered)
        calculated_filtered = self._apply_rq4(q_filtered, calculated_filtered)
        sigma_filtered = self._apply_rq4(q_filtered, sigma_filtered)

        points = []
        for q_value, measured_value, calculated_value, sigma_value in zip(
            q_filtered,
            measured_filtered,
            calculated_filtered,
            sigma_filtered,
        ):
            points.append(
                {
                    'q': float(q_value),
                    'measured': float(measured_value),
                    'calculated': float(calculated_value),
                    'sigma': float(sigma_value),
                    # False when there is no cross-section to show (see above);
                    # 'calculated' then mirrors 'measured' and must not be drawn.
                    'has_calculated': has_calculated,
                }
            )
        return points

    @Slot(int, result='QVariantList')
    @Slot(int, str, result='QVariantList')
    def getAnalysisDataPoints(self, experiment_index: int, channel: str = '') -> list:
        """Get measured and calculated data points for a specific experiment for analysis plotting.

        `channel` selects one spin channel of a polarized experiment; both the
        measured points and the calculated curve are then that channel's.
        """
        try:
            points = []
            for point in self._get_aligned_analysis_values(experiment_index, channel):
                measured = point['measured']
                calculated = point['calculated']
                points.append(
                    {
                        'x': point['q'],
                        'measured': float(np.log10(measured)) if measured > 0 else -10.0,
                        'calculated': float(np.log10(calculated)) if calculated > 0 else -10.0,
                        'hasCalculated': bool(point['has_calculated']),
                    }
                )
            return points
        except Exception as e:
            console.debug(f'Error getting analysis data points for index {experiment_index}: {e}')
            return []

    @Slot(int, result='QVariantList')
    @Slot(int, str, result='QVariantList')
    def getResidualDataPoints(self, experiment_index: int, channel: str = '') -> list:
        """Get residual data points for a specific experiment (optionally one spin channel)."""
        try:
            points = []
            for point in self._get_aligned_analysis_values(experiment_index, channel):
                if not point['has_calculated']:
                    # No cross-section: a residual of zero would look like a
                    # perfect fit, so report nothing at all.
                    continue
                residual = self._compute_residual(
                    point['calculated'], point['measured'], point['sigma'])
                points.append({'x': point['q'], 'y': float(residual)})
            return points
        except Exception as e:
            console.debug(f'Error getting residual data points for index {experiment_index}: {e}')
            return []

    def refreshSamplePage(self):
        # Clear cached data so it gets recalculated
        self._sample_data = {}
        self._model_data = {}
        self._sld_data = {}
        # Emit signals to update ranges and trigger QML refresh
        self.sampleChartRangesChanged.emit()
        self.sldChartRangesChanged.emit()
        self.samplePageDataChanged.emit()

    def refreshExperimentPage(self):
        self.drawMeasuredOnExperimentChart()

    def refreshAnalysisPage(self):
        self._model_data = {}
        self._invalidate_residual_range_cache()
        self.drawCalculatedAndMeasuredOnAnalysisChart()
        self.sampleChartRangesChanged.emit()

    def refreshExperimentRanges(self):
        """Emit signal to update experiment chart ranges when selection changes."""
        self.experimentChartRangesChanged.emit()

    @Slot()
    def drawCalculatedOnSampleChart(self):
        if PLOT_BACKEND == 'QtCharts':
            self.qtchartsReplaceCalculatedOnSampleChartAndRedraw()

    @staticmethod
    def _replace_series_points(series, points) -> int:
        """Replace a QtCharts series' content in one call.

        One ``replaceNp()`` re-signals and repaints once; per-point
        ``append()`` crosses the QML/C++ boundary and re-signals for every
        single point. (The ``replace(QList<QPointF>)`` overload is not
        exposed by PySide6 — only the numpy variants are.)
        """
        pts = list(points)
        if not pts:
            series.clear()
            return 0
        x = np.fromiter((point[0] for point in pts), dtype=np.float64, count=len(pts))
        y = np.fromiter((point[1] for point in pts), dtype=np.float64, count=len(pts))
        series.replaceNp(x, y)
        return len(pts)

    def qtchartsReplaceCalculatedOnSampleChartAndRedraw(self):
        if not self._clear_qtcharts_series('samplePage', 'sampleSerie'):
            return
        series = self._qtcharts_series_ref('samplePage', 'sampleSerie')
        nr_points = self._replace_series_points(
            series, ((point[0], np.log10(point[1])) for point in self.sample_data.data_points() if point[1] > 0)
        )
        console.debug(IO.formatMsg('sub', 'Calc curve', f'{nr_points} points', 'on sample page', 'replaced'))

    @Slot()
    def drawCalculatedOnSldChart(self):
        if PLOT_BACKEND == 'QtCharts':
            self.qtchartsReplaceCalculatedOnSldChartAndRedraw()

    def qtchartsReplaceCalculatedOnSldChartAndRedraw(self):
        # Draw on sample page
        series = self._chartRefs['QtCharts']['samplePage']['sldSerie']
        if series is not None:
            nr_points = self._replace_series_points(series, self.sld_data.data_points())
            console.debug(IO.formatMsg('sub', 'Sld curve', f'{nr_points} points', 'on sample page', 'replaced'))

        # Draw on analysis page
        analysis_series = self._chartRefs['QtCharts']['analysisPage']['sldSerie']
        if analysis_series is not None:
            nr_points = self._replace_series_points(analysis_series, self.sld_data.data_points())
            console.debug(IO.formatMsg('sub', 'Sld curve', f'{nr_points} points', 'on analysis page', 'replaced'))

    @Slot()
    def drawMeasuredOnExperimentChart(self):
        if PLOT_BACKEND == 'QtCharts':
            if self.is_multi_experiment_mode:
                self.qtchartsReplaceMultiExperimentChartAndRedraw()
            else:
                self.qtchartsReplaceMeasuredOnExperimentChartAndRedraw()

    def qtchartsReplaceMeasuredOnExperimentChartAndRedraw(self):
        if not self._clear_qtcharts_series('experimentPage', 'measuredSerie', 'errorUpperSerie', 'errorLowerSerie'):
            return

        series_measured = self._qtcharts_series_ref('experimentPage', 'measuredSerie')
        series_error_upper = self._qtcharts_series_ref('experimentPage', 'errorUpperSerie')
        series_error_lower = self._qtcharts_series_ref('experimentPage', 'errorLowerSerie')
        measured_points = []
        error_upper_points = []
        error_lower_points = []
        for point in self.experiment_data.data_points():
            q = point[0]
            r = point[1]
            if r <= 0:
                continue
            error_var = point[2]
            error_lower_linear = max(r - np.sqrt(error_var), 1e-10)
            r_val = self._apply_rq4(q, r)
            error_upper = self._apply_rq4(q, r + np.sqrt(error_var))
            error_lower = self._apply_rq4(q, error_lower_linear)
            measured_points.append((q, np.log10(r_val)))
            error_upper_points.append((q, np.log10(error_upper)))
            error_lower_points.append((q, np.log10(error_lower)))
        self._replace_series_points(series_measured, measured_points)
        self._replace_series_points(series_error_upper, error_upper_points)
        self._replace_series_points(series_error_lower, error_lower_points)

        console.debug(IO.formatMsg('sub', 'Measured curve', f'{len(measured_points)} points', 'on experiment page', 'replaced'))

    def qtchartsReplaceMultiExperimentChartAndRedraw(self):
        """Draw multiple experiment series with distinct colors."""
        console.debug(IO.formatMsg('sub', 'Multi-experiment mode', 'drawing separate lines'))

        # Clear default series but don't use them for multi-experiment mode
        self._clear_qtcharts_series('experimentPage', 'measuredSerie', 'errorUpperSerie', 'errorLowerSerie')

        # Individual experiment series are managed by QML
        # This method is called to trigger the refresh, actual drawing is handled by QML
        self.experimentDataChanged.emit()

    @Slot()
    def drawCalculatedAndMeasuredOnAnalysisChart(self):
        if PLOT_BACKEND == 'QtCharts':
            if self.is_multi_experiment_mode:
                self.qtchartsReplaceMultiExperimentAnalysisChartAndRedraw()
            else:
                self.qtchartsReplaceCalculatedAndMeasuredOnAnalysisChartAndRedraw()

    def qtchartsReplaceMultiExperimentAnalysisChartAndRedraw(self):
        """Clear default series and let QML handle multi-experiment drawing on analysis page."""
        console.debug(IO.formatMsg('sub', 'Multi-experiment mode', 'drawing separate lines on analysis page'))

        # Clear default series but don't use them for multi-experiment mode
        self._clear_qtcharts_series('analysisPage', 'measuredSerie', 'calculatedSerie')

        # Individual experiment series are managed by QML
        # This method is called to trigger the refresh, actual drawing is handled by QML
        self.experimentDataChanged.emit()

    def qtchartsReplaceCalculatedAndMeasuredOnAnalysisChartAndRedraw(self):
        if not self._clear_qtcharts_series('analysisPage', 'measuredSerie', 'calculatedSerie'):
            return

        series_measured = self._qtcharts_series_ref('analysisPage', 'measuredSerie')
        series_calculated = self._qtcharts_series_ref('analysisPage', 'calculatedSerie')
        nr_points = self._replace_series_points(
            series_measured,
            (
                (point[0], np.log10(self._apply_rq4(point[0], point[1])))
                for point in self.experiment_data.data_points()
                if point[1] > 0
            ),
        )
        console.debug(IO.formatMsg('sub', 'Measured curve', f'{nr_points} points', 'on analysis page', 'replaced'))

        nr_points = self._replace_series_points(
            series_calculated,
            ((point[0], np.log10(self._apply_rq4(point[0], point[1]))) for point in self.model_data.data_points()),
        )
        console.debug(IO.formatMsg('sub', 'Calculated curve', f'{nr_points} points', 'on analysis page', 'replaced'))

    # ------------------------------------------------------------------
    # Posterior predictive (Bayesian)
    # ------------------------------------------------------------------

    @Property('QVariantList', notify=posteriorPredictiveDataChanged)
    def posteriorPredictiveQ(self) -> list:
        return self._posterior_q

    @Property('QVariantList', notify=posteriorPredictiveDataChanged)
    def posteriorPredictiveMedian(self) -> list:
        return self._transform_posterior_series(
            self._posterior_q, self._posterior_median)

    @Property('QVariantList', notify=posteriorPredictiveDataChanged)
    def posteriorPredictiveLower(self) -> list:
        return self._transform_posterior_series(
            self._posterior_q, self._posterior_lower)

    @Property('QVariantList', notify=posteriorPredictiveDataChanged)
    def posteriorPredictiveUpper(self) -> list:
        return self._transform_posterior_series(
            self._posterior_q, self._posterior_upper)

    def _transform_posterior_series(self, q_list: list, y_list: list) -> list:
        """Apply RQ4 and log10 transforms to a posterior predictive series.

        Transforms are applied at read time so that toggling plot mode
        (RQ4 on/off) is reflected without re-publishing the data.
        """
        if not y_list:
            return []
        q = np.asarray(q_list, dtype=float)
        y = np.asarray(y_list, dtype=float)
        y = self._apply_rq4(q, y)
        eps = 1e-30
        return np.where(y > 0, np.log10(y), np.log10(eps)).tolist()

    def set_posterior_predictive(self, q, median, lower, upper) -> None:
        """Publish posterior predictive reflectivity curves to QML.

        Applies the same chart-space transforms (R(q)×q⁴, log10) used by
        the existing analysis series, so the posterior overlay stays in sync
        with plot-mode toggles.
        """
        import numpy as np

        q = np.asarray(q, dtype=float)
        median = np.asarray(median, dtype=float)
        lower = np.asarray(lower, dtype=float)
        upper = np.asarray(upper, dtype=float)

        # Store linear data — transforms applied at read time in property getters
        # so that toggling RQ4 mode is reflected without re-publishing.
        self._posterior_q = q.tolist()
        self._posterior_median = median.tolist()
        self._posterior_lower = lower.tolist()
        self._posterior_upper = upper.tolist()
        self.posteriorPredictiveDataChanged.emit()

    def clear_posterior_predictive(self) -> None:
        """Clear the posterior predictive reflectivity data."""
        self._posterior_q = []
        self._posterior_median = []
        self._posterior_lower = []
        self._posterior_upper = []
        self.posteriorPredictiveDataChanged.emit()

    # ------------------------------------------------------------------
    # Posterior predictive SLD profile (Phase 2)
    # ------------------------------------------------------------------

    @Property('QVariantList', notify=posteriorPredictiveSldDataChanged)
    def posteriorPredictiveSldZ(self) -> list:
        return self._posterior_sld_z

    @Property('QVariantList', notify=posteriorPredictiveSldDataChanged)
    def posteriorPredictiveSldMedian(self) -> list:
        return self._posterior_sld_median

    @Property('QVariantList', notify=posteriorPredictiveSldDataChanged)
    def posteriorPredictiveSldLower(self) -> list:
        return self._posterior_sld_lower

    @Property('QVariantList', notify=posteriorPredictiveSldDataChanged)
    def posteriorPredictiveSldUpper(self) -> list:
        return self._posterior_sld_upper

    def set_posterior_predictive_sld(self, z, median, lower, upper) -> None:
        """Publish posterior predictive SLD profile curves to QML.

        Unlike reflectivity, SLD data is published without any chart-space
        transform, matching the existing SLD chart series convention.
        """
        import numpy as np

        z = np.asarray(z, dtype=float)
        median = np.asarray(median, dtype=float)
        lower = np.asarray(lower, dtype=float)
        upper = np.asarray(upper, dtype=float)

        self._posterior_sld_z = z.tolist()
        self._posterior_sld_median = median.tolist()
        self._posterior_sld_lower = lower.tolist()
        self._posterior_sld_upper = upper.tolist()
        self.posteriorPredictiveSldDataChanged.emit()

    def clear_posterior_predictive_sld(self) -> None:
        """Clear the posterior predictive SLD data."""
        self._posterior_sld_z = []
        self._posterior_sld_median = []
        self._posterior_sld_lower = []
        self._posterior_sld_upper = []
        self.posteriorPredictiveSldDataChanged.emit()
