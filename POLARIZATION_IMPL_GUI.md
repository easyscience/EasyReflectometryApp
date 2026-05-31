# Polarization GUI Implementation Plan — Experiment & Analysis Tabs

> Generated: 2026-05-29 — Plan for wiring the polarization controls (currently driven by the
> Mock backend) into the live `EasyReflectometryApp/Gui` for **polarized datasets** in the
> **Experiment** and **Analysis** tabs. Companion to `POLARIZATION_IMPL.md`.

---

## 0. TL;DR — Can we move the mockup to the real code?

**The QML/GUI layer is already real and is *not* a mockup.** What is mock is only the *data
source* — `Backends/Mock/Polarization.qml` (synthetic curves) exposed through
`MockBackend.qml` as the `polarization` object.

- The reusable components (`PolarizationChannelSelector`, `SldComponentSelector`,
  `ChartToolbar`, `ChartMouseControls`), the `BackendWrapper.qml` polarization API
  (properties / slots / signals, all `try/catch`-guarded), and the **Analysis** tab
  (sidebar + channel-aware chart + 3-tab lower panel with Spin Asymmetry & per-channel
  Residuals) are **already implemented and live** in `Gui/`.
- The **Sample** tab is also already wired (Advanced sidebar selectors + channel-aware
  calculated chart). This was the original prototype target.
- The **Experiment** tab has **no polarization wiring at all** today.

So "moving the mockup to the real code" splits into two independent tracks:

1. **GUI track (this document, in `Gui/`):** the Experiment tab needs the same channel-aware
   treatment the Analysis tab already has, and the Analysis tab needs a small data-contract
   addition. Everything here works *today* against the Mock backend.
2. **Backend track (out of scope here, see `POLARIZATION_IMPL.md` §4):** to drive the GUI
   from real data, `PyBackend` must grow a `polarization` object
   (`Backends/Py/polarization.py`) matching the QML contract, plus the `reflectometry-lib`
   changes (channel-specific reflectivity API, magnetic layer params, channel-aware measured
   data, serialization). Until that exists, `polarizationAvailable` stays `false` for the
   real backend and the app behaves exactly as before (graceful degradation via `try/catch`).

**Verdict:** Yes — the GUI work for Experiment + Analysis can proceed now against the Mock
backend and is purely additive. It does not require the Python backend to land first, because
the `BackendWrapper` guards already make every polarization call a no-op when the active
backend lacks a `polarization` object.

---

## 1. Current State Inventory

| Area | File | Polarization state |
|---|---|---|
| Mock data source | `Backends/Mock/Polarization.qml` | ✅ Complete (4 channels, 2 SLD components, all data fns) |
| Mock exposure | `Backends/MockBackend.qml:17` | ✅ `property var polarization: Backend.Polarization` |
| Wrapper API | `Gui/Globals/BackendWrapper.qml:567–720` | ✅ Complete, `try/catch`-guarded |
| Channel selector | `Gui/Components/PolarizationChannelSelector.qml` | ✅ Reusable; self-hides via `polarizationAvailable` |
| SLD selector | `Gui/Components/SldComponentSelector.qml` | ✅ Reusable |
| **Analysis** sidebar | `Gui/Pages/Analysis/Sidebar/Advanced/Layout.qml:17–19` | ✅ Both selectors mounted |
| **Analysis** main chart | `Gui/Pages/Analysis/MainContent/CombinedView.qml` | ✅ Channel-aware (`isPolarizationMode`) |
| **Analysis** lower panel | `.../SldView.qml`, `SpinAsymmetryView.qml`, `ResidualsView.qml` | ✅ 3 tabs; Spin Asymmetry hidden when not polarized |
| **Sample** sidebar | `Gui/Pages/Sample/Sidebar/Advanced/Layout.qml:13–15` | ✅ Both selectors mounted |
| **Sample** main chart | `Gui/Pages/Sample/MainContent/CombinedView.qml` | ✅ Channel-aware calculated |
| **Experiment** sidebar | `Gui/Pages/Experiment/Sidebar/{Basic,Advanced}/Layout.qml` | ❌ None |
| **Experiment** main chart | `Gui/Pages/Experiment/MainContent/ExperimentView.qml` | ❌ None (measured-only, multi-experiment) |

> Note: `POLARIZATION_IMPL.md` §2.5 describes the selectors living in the Analysis *Basic*
> sidebar; in the live code they are in the *Advanced* sidebar of Analysis and Sample. This
> plan follows the live code.

### Why Experiment + Analysis (and not Sample) for "datasets"

