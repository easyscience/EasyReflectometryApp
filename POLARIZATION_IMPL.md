# Polarization Implementation Analysis

> Generated: 2026-05-03 — Analysis of polarized beam support across `reflectometry-lib` and `EasyReflectometryApp`.

---

## 1. Polarized Beam Support in `reflectometry-lib`

Polarization support lives in the **refl1d calculator wrapper** and the **calculator base** classes.

### 1.1 `wrapper_base.py` — Magnetism Flag

**Path:** `reflectometry-lib/src/easyreflectometry/calculators/wrapper_base.py`

The `WrapperBase` class has a `_magnetism` boolean flag (default `False`) with a property getter/setter:

```python
self._magnetism = False  # line 12

@property
def magnetism(self) -> bool:        # line 216
    return self._magnetism

@magnetism.setter
def magnetism(self, magnetism: bool):  # line 219
    self._magnetism = magnetism
```

### 1.2 `calculator_base.py` — Public API

**Path:** `reflectometry-lib/src/easyreflectometry/calculators/calculator_base.py`

The `include_magnetism` property on the calculator delegates to the wrapper:

```python
@property
def include_magnetism(self):              # line 183
    return self._wrapper.magnetism

@include_magnetism.setter
def include_magnetism(self, magnetism: bool):  # line 187
    self._wrapper.magnetism = magnetism
```

### 1.3 `refl1d/wrapper.py` — Actual Polarization Calculation

**Path:** `reflectometry-lib/src/easyreflectometry/calculators/refl1d/wrapper.py`

Key elements:

- **`ALL_POLARIZATIONS = False`** (line 15) — controls whether all 4 spin channels (`++`, `+-`, `-+`, `--`) are computed or just `++`.

- **Layer magnetism** (lines 31–42):
  - `create_layer()` adds `names.Magnetism(rhoM=0.0, thetaM=0.0)` when magnetism is enabled.
  - `update_layer()` handles `magnetism_rhoM` / `magnetism_thetaM` kwargs separately from structural params.

- **`calculate()` method** (lines 152–195) — branches on `self._magnetism`:
  - **Non-magnetic**: Uses a standard `QProbe` → `names.Experiment(probe, sample).reflectivity()` → returns single reflectivity array.
  - **Magnetic**: Uses `_get_polarized_probe()` → `PolarizedNeutronQProbe` → `names.Experiment(probe, sample).reflectivity()` → returns a list of `(q, R)` tuples. Currently only the first (`R++`) is used; all 4 channels are commented out with `NotImplementedError`.

- **`_get_polarized_probe()`** (line 253) — Creates a `PolarizedNeutronQProbe` with 4 probes (one per spin channel). When `all_polarizations=False`, only probe 0 (`++`) is populated; the other 3 are `None`. Includes a workaround for a `_union_cache_key` initialization bug in refl1d.

- **`_get_probe()`** (line 237) — When `magnetism=True`, adds `theta_offset` attribute required for `PolarizedQProbe`.

### 1.4 Polarization in the Data Layer

**Path:** `reflectometry-lib/src/easyreflectometry/data/`

The data classes (`DataSet1D`, `DataStore`, `ProjectData`) are **polarization-agnostic**. They store x, y, ye, xe arrays with no concept of spin channels. Polarization awareness exists only at the calculator level.

### 1.5 Summary: Polarization in reflectometry-lib

| Feature | Status |
|---|---|
| `include_magnetism` flag on calculator | ✅ Implemented |
| Single-channel polarized calc (R++) | ✅ Implemented |
| All 4 channels (++, +-, -+, --) | 🚧 Code structure exists, guarded by `NotImplementedError` |
| Magnetic layer properties (rhoM, thetaM) | ✅ Implemented via `names.Magnetism` |
| Polarization in data layer (`data/`) | ❌ Not present — data classes are polarization-agnostic |

---

## 2. How Polarization Is Used in `EasyReflectometryApp`

The polarization UI is **fully implemented as of 2026-05-02** per `POLARIZATION.md`. It was built in 4 phases (QML skeleton → chart series → lower panel → Sample tab).

