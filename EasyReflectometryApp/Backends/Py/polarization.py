"""Polarization backend.

Implements the QML polarization contract (see POLARIZATION_IMPL_GUI.md) against
real loaded data. Polarization is enabled by a manual user toggle: when on, the
separately-loaded experiment files are treated as one logical polarized
experiment whose spin channels are mapped from the loaded files in load order
(channel 0 -> pp, 1 -> mm, 2 -> pm, 3 -> mp).

Per-channel reflectivity/analysis/residual data is delegated to the existing
Plotting1d methods so it stays consistent with the non-polarized plotting
contract (log10 + R(q)x q^4 handling). Spin asymmetry is computed from the pp
and mm channels.
"""

import numpy as np
from EasyApplication.Logic.Logging import console
from easyreflectometry import Project as ProjectLib
from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

# Canonical channel order. The list index is the loaded-experiment index a
# channel maps to when polarization is enabled.
_CHANNELS = [
    {'key': 'pp', 'label': 'R++', 'description': 'up-up', 'color': '#ef4444'},
    {'key': 'mm', 'label': 'R--', 'description': 'down-down', 'color': '#64748b'},
    {'key': 'pm', 'label': 'R+-', 'description': 'up-down', 'color': '#22c55e'},
    {'key': 'mp', 'label': 'R-+', 'description': 'down-up', 'color': '#f97316'},
]

_SLD_COMPONENTS = [
    {'key': 'nuclear', 'label': 'Nuclear', 'symbol': 'rho_n', 'color': '#f59e0b'},
    {'key': 'magnetic', 'label': 'Magnetic', 'symbol': 'rho_m', 'color': '#14b8a6'},
]