A *dataset* is **measured** data. Measured polarized data (the `pp / mm / pm / mp` spin
channels) is loaded and inspected in the **Experiment** tab and fit in the **Analysis** tab.
The **Sample** tab is model-only (calculated reflectivity + SLD), so its polarization wiring
is about the model, not the dataset. The Sample wiring already exists and is left as-is; this
plan focuses on the two dataset-facing tabs.

---

## 2. Data-Contract Gap

The Mock `Polarization.qml` exposes per-channel data via:

- `getAnalysisChannelDataPoints(expIndex, channelKey)` → `{x, measured, calculated}` — **no error bounds**.
- `getSampleChannelDataPoints(modelIndex, channelKey)` → `{x, y}` (calculated only).
- `getSldComponentDataPoints`, `getSpinAsymmetryDataPoints`, `getPolarizationResidualDataPoints`.

The **Experiment** chart (`ExperimentView.qml`) renders measured scatter **plus error
bounds** and consumes points shaped as `{x, y, errorUpper, errorLower}` from
`plottingGetExperimentDataPoints(index)` (see `Backends/Py/plotting_1d.py:631`). There is
**no channel-aware equivalent** today.

**Required new contract method** (mock + wrapper + eventual Py backend):

```
getExperimentChannelDataPoints(experimentIndex, channelKey)
    -> [ { x, y, errorUpper, errorLower }, ... ]   // log10, R(q)·q⁴-aware, matching getExperimentDataPoints
```

This mirrors `getExperimentDataPoints` but per channel, so the Experiment chart can stagger /
color per channel exactly like the Analysis chart does.

---

## 3. Plan — Experiment Tab (the new work)

Model the Experiment changes on the existing Analysis `CombinedView.qml` polarization path
(`isPolarizationMode`, `visibleChannelsForExperiment`, `createExperimentSeries`,
`populateExperimentSeries`, `staggeredY`, the polarization legend, and the
`onPolarizationDisplayChanged` / `onPolarizationDataChanged` connections).

### 3.1 Sidebar — add the channel selector

**File:** `Gui/Pages/Experiment/Sidebar/Advanced/Layout.qml`

Add `GuiComponents.PolarizationChannelSelector {}` above `Groups.PlotControl {}` and the
`Gui.Components` / `Gui.Globals` imports. Do **not** add `SldComponentSelector` — there is no
SLD profile in the Experiment tab.

- The selector already self-hides when `polarizationAvailable` is `false`
  (`PolarizationChannelSelector.qml:14`), so non-polarized projects see no change.
- The "Stagger channels" checkbox is built into the selector; no extra control needed.

> Placement decision: Advanced sidebar, for consistency with Analysis/Sample. (If product
> wants channel selection to be more prominent for polarized data, it can move to
> `Sidebar/Basic/Layout.qml` — both are one-line mounts.)

### 3.2 Main chart — channel-aware measured series

**File:** `Gui/Pages/Experiment/MainContent/ExperimentView.qml`

This chart currently has two modes: single-experiment (scatter + 2 error lines) and
multi-experiment (per-experiment scatter + dashed error bounds). Add a **polarization mode**
as the Analysis chart does:

1. Add `property bool isPolarizationMode: Globals.BackendWrapper.polarizationAvailable`.

   > **Gating on measured channels (Issue #5):** Unlike the Analysis tab (which shows both
   > measured and calculated), the Experiment tab only renders measured data. If
   > `polarizationAvailable` is `true` but no channels have `hasMeasured === true`,
   > polarization mode is meaningless for this tab. Consider gating more narrowly:
   > ```js
   > property bool isPolarizationMode: {
   >     if (!Globals.BackendWrapper.polarizationAvailable) return false
   >     var channels = Globals.BackendWrapper.polarizationGetExperimentChannels(
   >         Globals.BackendWrapper.analysisExperimentsCurrentIndex
   >     ) || []
   >     for (var i = 0; i < channels.length; i++) {
   >         if (channels[i].hasMeasured) return true
   >     }
   >     return false
   > }
   > ```
   > This prevents the channel selector and legend from appearing when the backend claims
   > polarization support but the current experiment has no per-channel measured data.
   >
   > Note: the current-experiment index is `Globals.BackendWrapper.analysisExperimentsCurrentIndex`
   > (`BackendWrapper.qml:225`) — the same property ExperimentView already uses (e.g. lines 30,
   > 316). There is no `plottingCurrentExperimentIndex`. Also note this is a plain property
   > binding: it re-evaluates when the experiment index changes but **not** on
   > `polarizationDisplayChanged`. That is acceptable because per-experiment channel
   > availability (`hasMeasured`) is static; channel *visibility* toggles are handled
   > separately by the `onPolarizationDisplayChanged` connection.