### 2.1 Architecture

All polarization state flows through a clean boundary:

```
MockBackend.qml → BackendWrapper.qml → QML Components
  (mock data)      (try/catch guards)   (reusable selectors/charts)
```

### 2.2 `Backends/Mock/Polarization.qml` — Mock Data Source

**Path:** `EasyReflectometryApp/EasyReflectometryApp/Backends/Mock/Polarization.qml`

Provides all the data the GUI needs with synthetic data:

- **4 channels**: `pp`, `mm`, `pm`, `mp` with standard polarization colors:
  - `R++` (up-up): `#ef4444` (red)
  - `R--` (down-down): `#64748b` (blue-grey)
  - `R+-` (up-down): `#22c55e` (green)
  - `R-+` (down-up): `#f97316` (orange)

- **2 SLD components**:
  - `nuclear` (`rho_n`): `#f59e0b` (orange)
  - `magnetic` (`rho_m`): `#14b8a6` (teal)

- **Mock data functions**:
  - `getExperimentChannels(experimentIndex)` — per-experiment channel availability
  - `getAnalysisChannelDataPoints(experimentIndex, channelKey)` — `{x, measured, calculated}` points
  - `getSampleChannelDataPoints(modelIndex, channelKey)` — `{x, y}` points
  - `getSldComponentDataPoints(modelIndex, componentKey)` — `{x, y}` points
  - `getSpinAsymmetryDataPoints(experimentIndex)` — `{x, measured, sigma, calculated}`
  - `getPolarizationResidualDataPoints(experimentIndex, channelKey)` — `{x, y}` points

- **Signals**: `displayChanged()`, `dataChanged()` for QML binding

- **State management**: `setChannelVisible()`, `setVisibleChannelKeys()`, `setStaggerEnabled()`, `setStaggerFactor()`, `setSldComponentVisible()`, `setVisibleSldComponentKeys()`

### 2.3 `Gui/Globals/BackendWrapper.qml` — Safe Boundary

**Path:** `EasyReflectometryApp/EasyReflectometryApp/Gui/Globals/BackendWrapper.qml`

All polarization properties/slots use `try/catch` guards so the app works against today's `PyBackend` (which has no `polarization` object):

**Properties** (lines 568–618):
```qml
readonly property bool polarizationAvailable
readonly property var polarizationChannels
readonly property var polarizationVisibleChannelKeys
readonly property bool polarizationStaggerEnabled
readonly property real polarizationStaggerFactor
readonly property var polarizationSldComponents
readonly property var polarizationVisibleSldComponentKeys
```

**Slots** (lines 623–680):
```qml
function polarizationSetChannelVisible(channelKey, visible)
function polarizationSetVisibleChannelKeys(channelKeys)
function polarizationSetStaggerEnabled(value)
function polarizationSetStaggerFactor(value)
function polarizationSetSldComponentVisible(componentKey, visible)
function polarizationSetVisibleSldComponentKeys(componentKeys)
function polarizationGetExperimentChannels(experimentIndex)
function plottingGetAnalysisChannelDataPoints(experimentIndex, channelKey)
function plottingGetSampleChannelDataPoints(modelIndex, channelKey)
function plottingGetSldComponentDataPoints(modelIndex, componentKey)
function plottingGetSpinAsymmetryDataPoints(experimentIndex)
function plottingGetPolarizationResidualDataPoints(experimentIndex, channelKey)
```

**Signals** (lines 620–621):
```qml
signal polarizationDisplayChanged()   // channel/component membership changed → recreate series
signal polarizationDataChanged()      // only data values changed → refresh existing series
```

Signal forwarding is wired in `connectPolarizationSignals()` (line 522), connecting `activeBackend.polarization.displayChanged` → `polarizationDisplayChanged` and `activeBackend.polarization.dataChanged` → `polarizationDataChanged`.

### 2.4 Reusable QML Components (`Gui/Components/`)

