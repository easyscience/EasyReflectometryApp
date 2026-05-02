# Plan: Polarization-Specific GUI Elements

## Goal

Add QML layout support for polarized reflectometry workflows while keeping the first implementation GUI-focused. The UI should expose polarization channel visibility, channel-specific chart overlays, and SLD component visibility, with only thin hooks to backend properties and slots that can be implemented later.

The attached mockup [magnetic_reflectometry.png](magnetic_reflectometry.png) is the target direction for the Analysis tab:

- one main reflectivity chart with visible polarization channels overlaid;
- a lower panel with `SLD`, `Spin asymmetry`, and `Residuals` tabs;
- sidebar groups for experiment selection, polarization channel visibility, SLD component visibility, fittables, and fitting;
- no polarization correction controls in the analysis GUI.

The Sample tab needs the same channel-aware layout idea: the main reflectivity chart and SLD chart should be able to show multiple polarization channels/components at once.

## Existing Structure To Extend

The current Qt 6 UI already has most of the needed shape:

- [EasyReflectometryApp/Gui/Pages/Analysis/Layout.qml](EasyReflectometryApp/Gui/Pages/Analysis/Layout.qml) loads a single `CombinedView.qml` inside the Reflectivity tab and provides Basic/Extra sidebar columns.
- [EasyReflectometryApp/Gui/Pages/Analysis/MainContent/CombinedView.qml](EasyReflectometryApp/Gui/Pages/Analysis/MainContent/CombinedView.qml) uses a vertical `SplitView`: reflectivity chart on top, lower panel underneath.
- [EasyReflectometryApp/Gui/Pages/Analysis/MainContent/SldView.qml](EasyReflectometryApp/Gui/Pages/Analysis/MainContent/SldView.qml) already owns the lower `TabBar`/`StackLayout` for `SLD` and `Residuals`.
- [EasyReflectometryApp/Gui/Pages/Sample/MainContent/CombinedView.qml](EasyReflectometryApp/Gui/Pages/Sample/MainContent/CombinedView.qml) also uses a vertical `SplitView`: calculated reflectivity on top and `Gui.SldChart` underneath.
- [EasyReflectometryApp/Gui/SldChart.qml](EasyReflectometryApp/Gui/SldChart.qml) already dynamically creates SLD series per model and is the best place to add SLD component visibility once the data contract exists.
- [EasyReflectometryApp/Gui/Globals/BackendWrapper.qml](EasyReflectometryApp/Gui/Globals/BackendWrapper.qml) is the QML boundary for Python properties and slots. New QML should only call backend through this wrapper.
- [EasyReflectometryApp/Gui/Globals/Variables.qml](EasyReflectometryApp/Gui/Globals/Variables.qml) is the right place for GUI-only state such as legend visibility, channel colors, and temporary channel visibility defaults.

## UX Layout

### Analysis Tab

Keep the current `Analysis/Layout.qml` page structure and update only its contents.

Main content:

1. Top panel: channel-aware reflectivity chart.
   - Replace the current single calculated/measured pair in `Analysis/MainContent/CombinedView.qml` with dynamic series created from a channel list.
   - Keep the chart as one combined view, not four subplots.
   - Render measured data and calculated data for each visible channel with distinct style conventions:
     - channel color identifies `R++`, `R--`, `R+-`, `R-+`;
     - measured data uses markers or dotted style;
     - calculated data uses solid line style;
     - hidden channels remove or hide both measured and calculated series.
   - Keep existing chart toolbar behavior: legend, hover, pan/zoom, reset axes, logarithmic q-axis, and `R(q) x q^4` mode.
   - Add a `Stagger channels` checkbox (and reuse the existing multi-experiment staggering factor model) instead of inventing a separate `Vertical offset` concept. Since reflectivity is plotted as `log10(R)`, the stagger is implemented as an additive offset on log-Y (equivalent to a multiplicative factor on R). The backend returns raw values; QML applies the additive stagger on draw. The checkbox belongs in the polarization sidebar group.