class Polarization(QObject):
    # displayChanged: channel/component membership or visibility changed -> recreate series.
    # dataChanged: only data values changed -> refresh existing series.
    displayChanged = Signal()
    dataChanged = Signal()

    def __init__(self, project_lib: ProjectLib, plotting, parent=None):
        super().__init__(parent)
        self._project_lib = project_lib
        self._plotting = plotting
        self._polarized = False
        self._stagger_enabled = False
        self._stagger_factor = 0.5
        self._visible_channel_keys = ['pp', 'mm']
        self._visible_sld_component_keys = ['nuclear', 'magnetic']

    # ------------------------------------------------------------------ helpers
    def _experiment_count(self) -> int:
        try:
            return len(self._project_lib._experiments.keys())
        except Exception:  # noqa: S110
            return 0

    def _channel_experiment_index(self, channel_key: str) -> int:
        for index, channel in enumerate(_CHANNELS):
            if channel['key'] == channel_key:
                return index
        return -1

    def _channel_available(self, channel_key: str) -> bool:
        index = self._channel_experiment_index(channel_key)
        return 0 <= index < self._experiment_count()

    def _model_has_magnetism(self) -> bool:
        # Magnetic SLD components require magnetic model parameters, which are not
        # yet exposed in the model layer. Until then the magnetic component is
        # advertised as unavailable. See POLARIZATION_IMPL.md section 4.2.
        return False

    # --------------------------------------------------------------- properties
    @Property(bool, notify=displayChanged)
    def available(self) -> bool:
        return bool(self._polarized) and self._experiment_count() > 0

    @Property(bool, notify=displayChanged)
    def polarized(self) -> bool:
        return bool(self._polarized)

    @Property('QVariantList', notify=displayChanged)
    def channels(self) -> list:
        count = self._experiment_count()
        result = []
        for index, channel in enumerate(_CHANNELS):
            enabled = index < count
            result.append(
                {
                    'key': channel['key'],
                    'label': channel['label'],
                    'description': channel['description'],
                    'color': channel['color'],
                    'enabled': enabled,
                    'hasMeasured': enabled,
                    'hasCalculated': enabled,
                }
            )
        return result

    @Property('QVariantList', notify=displayChanged)
    def visibleChannelKeys(self) -> list:
        return list(self._visible_channel_keys)

    @Property(bool, notify=displayChanged)
    def staggerEnabled(self) -> bool:
        return bool(self._stagger_enabled)

    @Property(float, notify=displayChanged)
    def staggerFactor(self) -> float:
        return float(self._stagger_factor)

    @Property('QVariantList', notify=displayChanged)
    def sldComponents(self) -> list:
        has_magnetic = self._model_has_magnetism()
        result = []
        for component in _SLD_COMPONENTS:
            is_available = True if component['key'] == 'nuclear' else has_magnetic
            result.append(
                {
                    'key': component['key'],
                    'label': component['label'],
                    'symbol': component['symbol'],
                    'color': component['color'],
                    'enabled': is_available,
                    'available': is_available,
                }
            )
        return result

    @Property('QVariantList', notify=displayChanged)
    def visibleSldComponentKeys(self) -> list:
        return list(self._visible_sld_component_keys)

    # ------------------------------------------------------------------ setters
    @Slot(bool)
    def setPolarized(self, value: bool) -> None:
        value = bool(value)
        if value == self._polarized:
            return
        self._polarized = value
        if value:
            # Default to showing every channel backed by a loaded file.
            self._visible_channel_keys = [c['key'] for c in _CHANNELS if self._channel_available(c['key'])]
        self.displayChanged.emit()

    @Slot(str, bool)
    def setChannelVisible(self, channel_key: str, visible: bool) -> None:
        keys = list(self._visible_channel_keys)
        if visible and channel_key not in keys:
            keys.append(channel_key)
        elif not visible and channel_key in keys:
            keys.remove(channel_key)
        self._visible_channel_keys = keys
        self.displayChanged.emit()

    @Slot('QVariantList')
    def setVisibleChannelKeys(self, channel_keys) -> None:
        self._visible_channel_keys = [str(k) for k in channel_keys]
        self.displayChanged.emit()

    @Slot(bool)
    def setStaggerEnabled(self, value: bool) -> None:
        self._stagger_enabled = bool(value)
        self.displayChanged.emit()

    @Slot(float)
    def setStaggerFactor(self, value: float) -> None:
        self._stagger_factor = float(value)
        self.displayChanged.emit()

    @Slot(str, bool)
    def setSldComponentVisible(self, component_key: str, visible: bool) -> None:
        keys = list(self._visible_sld_component_keys)
        if visible and component_key not in keys:
            keys.append(component_key)
        elif not visible and component_key in keys:
            keys.remove(component_key)
        self._visible_sld_component_keys = keys
        self.displayChanged.emit()

    @Slot('QVariantList')
    def setVisibleSldComponentKeys(self, component_keys) -> None:
        self._visible_sld_component_keys = [str(k) for k in component_keys]
        self.displayChanged.emit()

    # -------------------------------------------------------------- data slots
    @Slot(int, result='QVariantList')
    def getExperimentChannels(self, experiment_index: int) -> list:
        # Channel availability is per logical polarized experiment; the index is
        # accepted for contract parity but the same channel set applies.
        return self.channels

    @Slot(int, str, result='QVariantList')
    def getExperimentChannelDataPoints(self, experiment_index: int, channel_key: str) -> list:
        index = self._channel_experiment_index(channel_key)
        if not (0 <= index < self._experiment_count()):
            return []
        return self._plotting.getExperimentDataPoints(index)

    @Slot(int, str, result='QVariantList')
    def getAnalysisChannelDataPoints(self, experiment_index: int, channel_key: str) -> list:
        index = self._channel_experiment_index(channel_key)
        if not (0 <= index < self._experiment_count()):
            return []
        return self._plotting.getAnalysisDataPoints(index)

    @Slot(int, str, result='QVariantList')
    def getSampleChannelDataPoints(self, model_index: int, channel_key: str) -> list:
        # No per-channel calculated model yet; all channels share the model curve.
        return self._plotting.getSampleDataPointsForModel(model_index)

    @Slot(int, str, result='QVariantList')
    def getSldComponentDataPoints(self, model_index: int, component_key: str) -> list:
        if component_key == 'nuclear':
            return self._plotting.getSldDataPointsForModel(model_index)
        # Magnetic SLD profile is unavailable until magnetic model params exist.
        return []

    @Slot(int, str, result='QVariantList')
    def getPolarizationResidualDataPoints(self, experiment_index: int, channel_key: str) -> list:
        index = self._channel_experiment_index(channel_key)
        if not (0 <= index < self._experiment_count()):
            return []
        return self._plotting.getResidualDataPoints(index)

    @Slot(int, result='QVariant')
    def getSpinAsymmetryDataPoints(self, experiment_index: int) -> dict:
        return self._compute_spin_asymmetry()

    # --------------------------------------------------------------- internals
    def _compute_spin_asymmetry(self) -> dict:
        """Spin asymmetry SA = (R++ - R--) / (R++ + R--) from the pp/mm channels.

        Measured uncertainty is propagated from the per-channel ``ye`` arrays.
        ``calculated`` mirrors ``measured`` as a placeholder until a real
        polarized calculation exists (no per-channel model yet).
        """
        empty = {'x': [], 'measured': [], 'sigma': [], 'calculated': []}
        if self._experiment_count() < 2:
            return empty
        try:
            pp = self._project_lib.experimental_data_for_model_at_index(0)
            mm = self._project_lib.experimental_data_for_model_at_index(1)

            q_pp = np.asarray(getattr(pp, 'x', np.empty(0)), dtype=float)
            r_pp = np.asarray(getattr(pp, 'y', np.empty(0)), dtype=float)
            e_pp = np.asarray(getattr(pp, 'ye', np.zeros_like(r_pp)), dtype=float)
            q_mm = np.asarray(getattr(mm, 'x', np.empty(0)), dtype=float)
            r_mm = np.asarray(getattr(mm, 'y', np.empty(0)), dtype=float)
            e_mm = np.asarray(getattr(mm, 'ye', np.zeros_like(r_mm)), dtype=float)

            if q_pp.size == 0 or q_mm.size == 0:
                return empty

            # Restrict to the q overlap and interpolate mm onto the pp grid.
            lo = max(q_pp.min(), q_mm.min())
            hi = min(q_pp.max(), q_mm.max())
            mask = (q_pp >= lo) & (q_pp <= hi)
            q = q_pp[mask]
            if q.size == 0:
                return empty
            a = r_pp[mask]
            sa_err = e_pp[mask] if e_pp.size else np.zeros_like(a)
            b = np.interp(q, q_mm, r_mm)
            sb_err = np.interp(q, q_mm, e_mm) if e_mm.size else np.zeros_like(b)

            denom = a + b
            safe = denom != 0
            sa = np.zeros_like(q)
            sa[safe] = (a[safe] - b[safe]) / denom[safe]

            sigma = np.zeros_like(q)
            d2 = denom[safe] ** 2
            sigma[safe] = np.sqrt(
                (2.0 * b[safe] / d2 * sa_err[safe]) ** 2 + (2.0 * a[safe] / d2 * sb_err[safe]) ** 2
            )

            return {
                'x': q.tolist(),
                'measured': sa.tolist(),
                'sigma': sigma.tolist(),
                'calculated': sa.tolist(),
            }
        except Exception as e:
            console.debug(f'Error computing spin asymmetry: {e}')
            return empty