| Component | Purpose |
|---|---|
| `PolarizationChannelSelector.qml` | GroupBox with 4 channel rows (checkbox + color swatch + label) + stagger checkbox |
| `SldComponentSelector.qml` | GroupBox with Nuclear/Magnetic component rows |
| `ChartToolbar.qml` | Shared legend/hover/pan/zoom/reset toolbar (extracted from 3+ charts) |
| `ChartMouseControls.qml` | Shared box-zoom/pan/right-click-reset mouse behavior |

### 2.5 UI Layout Details

#### Analysis Tab (`Analysis/Layout.qml`)

**Sidebar** (`Analysis/Sidebar/Basic/Layout.qml`):
```
Experiments
PolarizationChannels   ← NEW (hidden when !polarizationAvailable)
SldComponents          ← NEW (hidden when !polarizationAvailable)
Fittables
Fitting                (registered separately)
```

**Main content top** (`Analysis/MainContent/CombinedView.qml`):
- Channel-aware reflectivity chart with per-`(experiment, channel)` series
- Extends existing multi-experiment pipeline; channel is the inner series dimension
- Measured = markers/dotted, Calculated = solid line, colored by channel
- Staggering = additive offset on log-Y using `polarizationStaggerFactor`
- Reacts to `polarizationDisplayChanged` (recreate series + reset axes) and `polarizationDataChanged` (refresh data)

**Main content lower** (`Analysis/MainContent/SldView.qml`):
```
SLD            — component-aware (nuclear + magnetic lines when polarized)
Spin asymmetry — NEW tab (hidden when !polarizationAvailable)
Residuals      — per-channel residual lines when polarized
```

#### Sample Tab (`Sample/Layout.qml`)

**Sidebar**: Selectors (`PolarizationChannelSelector`, `SldComponentSelector`) in **Advanced** column (`Sample/Sidebar/Advanced/Layout.qml`), keeping Basic sidebar focused on model/material/layer editing.

**Main content**: Channel-aware calculated reflectivity + SLD component rendering, sharing visibility state with Analysis tab.

### 2.6 When `polarizationAvailable` is `false`

- `PolarizationChannels` and `SldComponents` sidebar groups are **hidden**
- Lower panel shows original `SLD | Residuals` (2 tabs, no Spin Asymmetry)
- Charts behave exactly as before — single-channel, no polarization awareness
- Current `PyBackend` (no `polarization` object) → `polarizationAvailable` returns `false` via `try/catch`

### 2.7 Chart Series Behavior

The chart uses a 2-D matrix `(experiment × channel)`:

1. `multiExperimentSeries` stores a sub-map keyed by `channel.key`, each containing the measured/error/calculated series triplet.
2. `updateMultiExperimentSeries()` inner-loops over `polarizationGetExperimentChannels(experimentIndex)` filtered by `polarizationVisibleChannelKeys`.
3. Channel color and measured/calculated style conventions applied per `(experiment, channel)` triplet.
4. In multi-experiment mode, experiments sharing the same channel use the same channel color, distinguished by dash pattern or marker shape.
5. Staggering applied as additive offset on log-Y per visible channel.
6. On `polarizationDisplayChanged` → `updateMultiExperimentSeries()` + reset axes.
7. On `polarizationDataChanged` → refresh data into existing series without recreation.

---

## 3. What's NOT Implemented Yet (Phase 5 — Python Backend)

The Python `PyBackend` has **no `polarization` object**. The mock backend provides all data for UI development. Phase 5 (planned for later) needs to implement:

1. A real `polarization` backend object exposed from `PyBackend`
2. Channel metadata (including per-experiment availability) and persisted visibility state
3. Channel-specific calculated reflectivity data from the calculator
4. Channel-specific measured data loading where available
5. Nuclear/magnetic SLD component data, including the `available` flag per component
6. Spin asymmetry computation with measured, sigma, and calculated arrays
7. Per-channel polarization residuals
8. **Project serialization** for polarization display preferences (channel/component visibility, stagger settings)

---

## 4. Assessment Against Current `reflectometry-lib`

Short answer: **the plan identifies the right GUI contract, but it does not yet fully cover the necessary functionality changes in `reflectometry-lib` and the live `PyBackend`.** It is sufficient as a UI/mock-backend implementation record, but not as a complete backend implementation plan.