2. Add a `Connections { target: Globals.BackendWrapper }` block handling
   `onPolarizationDisplayChanged` (→ `updateMultiExperimentSeries()` + reset-axes timer) and
   `onPolarizationDataChanged` (→ refresh data into existing series, or
   `plottingRefreshExperiment()` when not in polarization mode).

   > **`refreshDynamicSeriesData()` helper (Issue #2):** The `onPolarizationDataChanged`
   > handler must call a `refreshDynamicSeriesData()` function when in polarization mode
   > (exactly as Analysis `CombinedView.qml` does). This helper iterates
   > `multiExperimentSeries` and calls `populateExperimentSeries()` on each entry, pulling
   > fresh per-channel data. Without this helper, `onPolarizationDataChanged` has no
   > channel-aware refresh path. Add it alongside `populateExperimentSeries()`:
   > ```js
   > function refreshDynamicSeriesData() {
   >     for (var i = 0; i < multiExperimentSeries.length; i++) {
   >         populateExperimentSeries(multiExperimentSeries[i])
   >     }
   > }
   > ```
   >
   > **Reset-axes timer (Issue #8):** Reuse the existing `experimentResetAxesTimer`
   > (already defined at `ExperimentView.qml:249`) rather than creating a new timer. The
   > Experiment tab has no lower panel, so a single chart-level timer is sufficient.
   >
   > **Signal connection initialization (Issue #10):** Verify that
   > `BackendWrapper.connectPolarizationSignals()` is called before ExperimentView
   > initializes. In the current architecture, `BackendWrapper` connects polarization
   > signals internally when the backend is set. No extra `Component.onCompleted` wiring
   > is needed in ExperimentView — the `Connections` block above suffices — but confirm
   > this during implementation by tracing that `polarizationDisplayChanged` fires when
   > the `PolarizationChannelSelector` toggles a channel.
3. Extend `updateMultiExperimentSeries()` with a polarization branch (before the existing
   multi-experiment branch): for each experiment in scope (current experiment in single mode,
   or `plottingIndividualExperimentDataList` in multi mode), inner-loop over
   `visibleChannelsForExperiment(expIndex)` and create one measured+error series triplet per
   visible channel, colored by `channel.color`.
4. Add `visibleChannelsForExperiment(expIndex)` and `visiblePolarizationChannels()` helpers
   (copy from `CombinedView.qml:300–337`), filtering
   `polarizationGetExperimentChannels(expIndex)` by `polarizationVisibleChannelKeys` and
   `channel.enabled` / `channel.hasMeasured`.
5. In `createExperimentSeries(...)` / `populateExperimentSeries(...)`, when in polarization
   mode pull data from the **new** `plottingGetExperimentChannelDataPoints(expIndex,
   channelKey)` instead of `plottingGetExperimentDataPoints(expIndex)`, and apply a
   `staggeredY(value, channelIndex)` offset using `polarizationStaggerEnabled` /
   `polarizationStaggerFactor` (copy `CombinedView.qml:426–431`).
   - Keep error-bound series (`errorUpper`/`errorLower`) per channel; they already exist in
     the Experiment multi-experiment path.
   - Reuse `MeasuredScatter.create(...)` for the markers, exactly as the existing code does.

   > **Signature (Issue #3):** Extend `createExperimentSeries` to accept optional
   > `channel` / `channelIndex` parameters (defaulting to `undefined` / `0`), matching the
   > pattern in Analysis `CombinedView.qml:364`:
   > ```js
   > function createExperimentSeries(expIndex, expName, color, channel, channelIndex) {
   >     var usePolarizationChannel = isPolarizationMode && channel && channel.key !== 'default'
   >     var seriesColor = usePolarizationChannel ? (channel.color || color) : color
   >     var channelSuffix = usePolarizationChannel ? ` - ${channel.label || channel.key}` : ''
   >     // ... existing series creation, but names include channelSuffix, colors use seriesColor ...
   > }
   > ```
   > The existing call sites `createExperimentSeries(expData.index, expData.name, expData.color)`
   > continue to work unchanged when `isPolarizationMode` is `false` because `channel` is
   > `undefined` and the non-polarization path is taken.
   >
   > **Staggering must apply to all three series (Issue #11):** In polarization mode,
   > `populateExperimentSeries` must apply `staggeredY()` to `point.y`, `point.errorUpper`,
   > **and** `point.errorLower` — not just the measured scatter. The error-bound lines must
   > shift by the same per-channel offset to stay aligned with their markers.
6. Add a polarization branch to `recreateForLogMode()` and `recreateSeriesForCurrentMode()`
   so log/linear axis switches and marker-style changes rebuild channel series.
7. Add a polarization legend block to the existing legend `Rectangle` (copy the
   "Polarization channels:" `Column` from `CombinedView.qml:609–657`), shown when
   `isPolarizationMode`.

**Guarding:** every branch must fall through to today's behavior when `isPolarizationMode`
is `false`, so non-polarized projects are byte-for-byte unaffected.

### 3.2.8 Staggering conflict resolution (Issues #1, #12, #13)

ExperimentView already has a multi-experiment staggering system driven by
`Globals.Variables.useStaggeredPlotting` and `Globals.Variables.staggeringFactor`
(`ExperimentView.qml:127–165`). This system computes per-experiment Y-offsets based on
each experiment's data range and applies them in `populateExperimentSeries`. The new
polarization staggering (`polarizationStaggerEnabled` / `polarizationStaggerFactor`)
operates per-**channel** and must coexist with the multi-experiment system.

**Rule:** When `isPolarizationMode` is `true`, the existing `useStaggeredPlotting`
staggering is **suppressed** and only `polarizationStaggerEnabled` applies. Rationale:
channel staggering already provides visual separation between experiments (each
experiment's channels are grouped and offset); layering both staggerings produces
illegible charts.

**Changes required:**

1. **`populateExperimentSeries`:** When `isPolarizationMode`, skip the existing
   `useStaggeredPlotting` / `staggeringFactor` Y-offset calculation (lines 530–560) and
   use `staggeredY(value, channelIndex)` exclusively.

2. **`adjustAxisForStaggering()` (Issue #12):** This function (`ExperimentView.qml:195`)
   currently scans `multiExperimentSeries[i].measuredSerie` to compute Y-axis bounds.
   In polarization mode, it must also account for channel-staggered data — the
   `staggeredY` offsets can push points far from their unstaggered positions. Update
   the function to iterate over all series in `multiExperimentSeries` and apply the
   same `staggeredY` logic when computing `allMinY` / `allMaxY`. Call
   `adjustAxisForStaggering()` from `updateMultiExperimentSeries()` after all
   polarization series are created.

3. **Existing staggering watchers (Issue #13):** The watchers on
   `onUseStaggeredPlottingChanged` (`ExperimentView.qml:150`) and `onStaggeringFactorChanged`
   (`ExperimentView.qml:167`) call `populateExperimentSeries` and
   `adjustAxisForStaggering`. Add an early-return guard:
   ```js
   onUseStaggeredPlottingChanged: {
       if (isPolarizationMode) return  // polarization uses its own stagger system
       // ... existing logic ...
   }
   onStaggeringFactorChanged: {
       if (isPolarizationMode) return
       // ... existing logic ...
   }
   ```
   The same guard applies to the `Connections` block on
   `Globals.Variables.onStaggeringFactorChanged` (`ExperimentView.qml:183`).

### 3.3 No lower panel for Experiment

The Experiment tab has a single chart (no SLD / residual / spin-asymmetry panel). Spin
asymmetry and per-channel residuals stay in the **Analysis** tab where calculated data
exists. Do **not** add a lower panel to Experiment.

---

## 4. Plan — Analysis Tab (already wired; verify + one addition)

The Analysis tab is functionally complete. Required work is limited to:

1. **Verify** the channel-aware chart, the 3-tab lower panel, and the Advanced-sidebar
   selectors render correctly against the Mock backend (they do today).
2. **No structural change needed.** The Analysis chart already uses
   `plottingGetAnalysisChannelDataPoints` for measured+calculated per channel.
3. Optional consistency: if §2's `getExperimentChannelDataPoints` is added, confirm the
   Analysis path is unaffected (it uses the analysis method, not the experiment method).

So the Analysis tab is effectively a "confirm and regression-test" item, not new
development.

---

## 5. Mock Backend Additions

**File:** `Backends/Mock/Polarization.qml`

Add one function to satisfy §2's new contract (synthetic measured data with error bounds):

```qml
function getExperimentChannelDataPoints(experimentIndex, channelKey) {
    // reuse the channelOffsets pattern from getAnalysisChannelDataPoints,
    // but emit { x, y, errorUpper, errorLower } (log10-style) so ExperimentView
    // can draw markers + dashed error bounds per channel.
}
```

No other mock changes are required — channels, SLD components, stagger state, and signals
already exist.

---

## 6. BackendWrapper Addition

**File:** `Gui/Globals/BackendWrapper.qml`

Add one guarded wrapper next to the existing polarization slots (~line 705), mirroring
`plottingGetAnalysisChannelDataPoints`:

```qml
function plottingGetExperimentChannelDataPoints(experimentIndex, channelKey) {
    try {
        return activeBackend.polarization.getExperimentChannelDataPoints(experimentIndex, channelKey)
    } catch (e) {
        console.warn("plottingGetExperimentChannelDataPoints failed:", e)
        return []
    }
}
```

The `polarizationDisplayChanged` / `polarizationDataChanged` signals and
`connectPolarizationSignals()` already exist and are reused by the Experiment chart — no new
signal wiring needed.

---

## 7. Backend Dependency (the actual "real data" switch)

The GUI work above lights up against the **Mock** backend immediately. To drive Experiment +
Analysis from **real** polarized data, the following must land (tracked in
`POLARIZATION_IMPL.md` §4.2–4.3 — out of scope for `Gui/` but listed here as the blocking
dependency):

1. `Backends/Py/polarization.py` — a `QObject` exposed from `PyBackend` as
   `@Property('QVariant', constant=True) def polarization(...)`, matching the QML contract
   **including the new `getExperimentChannelDataPoints`**.
2. Channel metadata with **per-experiment availability** (`getExperimentChannels`) and
   persisted visibility / stagger state.
3. Channel-specific measured data grouping in `reflectometry-lib` (the data layer is
   currently polarization-agnostic) + channel-specific calculated reflectivity API.
4. **Capability gating:** expose `available = true` only when the active calculator supports
   magnetism (refl1d). For refnx / bornagain keep `polarizationAvailable = false` so the
   selectors and channel modes never appear.
5. Project serialization for channel/component visibility, stagger, and magnetic layer params.

Until (1) exists, the real backend simply returns `false`/empty through the `try/catch`
guards and the Experiment/Analysis tabs behave as they do today.

---

## 8. File-by-File Change List

| # | File | Change | New? |
|---|---|---|---|
| 1 | `Backends/Mock/Polarization.qml` | Add `getExperimentChannelDataPoints()` | edit |
| 2 | `Gui/Globals/BackendWrapper.qml` | Add `plottingGetExperimentChannelDataPoints()` guard | edit |
| 3 | `Gui/Pages/Experiment/Sidebar/Advanced/Layout.qml` | Mount `PolarizationChannelSelector`; add imports | edit |
| 4 | `Gui/Pages/Experiment/MainContent/ExperimentView.qml` | Add polarization mode (series, helpers, legend, signal connections, log/marker rebuild) | edit |
| 5 | (later, backend) `Backends/Py/polarization.py` | Real polarization object incl. `getExperimentChannelDataPoints` | new |

No new QML files are required for the Experiment tab — the selector and chart component
already exist and are reused.

---

## 9. Verification

1. **Mock, non-polarized regression:** with `polarizationAvailable` forced `false`, confirm
   Experiment + Analysis tabs are visually identical to current `master` (no selectors, no
   channel series).
2. **Mock, polarized:** with the Mock backend active, confirm:
   - Experiment Advanced sidebar shows "Polarization channels" with 4 rows + stagger.
   - Toggling channels adds/removes per-channel measured series (correct colors) in the
     Experiment chart; the `mp` channel (mock `enabled:false`) stays disabled.
   - Stagger checkbox offsets channels on the log-Y chart.
   - Log/linear q-axis toggle and marker-style change rebuild channel series correctly.
   - Analysis tab unchanged (channel chart, Spin Asymmetry tab, per-channel Residuals).
3. **Single vs multi-experiment:** verify both modes in the Experiment chart with channels
   visible.
4. Run the app via the project's run path and eyeball both tabs (see `/run`).

---

## 10. Open Questions

1. **Sidebar placement** for the Experiment channel selector — Advanced (consistency, this
   plan's default) vs Basic (prominence for polarized data)?
2. **Error bounds per channel** — render dashed error-bound lines per channel (as
   multi-experiment mode does now) or markers-only to avoid clutter when many channels are
   visible?
3. Should the Experiment tab share the exact `visibleChannelKeys` / `staggerEnabled` state
   with Analysis (it does, since both read the same `BackendWrapper` → `polarization`
   object), or have independent per-tab display state? Current design = shared.