2. Lower panel: extend `Analysis/MainContent/SldView.qml` from two tabs to three tabs.
   - `SLD`: existing SLD chart, updated to show selected SLD components.
   - `Spin asymmetry`: new chart component showing `(R++ - R--) / (R++ + R--)` vs q. Render measured points with propagated error bars and the calculated curve from day one; QML hides the measured trace when the backend returns empty measured/sigma arrays.
   - `Residuals`: extend the existing residual chart to draw one residual line per visible polarization channel, colored to match the channel legend, reusing the multi-experiment residual machinery with channel as the inner dimension. Do not collapse polarization residuals into a single combined curve in the first pass; a combined-curve toggle can be added later.
   - When `polarizationAvailable` is false, the lower panel falls back to the original two-tab layout (`SLD`, `Residuals`) and the `Spin asymmetry` tab is hidden, not just disabled.

Sidebar:

The current `Analysis/Sidebar/Basic/Layout.qml` only contains `Groups.Experiments` and `Groups.Fittables` (the `Fitting` group is registered separately, not inside this layout). The plan inserts the new groups between them.

1. Keep the current `Experiments` group at the top.
2. Add a new `PolarizationChannels.qml` group below `Experiments`.
   - Rows: `R++ (up-up)`, `R-- (down-down)`, `R+- (up-down)`, `R-+ (down-up)`.
   - Each row has a visibility checkbox, a color swatch, and a channel label.
   - Include a `Stagger channels` checkbox at the bottom of the group (see staggering note above).
   - Channels not available for any active experiment render disabled with a tooltip.
   - The group should collapse like existing `EaElements.GroupBox` sections.
   - The whole group is hidden when `polarizationAvailable` is false.
3. Add a new `SldComponents.qml` group below `PolarizationChannels`.
   - Rows: `Nuclear (rho_n)` and `Magnetic (rho_m)`.
   - Each row has a visibility checkbox, color swatch, and label.
   - The `Magnetic (rho_m)` row is disabled when no model has magnetic layers (driven by `polarizationSldComponents[i].available`).
   - The whole group is hidden when `polarizationAvailable` is false.
4. Keep `Fittables` (and the separately registered `Fitting`) below these groups, preserving the existing layout order.
5. Do not add correction controls. Polarization corrections stay in data reduction/import workflows, outside this analysis GUI.

### Sample Tab

Use the same visual language as Analysis but preserve the Sample workflow.

Main content:

1. Update `Sample/MainContent/CombinedView.qml` so the top calculated reflectivity chart can draw one line per visible polarization channel for the current model, or per `(model, channel)` if multiple models are visible.
2. Update the lower SLD chart so nuclear and magnetic SLD components can be displayed together.
3. Reuse the same channel and SLD component control state as Analysis when practical, so users do not have to reconfigure visibility on each tab.

Sidebar:

1. Keep current model/material/layer editing controls.
2. Add polarization display controls (`PolarizationChannelSelector` and `SldComponentSelector`) to the Advanced sidebar column (`Sample/Sidebar/Advanced/Layout.qml`), keeping the Basic sidebar focused on model/material/layer editing.
3. Avoid placing analysis-only fitting controls on the Sample tab.

## Proposed QML Components

Create small reusable components instead of duplicating channel rows in Analysis and Sample:

1. `Gui/Components/PolarizationChannelSelector.qml`
   - GroupBox containing the four channel rows and the stagger checkbox.
   - Properties:
     - `channelsModel`: list of channel metadata from `Globals.BackendWrapper.polarizationChannels`.
     - `selectedKeys`: list from `Globals.BackendWrapper.polarizationVisibleChannelKeys`.
     - `staggerEnabled`: bool from `Globals.BackendWrapper.polarizationStaggerEnabled`.
   - Emits/calls:
     - `Globals.BackendWrapper.polarizationSetChannelVisible(channelKey, checked)`.
     - `Globals.BackendWrapper.polarizationSetStaggerEnabled(checked)`.

2. `Gui/Components/SldComponentSelector.qml`
   - GroupBox containing nuclear and magnetic component rows.
   - Properties:
     - `componentsModel`: list from `Globals.BackendWrapper.polarizationSldComponents`.
     - `selectedKeys`: list from `Globals.BackendWrapper.polarizationVisibleSldComponentKeys`.
   - Emits/calls:
     - `Globals.BackendWrapper.polarizationSetSldComponentVisible(componentKey, checked)`.

3. `Gui/Components/PolarizationLegend.qml`
   - Optional helper for a compact chart legend when QtCharts built-in legend remains hidden.
   - Should support channel color, measured marker indicator, calculated line indicator, and component labels.