The current GUI described in `POLARIZATION.md` expects a backend object with channel-aware metadata and plotting methods. The current `reflectometry-lib` only exposes a scalar reflectivity path plus a refl1d-specific magnetism flag. Bridging those two worlds requires more than adding a `polarization` property to `PyBackend`.

### 4.1 Existing Library Support That Can Be Reused

- `CalculatorBase.include_magnetism` delegates to `WrapperBase.magnetism`.
- `Refl1dWrapper.create_layer()` can create `refl1d.names.Magnetism` on layers when magnetism is enabled.
- `Refl1dWrapper.calculate()` already creates a `PolarizedNeutronQProbe` in magnetic mode.
- `_get_polarized_probe()` already knows how to create four probe slots, although only the first slot is populated while `ALL_POLARIZATIONS = False`.

### 4.2 Missing `reflectometry-lib` Functionality

The following changes are needed before the current GUI can be backed by real library calculations:

1. **Channel-specific reflectivity API**
  - Existing API: `CalculatorBase.reflectity_profile(...) -> np.ndarray` and `Project.model_data_for_model_at_index(...) -> DataSet1D` return one reflectivity curve.
  - Needed API: a non-breaking method returning a mapping such as `{ 'pp': array, 'pm': array, 'mp': array, 'mm': array }`, plus project-level helpers that return channel-specific `DataSet1D` objects.
  - Keep the existing scalar method for non-polarized code paths.

2. **Remove the module-global channel switch**
  - Existing refl1d code uses `ALL_POLARIZATIONS = False` and raises `NotImplementedError` when it is true.
  - Needed behavior: choose requested channels per call, return all requested channels, and avoid global mutable behavior.
  - The refl1d result order in the current comments is `pp`, `pm`, `mp`, `mm`; the GUI metadata order is `pp`, `mm`, `pm`, `mp`, so the backend must map keys explicitly.

3. **Magnetic parameters in the EasyReflectometry model layer**
  - `Refl1dWrapper.update_layer()` can consume `magnetism_rhoM` and `magnetism_thetaM`, but `Refl1d._layer_link` currently exposes only `thickness` and `roughness`, and `sample.elements.layers.Layer` has no `magnetism_rhoM` / `magnetism_thetaM` parameters.
  - Needed behavior: add magnetic layer parameters or a magnetic-layer extension, wire them into the refl1d calculator link, expose them to fitting/serialization, and decide how the GUI enables/disables magnetic SLD availability.

4. **Channel-aware measured data model**
  - `DataSet1D` is polarization-agnostic and `Project._experiments` maps one index to one `DataSet1D`.
  - The GUI expects one experiment to be able to expose multiple channels through `polarizationGetExperimentChannels(experimentIndex)`.
  - Needed behavior: either add channel metadata/grouping around `DataSet1D` objects or introduce a small polarized experiment container that maps channel keys to `DataSet1D` instances.

5. **ORSO / text import channel metadata**
  - Existing loading turns files into generic datasets and `load_all_experiments_from_file()` can load multiple datasets as separate experiments.
  - Needed behavior: detect polarized ORSO datasets/channels, group them under a logical experiment when appropriate, preserve channel labels, and gracefully handle partial channel sets.

6. **Component-specific SLD profiles**
  - Existing `sld_profile()` returns only one `DataSet1D` curve.
  - The GUI expects `nuclear` and `magnetic` component series via `plottingGetSldComponentDataPoints(modelIndex, componentKey)`.
  - Needed behavior: provide component-specific profile data, including an `available` flag for the magnetic component.

7. **Project serialization**
  - Existing project serialization writes experiment arrays and model data, but no channel grouping, magnetic layer parameters, or polarization display state.
  - Needed behavior: persist channel/component visibility, stagger settings, measured channel grouping, and magnetic parameters.

8. **Calculator capability handling**
  - `refnx` explicitly does not support magnetism.
  - Needed behavior: expose polarization only when the active calculator supports it, most likely refl1d-only for now. The app should keep `polarizationAvailable = false` for refnx/bornagain unless support is implemented.