4. `Gui/Pages/Analysis/MainContent/SpinAsymmetryView.qml`
   - New chart component following the same toolbar/axis interaction pattern as `ResidualsView.qml`.
   - Reads data via `Globals.BackendWrapper.plottingGetSpinAsymmetryDataPoints(scopeOrModelIndex)` or an equivalent future slot.
   - Supports reset axes, hover tooltip, pan/zoom, and log q-axis.

5. Shared chart toolbar component: extract the repeated QtCharts toolbar/zoom/pan/legend behavior from `CombinedView.qml`, `SldChart.qml`, and `ResidualsView.qml` into a shared local component. This is scheduled as Phase 3a (prerequisite for Phase 3) so `SpinAsymmetryView.qml` can consume it directly instead of duplicating toolbar code into a fourth chart.

## BackendWrapper Contract

Add only QML-facing hooks in the first GUI pass. Python implementations can initially return mock/static data.

All new properties and functions MUST follow the existing defensive pattern used by `plottingIsMultiExperimentMode` in [Globals/BackendWrapper.qml](EasyReflectometryApp/Gui/Globals/BackendWrapper.qml): wrap `activeBackend.polarization.*` access in `try/catch` and return safe defaults (`false`, `[]`, `{}`) when the attribute is missing. The current `PyBackend` has no `polarization` object, and the QML must continue to load and render the non-polarized layout against today's backend without runtime errors.

Suggested properties on `Globals.BackendWrapper`:

```qml
readonly property bool polarizationAvailable: { try { return activeBackend.polarization.available || false } catch (e) { return false } }
readonly property var polarizationChannels: { try { return activeBackend.polarization.channels || [] } catch (e) { return [] } }
readonly property var polarizationVisibleChannelKeys: { try { return activeBackend.polarization.visibleChannelKeys || [] } catch (e) { return [] } }
readonly property bool polarizationStaggerEnabled: { try { return activeBackend.polarization.staggerEnabled || false } catch (e) { return false } }
readonly property real polarizationStaggerFactor: { try { return activeBackend.polarization.staggerFactor || 0.5 } catch (e) { return 0.5 } }
readonly property var polarizationSldComponents: { try { return activeBackend.polarization.sldComponents || [] } catch (e) { return [] } }
readonly property var polarizationVisibleSldComponentKeys: { try { return activeBackend.polarization.visibleSldComponentKeys || [] } catch (e) { return [] } }
```

Suggested slots/functions on `Globals.BackendWrapper` (each must guard against a missing `polarization` object):

```qml
function polarizationSetChannelVisible(channelKey, visible)
function polarizationSetVisibleChannelKeys(channelKeys)
function polarizationSetStaggerEnabled(value)
function polarizationSetStaggerFactor(value)
function polarizationSetSldComponentVisible(componentKey, visible)
function polarizationSetVisibleSldComponentKeys(componentKeys)

function polarizationGetExperimentChannels(experimentIndex)            // per-experiment subset of available channels
function plottingGetAnalysisChannelDataPoints(experimentIndex, channelKey)
function plottingGetSampleChannelDataPoints(modelIndex, channelKey)
function plottingGetSldComponentDataPoints(modelIndex, componentKey)
function plottingGetSpinAsymmetryDataPoints(experimentIndex)            // returns measured + sigma + calculated
function plottingGetPolarizationResidualDataPoints(experimentIndex, channelKey)
```

Note: `polarizationChannels` is the *union* of channels across all experiments (drives the legend/sidebar). Per-experiment availability comes from `polarizationGetExperimentChannels(experimentIndex)`, so unavailable channels render disabled in the sidebar and are never requested from the calculator.

Suggested signal forwarding:

```qml
signal polarizationDisplayChanged()
signal polarizationDataChanged()
```

The QML should connect to these signals to recreate series only when channel/component membership changes, and refresh existing series when only data values change.

Suggested channel metadata shape:

```js
{
    key: 'pp',
    label: 'R++',
    description: 'up-up',
    color: '#ef4444',
    enabled: true,
    hasMeasured: true,
    hasCalculated: true
}
```

Suggested SLD component metadata shape:

```js
{
    key: 'nuclear',
    label: 'Nuclear',
    symbol: 'rho_n',
    color: '#f59e0b',
    enabled: true,
    available: true   // false when no model exposes this component (e.g. magnetic w/o magnetic layers)
}
```

## Chart Series Plan

### Analysis Reflectivity Chart