### 4.3 Missing `EasyReflectometryApp` Python Backend Functionality

The app also needs live Python backend work beyond the mock QML object:

1. Add a `Backends/Py/polarization.py` QObject, expose it from `PyBackend` as `@Property('QVariant', constant=True) def polarization(...)`, and match the current QML contract exactly.
2. Implement properties/signals: `available`, `channels`, `visibleChannelKeys`, `staggerEnabled`, `staggerFactor`, `sldComponents`, `visibleSldComponentKeys`, `displayChanged`, and `dataChanged`.
3. Implement slots used by `BackendWrapper.qml`: channel visibility setters, `getExperimentChannels`, `getAnalysisChannelDataPoints`, `getSampleChannelDataPoints`, `getSldComponentDataPoints`, `getSpinAsymmetryDataPoints`, and `getPolarizationResidualDataPoints`.
4. Return plotting-ready values consistently with the existing non-polarized plotting backend. Current QML appends reflectivity Y values directly, and `Plotting1d.getAnalysisDataPoints()` / `getSampleDataPointsForModel()` already return `log10(R)` values with `R(q) x q^4` applied when enabled. The polarization backend should follow that same contract unless the QML is changed.
5. Compute spin asymmetry from matched/interpolated `pp` and `mm` channels and propagate measured uncertainty when measured data exist.
6. Reuse existing cache invalidation and refresh signals from sample, experiment, project load/reset, fitting, and `R(q) x q^4` changes so channel data updates with the rest of the app.

### 4.4 Verdict

`POLARIZATION_IMPL.md` currently covers the **QML-facing contract** and the **mock implementation**, but it does **not** yet cover enough concrete `reflectometry-lib` changes to implement the current GUI against real data. The most important missing pieces are the channel-specific reflectivity API, magnetic model parameters, channel-aware measured data grouping, SLD component profiles, and serialization.

---

## 5. File Map — Polarization-Related Files

### reflectometry-lib
```
src/easyreflectometry/calculators/
├── calculator_base.py     ← include_magnetism property
├── wrapper_base.py        ← _magnetism flag
└── refl1d/wrapper.py      ← PolarizedNeutronQProbe, _get_polarized_probe, ALL_POLARIZATIONS
```

### EasyReflectometryApp
```
EasyReflectometryApp/
├── POLARIZATION.md                              ← Design plan document
├── Backends/
│   ├── MockBackend.qml                          ← Exposes Mock.Polarization
│   └── Mock/
│       ├── Polarization.qml                     ← Mock data & state (all 4 channels, 2 SLD components)
│       └── qmldir                               ← Registers Polarization singleton
├── Gui/
│   ├── Components/
│   │   ├── PolarizationChannelSelector.qml      ← Reusable 4-channel visibility group
│   │   ├── SldComponentSelector.qml             ← Reusable SLD component visibility group
│   │   ├── ChartToolbar.qml                     ← Shared chart toolbar
│   │   ├── ChartMouseControls.qml               ← Shared mouse interaction
│   │   └── qmldir                               ← Registers components module
│   ├── Globals/
│   │   └── BackendWrapper.qml                   ← try/catch-guarded polarization API
│   └── Pages/
│       ├── Analysis/
│       │   ├── Layout.qml                       ← Top-level Analysis page
│       │   ├── Sidebar/Basic/Layout.qml         ← Sidebar with polarization groups
│       │   └── MainContent/
│       │       ├── CombinedView.qml              ← Channel-aware reflectivity chart
│       │       ├── SldView.qml                   ← 3-tab lower panel (SLD|SpinAsym|Residuals)
│       │       ├── SpinAsymmetryView.qml         ← Spin asymmetry chart
│       │       └── ResidualsView.qml             ← Per-channel residual chart
│       └── Sample/
│           ├── Sidebar/Advanced/Layout.qml       ← Sample polarization controls
│           └── MainContent/
│               └── CombinedView.qml              ← Sample channel-aware chart
└── Gui/
    └── SldChart.qml                              ← Shared SLD chart (component-aware mode)
```