In [Analysis/MainContent/CombinedView.qml](EasyReflectometryApp/Gui/Pages/Analysis/MainContent/CombinedView.qml) the existing chart already owns a full multi-experiment pipeline (`multiExperimentSeries`, `updateMultiExperimentSeries`, `MeasuredScatter.js` integration, log-axis recreation, `R(q) x q^4` mode, background/scale reference lines, and the `onMultiExperimentSelectionChanged` connection). Polarization MUST extend this pipeline rather than introduce a parallel `polarizationSeries` map; otherwise we end up with two competing series-management systems that disagree on log-axis recreation, OpenGL toggling, staggering, and reference lines.

Treat the series collection as a 2-D matrix `(experiment x channel)`:

1. Extend `multiExperimentSeries` so each entry stores a sub-map keyed by `channel.key`, each containing the measured/error/calculated series triplet that the existing code already creates per experiment.
2. Extend `updateMultiExperimentSeries()` to inner-loop over `polarizationGetExperimentChannels(experimentIndex)` filtered by `polarizationVisibleChannelKeys`, creating one triplet per `(experiment, channel)` pair. When `polarizationAvailable` is false the inner loop runs once with a synthetic single-channel entry so non-polarized projects keep today's exact behavior.
3. Reuse the existing log-axis recreation, OpenGL handling, and reference-line code paths unchanged.
4. Channel color and measured/calculated style conventions are applied per `(experiment, channel)` triplet. Channel identity drives the color and dash/marker style (measured = markers/dotted, calculated = solid line). In multi-experiment mode, experiments sharing the same channel use the same channel color and are distinguished by marker shape or dash pattern rather than hue modulation.
5. Apply staggering as an additive offset on log-Y per visible channel when `polarizationStaggerEnabled` is true, reusing the existing multi-experiment staggering factor (`polarizationStaggerFactor`).
6. On `polarizationDisplayChanged`, call `updateMultiExperimentSeries()` (the same function already used by multi-experiment changes), then reset axes.
7. On `polarizationDataChanged` or existing plot refresh signals, refresh data into existing series without recreation.

### Analysis SLD Chart

In `Gui/SldChart.qml` or a small wrapper around it:

1. Add a mode/property to switch from model-only series to component-aware series.
2. Create one line per visible SLD component, or per `(model, component)` if multiple models remain visible.
3. Read points from `plottingGetSldComponentDataPoints(modelIndex, componentKey)`.
4. Keep existing `reverseZAxis`, legend, tooltip, pan/zoom, and reset behavior.

### Spin Asymmetry Chart

Create `Analysis/MainContent/SpinAsymmetryView.qml` based on `ResidualsView.qml`:

1. Axes:
   - x-axis: q, linear/log controlled by `Globals.Variables.logarithmicQAxis`;
   - y-axis: spin asymmetry, typically bounded near `[-1, 1]` but still driven by backend min/max hooks later.
2. Data:
   - measured points with propagated error bars and a calculated curve, both from `plottingGetSpinAsymmetryDataPoints(experimentIndex)`;
   - the slot returns `{x, measured, sigma, calculated}` where `measured` and `sigma` are empty arrays when measured `R++`/`R--` are not present, in which case QML hides the measured trace.
3. Toolbar:
   - legend, hover, pan/zoom, reset axes, matching existing chart controls.

### Residuals Chart

Extend the existing residuals tab to draw one residual line per visible polarization channel (per active experiment when in multi-experiment mode), reusing the existing multi-experiment residual machinery in `ResidualsView.qml` with channel as the inner dimension. Each line is colored to match the channel legend in the main reflectivity chart. Use `plottingGetPolarizationResidualDataPoints(experimentIndex, channelKey)` per `(experiment, channel)` pair. Do not collapse polarization residuals into a single combined curve in the first pass; a `Combined residuals` toggle can be added later.

### Sample Reflectivity Chart

In `Sample/MainContent/CombinedView.qml`:

1. Add channel-aware series creation similar to Analysis but without measured data unless future backend data provides it.
2. Suggested first pass: one calculated line per visible channel for the current model.
3. If multiple models are active, use a predictable legend label such as `Model label - R++`; color is driven by channel identity, with models distinguished by dash pattern or marker shape.
4. Reuse `polarizationDisplayChanged` and `polarizationDataChanged` to avoid separate Sample-only state.

## State And Defaults

Add GUI defaults in `Globals/Variables.qml` only if they are purely visual fallback values:

- `readonly property var polarizationChannelColorPalette` for default channel colors;
- `readonly property var sldComponentColorPalette` for default nuclear/magnetic colors;
- optional fallback visibility arrays while backend hooks are mocked.

Prefer backend-owned state once the Python `polarization` object exists, so project loading can restore channel selections consistently.

Recommended default channel colors from the mockup:

- `R++`: red;
- `R--`: blue-grey;
- `R+-`: green;
- `R-+`: orange;
- `rho_n`: orange;
- `rho_m`: teal.

## Implementation Phases

### Phase 1: QML Skeleton And Mock Hooks

1. Add mock polarization properties/slots to [EasyReflectometryApp/Backends/MockBackend.qml](EasyReflectometryApp/Backends/MockBackend.qml) or a new mock singleton under `Backends/Mock`.
2. Expose the properties/slots in `Globals/BackendWrapper.qml` with the defensive `try/catch` fallback pattern described in the BackendWrapper Contract section, so the QML keeps working against today's `PyBackend` (which has no `polarization` object).
3. Add `PolarizationChannelSelector.qml` and `SldComponentSelector.qml`.
4. Insert the selector groups into `Analysis/Sidebar/Basic/Layout.qml` between `Groups.Experiments` and `Groups.Fittables`, hidden when `polarizationAvailable` is false.
5. Add the lower `Spin asymmetry` tab and placeholder `SpinAsymmetryView.qml`. Hide the tab when `polarizationAvailable` is false so non-polarized projects keep the original `SLD | Residuals` layout.
6. Have `SpinAsymmetryView.qml` self-register its chart view reference in `Component.onCompleted` (e.g. `Globals.References.pages.analysis.mainContent.spinAsymmetryView = chartView`), following the same pattern used by `SldView.qml` and `ResidualsView.qml`. This keeps multi-tab reset/zoom plumbing working with three tabs without modifying the static `References.qml` JSON.
7. Verify the UI loads with mock data and that toggles update chart visibility state.

Status after Phase 1 implementation (2026-05-02): completed QML skeleton and mock-hook work.

- Added `Backends/Mock/Polarization.qml`, registered it in `Backends/Mock/qmldir`, and exposed it from `Backends/MockBackend.qml`.
- Added defensive polarization properties, slots, plotting-data placeholders, and signal forwarding hooks in `Gui/Globals/BackendWrapper.qml`.
- Added reusable `Gui/Components/PolarizationChannelSelector.qml` and `Gui/Components/SldComponentSelector.qml`, with a `Gui.Components` `qmldir` module.
- Inserted the selector groups into `Analysis/Sidebar/Basic/Layout.qml` between `Experiments` and `Fittables`, hidden through `polarizationAvailable`.
- Added placeholder `Analysis/MainContent/SpinAsymmetryView.qml`, wired it into `SldView.qml`, and kept the non-polarized two-tab `SLD | Residuals` mapping intact when `polarizationAvailable` is false.
- Validation: `git diff --check` passed. VS Code QML diagnostics still report existing unresolved import-path warnings for project modules in this workspace; the newly added mock/backend and spin-asymmetry files report no syntax diagnostics from the editor.

### Phase 2: Analysis Chart Series

1. Update `Analysis/MainContent/CombinedView.qml` to create/refresh channel-specific measured and calculated series.
2. Preserve existing single/multi-experiment behavior while adding channel as the inner series dimension.
3. Update the custom legend to show visible polarization channels and measured/calculated style hints.
4. Wire vertical offset display mode.
5. Keep existing background/scale reference line behavior unless polarization-specific reference behavior is defined later.

Status after Phase 2 implementation (2026-05-02): completed Analysis reflectivity chart series work.

- Extended `Analysis/MainContent/CombinedView.qml` so polarized mode creates dynamic measured/calculated series per `(experiment, channel)` pair using `polarizationGetExperimentChannels`, `polarizationVisibleChannelKeys`, and `plottingGetAnalysisChannelDataPoints` through `Globals.BackendWrapper`.
- Preserved the existing non-polarized single-experiment and multi-experiment paths; `PyBackend` projects without `activeBackend.polarization` continue to use the original registered measured/calculated series.
- Wired `polarizationDisplayChanged` to recreate channel series and reset axes, and `polarizationDataChanged` to refresh existing channel series data without recreating them.
- Applied channel colors directly to both measured and calculated series; in polarized multi-experiment mode, experiments are distinguished by calculated-line dash pattern rather than hue modulation.
- Applied `polarizationStaggerEnabled` as an additive log-Y offset using `polarizationStaggerFactor`, keeping backend data raw.
- Updated the Analysis chart legend to show visible polarization channels plus measured/calculated style hints when polarized mode is active.
- Added mock analysis channel data in `Backends/Mock/Polarization.qml` so the Phase 2 chart path has visible synthetic series in mock mode.
- Validation: `git diff --check` passed. VS Code QML diagnostics still report the existing unresolved import-path cascade for project modules in this workspace; `Backends/Mock/Polarization.qml` reports no syntax diagnostics.

### Phase 3a: Shared Chart Toolbar Extraction (prerequisite for Phase 3)

Extract the repeated QtCharts toolbar/zoom/pan/legend behavior currently duplicated across `Analysis/MainContent/CombinedView.qml`, `Gui/SldChart.qml`, and `Analysis/MainContent/ResidualsView.qml` into a shared local component before adding `SpinAsymmetryView.qml`. Doing this first avoids duplicating the toolbar code into a fourth chart and keeps the three lower-tab charts visually consistent.

Status after Phase 3a implementation (2026-05-02): completed shared chart-control extraction.

- Added `Gui/Components/ChartToolbar.qml` and registered it in `Gui/Components/qmldir` for the common legend, hover, pan, zoom, and reset toolbar buttons.
- Added `Gui/Components/ChartMouseControls.qml` and registered it in `Gui/Components/qmldir` for shared box zoom, pan, and right-click reset mouse behavior.
- Replaced duplicated toolbar rows in `Analysis/MainContent/CombinedView.qml`, `Gui/SldChart.qml`, `Analysis/MainContent/ResidualsView.qml`, and `Analysis/MainContent/SpinAsymmetryView.qml`.
- Replaced duplicated lower-chart mouse interaction blocks in `Gui/SldChart.qml`, `Analysis/MainContent/ResidualsView.qml`, and `Analysis/MainContent/SpinAsymmetryView.qml`.
- Preserved the top Analysis chart behavior where toolbar mode changes propagate to the lower panel and reset also resets lower-panel axes.

### Phase 3: Lower Panel Charts

1. Extend `Gui/SldChart.qml` or wrap it for SLD component series.
2. Implement `SpinAsymmetryView.qml` chart behavior using mock/future backend data, including measured + sigma + calculated traces.
3. Update `ResidualsView.qml` to draw one residual line per visible polarization channel (per active experiment in multi-experiment mode) when `polarizationAvailable` is true.

Status after Phase 3 implementation (2026-05-02): completed lower-panel chart work.

- Updated `Gui/SldChart.qml` with a polarization-aware component mode. When `polarizationAvailable` is true, it creates SLD series per visible SLD component, or per `(model, component)` when multiple models are present, using `plottingGetSldComponentDataPoints` through `Globals.BackendWrapper`.
- Implemented `Analysis/MainContent/SpinAsymmetryView.qml` as a real chart with calculated curve, measured points, measured +/- sigma traces, custom legend, hover tooltip, log/linear q-axis support, reset axes, pan, and zoom.
- Updated `Analysis/MainContent/ResidualsView.qml` so polarized mode creates residual lines per visible `(experiment, channel)` using `plottingGetPolarizationResidualDataPoints`, with channel colors and experiment dash styles.
- Added mock lower-panel data in `Backends/Mock/Polarization.qml` for SLD components, spin asymmetry, and per-channel residuals.
- Validation: `git diff --check` passed. VS Code QML diagnostics report no errors for `ChartToolbar.qml`, `ChartMouseControls.qml`, `Gui/SldChart.qml`, `SpinAsymmetryView.qml`, or `Backends/Mock/Polarization.qml`; `CombinedView.qml` and `ResidualsView.qml` still report the known unresolved import-path cascade for project modules in this workspace.

### Phase 4: Sample Tab Layout

1. Add the shared polarization/Sld component selectors to the Sample Advanced sidebar (`Sample/Sidebar/Advanced/Layout.qml`).
2. Update `Sample/MainContent/CombinedView.qml` to draw channel-specific calculated reflectivity series.
3. Update the Sample lower SLD chart to show SLD components.
4. Confirm Analysis and Sample share visibility state consistently.

Status after Phase 4 implementation (2026-05-02): completed Sample tab layout work.

- Added `PolarizationChannelSelector` and `SldComponentSelector` to `Sample/Sidebar/Advanced/Layout.qml`, keeping the Sample Basic controls focused on model/material/layer editing.
- Updated `Sample/MainContent/CombinedView.qml` so polarized mode creates calculated reflectivity lines per visible `(model, channel)` using `plottingGetSampleChannelDataPoints` through `Globals.BackendWrapper`.
- Preserved the existing non-polarized Sample series path through `plottingGetSampleDataPointsForModel`.
- Reused `ChartToolbar` and `ChartMouseControls` on the Sample reflectivity chart, keeping top/lower chart pan-zoom and reset behavior synchronized.
- Confirmed the lower Sample SLD chart already uses `Gui.SldChart`, so the Phase 3 component-aware SLD rendering now applies to Sample and Analysis through shared visibility state.
- Added mock Sample channel data in `Backends/Mock/Polarization.qml` so the Sample channel-series path renders synthetic data in mock mode.
- Validation: `git diff --check` passed. VS Code QML diagnostics report no errors for `Sample/MainContent/CombinedView.qml`, `Sample/Sidebar/Advanced/Layout.qml`, or `Backends/Mock/Polarization.qml`; `Gui/SldChart.qml` still reports the known unresolved import-path cascade for project modules in this workspace.

### Phase 5: Python Backend Implementation Later

This plan intentionally defers scientific/backend behavior. Later backend work should implement:

1. a `polarization` backend object exposed from `PyBackend`;
2. channel metadata (including per-experiment availability via `polarizationGetExperimentChannels`) and persisted visibility state;
3. channel-specific calculated reflectivity data;
4. channel-specific measured data where available;
5. nuclear/magnetic SLD component data, including the `available` flag per component;
6. spin asymmetry data with measured, sigma, and calculated arrays;
7. per-channel polarization residuals via `plottingGetPolarizationResidualDataPoints(experimentIndex, channelKey)`;
8. project serialization for polarization display preferences (channel/component visibility, stagger settings). This is required, not optional: visibility toggles are useless if they do not survive save/load.

## Acceptance Checklist

- Analysis tab loads with the mockup layout: reflectivity chart, lower `SLD | Spin asymmetry | Residuals` tabs, and polarization sidebar groups.
- Channel checkboxes show/hide corresponding reflectivity series without changing tabs.
- SLD component checkboxes show/hide nuclear and magnetic SLD component lines; the magnetic row is disabled when no model has magnetic layers.
- Stagger checkbox changes only display spacing (additive offset on log-Y) and does not imply a correction workflow.
- Sample tab can show multiple polarization channels in the main reflectivity chart and SLD components in the SLD chart.
- Non-polarized projects load and show the original single-channel behavior, with the Polarization and SLD-component sidebar groups hidden and the lower panel reverting to the original `SLD | Residuals` two-tab layout (no `Spin asymmetry` tab).
- Polarization residuals show one residual line per visible channel (per active experiment in multi-experiment mode), colored to match the channel legend.
- Existing chart controls still work: legend, hover tooltip, pan/zoom, reset axes, log q-axis, reverse SLD z-axis, and `R(q) x q^4`.
- The polarization-aware reflectivity chart continues to use the existing multi-experiment series pipeline, log-axis recreation, OpenGL toggling, and background/scale reference lines.
- QML calls new Python-facing functionality only through `Globals.BackendWrapper`, and all new wrapper accessors guard `activeBackend.polarization.*` with `try/catch` so the GUI works against the current `PyBackend`.

## Open Decisions

- Whether channel visibility is project state, session GUI state, or both. Recommended: project state (persisted) with `Variables.qml` providing first-load defaults only.
- Whether Sample should show `(model, channel)` combinations for all models immediately, or only for the current model in the first pass. Recommended: current model only in v1, full `(model, channel)` matrix later.
- Stagger semantics. Recommended: backend returns raw values, QML applies an additive offset on log-Y using `polarizationStaggerFactor`, reusing the existing multi-experiment staggering machinery.
- Whether spin asymmetry should initially show calculated-only data or include measured points. Recommended: include measured + propagated sigma from day one; QML hides the measured trace when arrays are empty.
- Whether channel colors should be user-editable later or fixed to standard polarization colors. Recommended: fixed standard palette in v1, user-editable later.
