# Bayesian (BUMPS-DREAM) Analysis in EasyReflectometryApp — GUI Integration Plan

This document plans the integration of the Bayesian DREAM sampling pipeline already
implemented in `reflectometry-lib` (`MultiFitter.sample()`, see
[reflectometry-lib/BAYESIAN_IN_ERL.md](../reflectometry-lib/BAYESIAN_IN_ERL.md))
into the EasyReflectometryApp Qt/QML GUI.

The library-side API is a fixed input:

```python
MultiFitter.sample(
    data: sc.DataGroup,
    samples: int = 10000,
    burn: int = 2000,
    thin: int = 10,
    chains: int | None = None,        # alias for population
    population: int | None = None,    # BUMPS DREAM `pop`
    seed: int | None = None,
    objective: str | None = None,
) -> dict   # {'draws', 'param_names', 'state', 'logp'}
```

It requires that the underlying minimizer is a BUMPS instance (i.e. the model
must be switched to `AvailableMinimizers.Bumps*` before `.sample()` is called).

---

## 1. UX Overview

### 1.1 Selecting the method

Add a new entry **`BUMPS-DREAM (Bayesian)`** to the existing combobox in
[Minimizer.qml](EasyReflectometryApp/Gui/Pages/Analysis/Sidebar/Advanced/Groups/Minimizer.qml).

The combobox model is currently the list of `AvailableMinimizers.name` values
exposed by [logic/minimizers.py](EasyReflectometryApp/Backends/Py/logic/minimizers.py).
We do **not** add `Bumps_dream` to the `AvailableMinimizers` enum (per the
core/library design decision in
[BAYESIAN_IN_ERL.md](../reflectometry-lib/BAYESIAN_IN_ERL.md)). Instead the
GUI prepends a **virtual entry** that the backend recognises as "use the
classical BUMPS minimizer for the underlying optimiser, but invoke
`MultiFitter.sample()` instead of `MultiFitter.fit()` when the user presses
*Start fitting*."

### 1.2 Mode-conditional controls

When `BUMPS-DREAM (Bayesian)` is selected:

- Hide the existing `Tolerance` and `Max evaluations` text fields (they have no
  meaning for DREAM).
- Show a new sub-group with four text fields, all bound to `int` properties on
  the backend:

  | Label              | Default | Backend property            | Library kwarg |
  |--------------------|--------:|-----------------------------|---------------|
  | `Samples`          |  10000  | `bayesianSamples`           | `samples`     |
  | `Burn-in Steps`    |   2000  | `bayesianBurnIn`            | `burn`        |
  | `Population`       |     10  | `bayesianPopulation`        | `population`  |
  | `Thinning`         |      1  | `bayesianThinning`          | `thin`        |

  (Optional, future: `Seed`. Out of scope for the first iteration unless
  reproducibility is requested.)

When any other minimizer is selected the new group is hidden and the original
classical-fit layout is restored unchanged.

### 1.3 Running

The existing **Start fitting** button (`fittingStartStop` slot) is reused. The
button label and the `FitStatusDialog` strings stay generic; the
`fitProgressMessage` switches to *"Sampling… (this may take several minutes)"*
when the Bayesian mode is active.  DREAM does not support a per-iteration
progress callback, so the progress bar in the fit dialog is set to an
**indeterminate** (bouncing) mode while sampling is in progress — this is
controlled by a new `bayesianResultAvailable`-related flag on the backend that
the QML dialog reads:

```qml
// In FitStatusDialog.qml — progress bar binding
ProgressBar {
    id: fitProgressBar
    indeterminate: Globals.BackendWrapper.analysisIsBayesianSelected
                 && Globals.BackendWrapper.analysisFittingRunning
    // ...existing value / visible bindings...
}
```

The fitting logic's `prepare_for_threaded_fit` already sets
`_fit_running_message = 'Fitting…'`.  Add a parallel method
`prepare_for_threaded_sample()` that sets `_fit_running_message = 'Sampling…
(this may take several minutes)'` so the message is ready before the worker
starts.

When sampling completes:

- The classical chi² display is replaced by a Bayesian summary
  (acceptance rate, R-hat, effective sample size — all available from the
  returned `state` object).
- The reflectivity chart is overlaid with a posterior-predictive band
  (see §5).
- A new *Bayesian Results* main-content tab becomes available next to the
  existing reflectivity view (see §6).

---

## 2. QML Changes

### 2.1 [Minimizer.qml](EasyReflectometryApp/Gui/Pages/Analysis/Sidebar/Advanced/Groups/Minimizer.qml)

```qml
EaElements.GroupBox {
    title: qsTr("Minimization method")
    icon: 'level-down-alt'

    EaElements.GroupRow {
        EaElements.ComboBox {
            id: minimizerCombo
            model: Globals.BackendWrapper.analysisMinimizersAvailable
            // Component.onCompleted unchanged (default = Bumps_simplex)
            onCurrentIndexChanged:
                Globals.BackendWrapper.analysisSetMinimizerCurrentIndex(currentIndex)
        }

        // Existing Tolerance / Max evaluations fields, hidden in Bayesian mode
        EaElements.TextField {
            visible: !Globals.BackendWrapper.analysisIsBayesianSelected
            // ...existing tolerance binding...
        }
        EaElements.TextField {
            visible: !Globals.BackendWrapper.analysisIsBayesianSelected
            // ...existing max-iterations binding...
        }
    }

    // New: Bayesian-only controls
    EaElements.GroupRow {
        visible: Globals.BackendWrapper.analysisIsBayesianSelected

        EaElements.TextField {
            text: Globals.BackendWrapper.bayesianSamples
            onAccepted: { Globals.BackendWrapper.bayesianSetSamples(parseInt(text)); focus = false }
            EaElements.Label { text: qsTr("Samples") }
        }
        EaElements.TextField {
            text: Globals.BackendWrapper.bayesianBurnIn
            onAccepted: { Globals.BackendWrapper.bayesianSetBurnIn(parseInt(text)); focus = false }
            EaElements.Label { text: qsTr("Burn-in") }
        }
        EaElements.TextField {
            text: Globals.BackendWrapper.bayesianPopulation
            onAccepted: { Globals.BackendWrapper.bayesianSetPopulation(parseInt(text)); focus = false }
            EaElements.Label { text: qsTr("Population") }
        }
        EaElements.TextField {
            text: Globals.BackendWrapper.bayesianThinning
            onAccepted: { Globals.BackendWrapper.bayesianSetThinning(parseInt(text)); focus = false }
            EaElements.Label { text: qsTr("Thinning") }
        }
    }
}
```

### 2.2 [BackendWrapper.qml](EasyReflectometryApp/Gui/Globals/BackendWrapper.qml)

Add forwarding properties / functions:

```qml
readonly property bool analysisIsBayesianSelected: activeBackend.analysis.isBayesianSelected

readonly property int bayesianSamples:    activeBackend.analysis.bayesianSamples
readonly property int bayesianBurnIn:     activeBackend.analysis.bayesianBurnIn
readonly property int bayesianPopulation: activeBackend.analysis.bayesianPopulation
readonly property int bayesianThinning:   activeBackend.analysis.bayesianThinning

function bayesianSetSamples(v)    { activeBackend.analysis.setBayesianSamples(v) }
function bayesianSetBurnIn(v)     { activeBackend.analysis.setBayesianBurnIn(v) }
function bayesianSetPopulation(v) { activeBackend.analysis.setBayesianPopulation(v) }
function bayesianSetThinning(v)   { activeBackend.analysis.setBayesianThinning(v) }

readonly property var bayesianPosterior: activeBackend.analysis.bayesianPosterior
readonly property bool bayesianResultAvailable: activeBackend.analysis.bayesianResultAvailable
```

Mirror entries are required in the Mock backend so the QML does not error in
mock mode.

---

## 3. Python Backend Changes

### 3.1 [logic/minimizers.py](EasyReflectometryApp/Backends/Py/logic/minimizers.py)

Add a virtual sentinel value to the front of the displayed list:

```python
BAYESIAN_LABEL = 'BUMPS-DREAM (Bayesian)'

class Minimizers:
    def __init__(self, project_lib):
        # ... existing filtering of LMFit / Bumps / DFO ...
        self._bayesian_index = 0
        self._list_available_minimizers = [None] + self._list_available_minimizers
        # `None` represents the Bayesian sentinel

    def minimizers_available(self) -> list[str]:
        return [BAYESIAN_LABEL if m is None else m.name
                for m in self._list_available_minimizers]

    def is_bayesian_selected(self) -> bool:
        return self._list_available_minimizers[self._minimizer_current_index] is None

    def set_minimizer_current_index(self, new_value: int) -> bool:
        if new_value == self._minimizer_current_index:
            return False
        self._minimizer_current_index = new_value
        entry = self._list_available_minimizers[new_value]
        if entry is None:
            # Bayesian mode: ensure underlying engine is Bumps for sample()
            self._project_lib.minimizer = AvailableMinimizers.Bumps_simplex
        else:
            self._project_lib.minimizer = entry
        return True

    def selected_minimizer_enum(self):
        """Return the AvailableMinimizers enum for the currently selected minimizer.

        Falls back to ``Bumps_simplex`` when the Bayesian sentinel (``None``)
        is selected, so callers that do not check ``is_bayesian_selected()``
        still receive a valid engine.
        """
        entry = self._list_available_minimizers[self._minimizer_current_index]
        return entry if entry is not None else AvailableMinimizers.Bumps_simplex
```

### 3.2 New [logic/bayesian.py](EasyReflectometryApp/Backends/Py/logic/bayesian.py)

Holds DREAM hyper-parameters and the last posterior result. It is purely a
state container — execution is delegated to the worker.

```python
class Bayesian:
    DEFAULTS = dict(samples=10000, burn=2000, population=10, thin=1)

    def __init__(self):
        self._samples    = self.DEFAULTS['samples']
        self._burn       = self.DEFAULTS['burn']
        self._population = self.DEFAULTS['population']
        self._thin       = self.DEFAULTS['thin']
        self._posterior: dict | None = None     # output of MultiFitter.sample()

    # getters / setters with simple validation (positive ints) ...
    # property posterior, has_result, clear() ...
```

### 3.3 [analysis.py](EasyReflectometryApp/Backends/Py/analysis.py)

Add the new properties / slots and a new branch in `_start_threaded_fit`:

```python
@Property(bool, notify=minimizerChanged)
def isBayesianSelected(self) -> bool:
    return self._minimizers_logic.is_bayesian_selected()

# Bayesian hyper-parameters: Property(int) + Slot(int) for each of
# samples / burnIn / population / thinning, all delegating to self._bayesian_logic.

@Property('QVariant', notify=fittingChanged)
def bayesianPosterior(self) -> dict | None:
    p = self._bayesian_logic.posterior
    if p is None:
        return None
    return {
        'paramNames': p['param_names'],
        'nDraws':     int(p['draws'].shape[0]),
        # heavy arrays are not pushed wholesale to QML — only summary
        # statistics are exposed; full draws stay in Python for the chart.
    }
```

### 3.4 Dispatch — sampling vs fitting

Modify `Analysis._start_threaded_fit` so that when Bayesian mode is selected
the worker runs `sample` instead of `fit`:

```python
def _start_threaded_fit(self) -> None:
    self._fitting_logic.reset_stop_flag()
    self._fitting_logic.prepare_for_threaded_fit()
    self.fittingChanged.emit()

    if self._minimizers_logic.is_bayesian_selected():
        self._start_threaded_sample()
    else:
        # ...existing classical path unchanged...
```

`_start_threaded_sample()` calls `FittingLogic.prepare_threaded_sample()` (not
`prepare_threaded_fit()`) to obtain the high-level `easyreflectometry.fitting.MultiFitter`
and the `scipp.DataGroup`, then dispatches to the existing `FitterWorker` with
`method_name='sample'`. The kwargs come from `Bayesian`:

```python
def _start_threaded_sample(self) -> None:
    multi_fitter, data_group = self._fitting_logic.prepare_threaded_sample(
        self._minimizers_logic
    )
    if multi_fitter is None:
        self.fittingChanged.emit()
        if self._fitting_logic.fit_error_message:
            self.fitFailed.emit(self._fitting_logic.fit_error_message)
        return

    self._fitter_thread = FitterWorker(
        fitter=multi_fitter,                   # the high-level reflectometry MultiFitter
        method_name='sample',
        args=(data_group,),                    # sc.DataGroup
        kwargs=dict(
            samples=self._bayesian_logic.samples,
            burn=self._bayesian_logic.burn,
            thin=self._bayesian_logic.thin,
            population=self._bayesian_logic.population,
        ),
        parent=self,
    )
    self._fitter_thread.setTerminationEnabled(True)
    self._fitter_thread.finished.connect(self._on_sample_finished)
    self._fitter_thread.failed.connect(self._on_fit_failed)
    self._fitter_thread.finished.connect(self._fitter_thread.deleteLater)
    self._fitter_thread.failed.connect(self._fitter_thread.deleteLater)
    self._fitter_thread.start()
```

#### Separate preparation path — `prepare_threaded_sample()`

The existing `FittingLogic.prepare_threaded_fit()` returns the **core**
`EasyScienceMultiFitter` (i.e. `multi_fitter.easy_science_multi_fitter`) plus
raw `x`, `y`, `weights` arrays.  The Bayesian path requires the **high-level**
`easyreflectometry.fitting.MultiFitter` plus a `sc.DataGroup`, so the two
paths are incompatible.  Do **not** reuse `prepare_threaded_fit()` for
sampling.  Instead, add a parallel method:

```python
# In logic/fitting.py — FittingLogic
def prepare_threaded_sample(self, minimizers_logic: 'Minimizers') -> tuple:
    """Prepare high-level MultiFitter + DataGroup for Bayesian sampling.

    :return: Tuple of (multi_fitter, data_group) or (None, None) on error.
    """
    from easyreflectometry.fitting import MultiFitter

    experiments = self._ordered_experiments()
    if not experiments:
        self._fit_error_message = 'No experiments to sample'
        self._running = False
        self._finished = True
        self._show_results_dialog = True
        return None, None

    models = [experiment.model for experiment in experiments]
    multi_fitter = MultiFitter(*models)

    # Ensure underlying engine is BUMPS for the sample() call
    selected = minimizers_logic.selected_minimizer_enum()
    if selected is not None:
        multi_fitter.easy_science_multi_fitter.switch_minimizer(selected)

    data_group = self.collect_selected_experiments_datagroup()
    return multi_fitter, data_group


def prepare_for_threaded_sample(self) -> None:
    """Set running flags and sampling progress message before launching the worker."""
    self._running = True
    self._finished = False
    self._show_results_dialog = False
    self._fit_error_message = None
    self._result = None
    self._results = []
    self.clear_fit_progress()
    self._fit_running_message = 'Sampling… (this may take several minutes)'
```

The `_start_threaded_sample()` method in `Analysis` calls this instead of
`prepare_threaded_fit()`.

#### Required helper to assemble `data_group`

`MultiFitter.sample()` takes a `scipp.DataGroup` (same shape as the one
consumed by `MultiFitter.fit`). The current GUI fitting path does **not**
already build that object; it converts project experiments to raw `x`, `y`,
and `weights` arrays and calls the inner core fitter directly. Therefore the
Bayesian path needs an explicit conversion helper in
[logic/fitting.py](EasyReflectometryApp/Backends/Py/logic/fitting.py):

```python
def collect_selected_experiments_datagroup(self) -> sc.DataGroup:
    """Build the scipp DataGroup required by reflectometry-lib MultiFitter.sample()."""
```

The helper should:

1. Use the same ordered / selected experiment list as the current threaded fit.
2. Convert each `DataSet1D` experiment into one reflectivity entry:
   - `coords[f'Qz_{i}'] = sc.array(dims=[f'Qz_{i}'], values=experiment.x,
     variances=experiment.xe, unit=sc.Unit('1/angstrom'))`
   - `data[f'R_{i}'] = sc.array(dims=[f'Qz_{i}'], values=experiment.y,
     variances=experiment.ye)`
3. Preserve `experiment.ye` as variances, because both the existing fitting
   code and `reflectometry-lib` treat `DataSet1D.ye` as σ².
4. Return `sc.DataGroup(data=data, coords=coords, attrs={})`.

The worker should receive the high-level `easyreflectometry.fitting.MultiFitter`
created from the selected experiment models, not
`multi_fitter.easy_science_multi_fitter`, so that the reflectometry-lib
`sample(data_group, ...)` method performs its normal reflectometry-specific
data preparation before delegating to core.

#### Worker compatibility

[fitter_worker.py](EasyReflectometryApp/Backends/Py/workers/fitter_worker.py)
already calls `getattr(self._fitter, self._method_name)(*args, **kwargs)`,
so it works for `sample` unchanged. The only special case is its current
auto-injection of `progress_callback` — that key must be skipped for
`sample`:

```python
if self._method_name == 'fit' and 'progress_callback' not in kwargs:
    kwargs['progress_callback'] = self._progress_callback
```

(Already so guarded — no change required.)

#### Result handling

```python
@Slot(list)
def _on_sample_finished(self, results: list) -> None:
    posterior = results[0]            # {'draws','param_names','state','logp'}
    self._bayesian_logic._posterior = posterior
    # Sampling does not produce FitResults; keep posterior state separate.
    self._fitting_logic.on_sample_finished()
    self._fitter_thread = None
    self._compute_and_publish_posterior_predictive()
    self._publish_posterior_summary()
    self.fittingChanged.emit()
    self.externalFittingChanged.emit()
```

Add the matching method to
[logic/fitting.py](EasyReflectometryApp/Backends/Py/logic/fitting.py):

```python
def on_sample_finished(self) -> None:
    """Handle successful Bayesian sampling completion without FitResults."""
    self._running = False
    self._finished = True
    self._show_results_dialog = True
    self._fit_error_message = None
    self._result = None
    self._results = []
    self.clear_fit_progress()
```

This keeps the shared running / dialog lifecycle consistent without storing
posterior dictionaries in `_result` or `_results`, which are currently
`FitResults`-specific and are read by `fit_success`, `fit_n_pars`, and
`fit_chi2`.

### 3.5 Cancellation

`FitterWorker.stop()` only sets a flag; DREAM is not interruptible. The Stop
button should therefore display a confirmation dialog explaining that the
current DREAM run will keep using CPU until it finishes:

> *"Bayesian MCMC sampling cannot be cancelled mid-run. The sampling will continue
> using CPU until it completes. Do you want to abort anyway?"*

The fit dialog should also show the equivalent message text while sampling is
in progress, and the progress bar must remain in **indeterminate** mode during
DREAM runs (see §1.3). (Same caveat already applies to long classical fits —
see `THREAD_TERMINATION_WARNING.md`.)

---

## 4. Library-side support already in place

No new public API is required from `reflectometry-lib`. The existing methods
are sufficient:

- `MultiFitter.sample(data, samples, burn, thin, population, seed, objective)`
  — see [reflectometry-lib/src/easyreflectometry/fitting.py](../reflectometry-lib/src/easyreflectometry/fitting.py)
- The returned dict already contains everything needed for both posterior
  visualisations.

Use the analysis helpers already available in `reflectometry-lib/analysis/bayesian.py`
(documented in [BAYESIAN_IN_ERL.md §4](../reflectometry-lib/BAYESIAN_IN_ERL.md)):

- `posterior_predictive_reflectivity(draws, param_names, model, q_values, n_samples)`
  → `(median, lower_95, upper_95)`
- `credible_intervals(draws, param_names, alpha=0.95)` → per-parameter
  summary used in §6.

These helpers stay in `reflectometry-lib`; the GUI imports and calls them
rather than duplicating posterior-analysis logic in the app repository.

---

## 5. Posterior Predictive Overlay on the Reflectivity Chart

### 5.1 Concept

After sampling, draw `N=200` random parameter sets from the posterior, evaluate
the model on the experiment's `q` grid, and reduce to per-`q`:

- `R_median(q)`         — solid line
- `R_lower(q), R_upper(q)` — 95% credible band (envelope)

Overlay these on the existing analysis chart in
[AnalysisView.qml](EasyReflectometryApp/Gui/Pages/Analysis/MainContent/AnalysisView.qml)
without disturbing the classical `calcSerie` / `measSerie` series.

### 5.2 Backend

In `Analysis._compute_and_publish_posterior_predictive()`:

```python
from easyreflectometry.analysis.bayesian import posterior_predictive_reflectivity

q = experiment.x
median, lo, hi = posterior_predictive_reflectivity(
    posterior['draws'], posterior['param_names'],
    model=experiment.model, q_values=q, n_samples=200,
)
self._plotting.set_posterior_predictive(q, median, lo, hi)
```

Important: `posterior_predictive_reflectivity()` returns **linear**
reflectivity. Before publishing to QML, `Plotting1d` must transform the
posterior curves into the same chart-space values as the existing analysis
series:

1. Apply `_apply_rq4(q, values)` when the `R(q) × q⁴` mode is enabled.
2. Clip or mask non-positive values before taking logarithms.
3. Publish `log10(median)`, `log10(lower)`, and `log10(upper)`, matching the
   current `axisY.title: "Log10 " + plottingYAxisTitle` behaviour.

This transform should live in `Plotting1d.set_posterior_predictive(...)` (or a
small private helper it calls), so the posterior overlay stays in sync with
the same plot-mode toggles used by measured and calculated data.

`Plotting1d` gains:

- A `posteriorPredictiveDataChanged` signal.
- Properties `posteriorPredictiveQ`, `posteriorPredictiveMedian`,
  `posteriorPredictiveLower`, `posteriorPredictiveUpper`
  (`Property('QVariantList', notify=...)`).
- `clear_posterior_predictive()` — called at the start of every fit/sample
  and whenever the project is reset.

### 5.3 QML

In `AnalysisView.qml`, add three series tied to the same axes:

```qml
LineSeries {
    id: ppMedianSerie
    name: qsTr("Posterior median")
    axisX: chartView.currentXAxis()
    axisY: chartView.axisY
    color: EaStyle.Colors.chartForegroundsExtra[1]
    width: 2
    visible: Globals.BackendWrapper.bayesianResultAvailable
}

AreaSeries {
    id: ppBandSerie
    name: qsTr("95% credible interval")
    axisX: chartView.currentXAxis()
    axisY: chartView.axisY
    color: Qt.rgba(ppMedianSerie.color.r, ppMedianSerie.color.g,
                   ppMedianSerie.color.b, 0.25)
    borderWidth: 0
    upperSeries: LineSeries { id: ppUpperSerie }
    lowerSeries: LineSeries { id: ppLowerSerie }
    visible: Globals.BackendWrapper.bayesianResultAvailable
}

Connections {
    target: Globals.BackendWrapper.activeBackend?.plotting ?? null
    function onPosteriorPredictiveDataChanged() {
        ppMedianSerie.clear(); ppUpperSerie.clear(); ppLowerSerie.clear()
        const q  = Globals.BackendWrapper.posteriorPredictiveQ
        const m  = Globals.BackendWrapper.posteriorPredictiveMedian
        const lo = Globals.BackendWrapper.posteriorPredictiveLower
        const hi = Globals.BackendWrapper.posteriorPredictiveUpper
        for (let i = 0; i < q.length; ++i) {
            ppMedianSerie.append(q[i], m[i])
            ppLowerSerie.append(q[i], lo[i])
            ppUpperSerie.append(q[i], hi[i])
        }
    }
}
```

### 5.4 Legend

`QtCharts1dBase.qml` currently sets `legend.visible: false`. Toggle it on as
soon as Bayesian results exist so that `Measured`, `Calculated`, `Posterior
median` and `95% credible interval` are distinguishable:

```qml
chartView.legend.visible: Globals.BackendWrapper.bayesianResultAvailable
                       || Globals.Variables.showLegendOnAnalysisPage
```

For consistency, ensure the existing `measSerie`, `calcSerie`, etc. carry a
non-empty `name:` so they appear in the legend.

### 5.5 Reset behaviour

When the user starts a new fit, switches calculator, or removes the
experiment, `clear_posterior_predictive()` is invoked and the three series
are cleared.

---

## 6. Posterior Distribution Chart (separate tab)

### 6.1 Where it lives

A new main-content tab/page **Bayesian Results**, accessible from the Analysis
page when `bayesianResultAvailable` is true. This uses the same page-host
pattern as the rest of the GUI.

Folder layout:

```
EasyReflectometryApp/Gui/Pages/Analysis/MainContent/
├── AnalysisView.qml              (existing, modified)
└── BayesianPosteriorView.qml     (new)
```

A dedicated tab in the Analysis page host (`Analysis.qml`, or the equivalent
main-content container) switches between the existing reflectivity view and
`BayesianPosteriorView`. The reflectivity view remains the default; the
Bayesian tab is disabled or hidden until a posterior result exists.

### 6.2 First iteration: marginal histograms

For each parameter return:

- A histogram (`BarSeries` / `HorizontalStackedBarSeries`) of `draws[:, k]`
  (computed in Python with `numpy.histogram`, exposed as `bins` + `counts`).
- A vertical line at the mean and at the 95% credible interval bounds.
- A label with `mean ± std` and the credible interval.

Backend exposure:

```python
@Property('QVariant', notify=fittingChanged)
def bayesianMarginals(self) -> list[dict]:
    if not self._bayesian_logic.has_result:
        return []
    out = []
    for k, name in enumerate(p['param_names']):
        col = p['draws'][:, k]
        counts, edges = np.histogram(col, bins=40, density=True)
        centers = 0.5 * (edges[:-1] + edges[1:])
        out.append(dict(
            name=name,
            mean=float(col.mean()), std=float(col.std()),
            ci_low=float(np.quantile(col, 0.025)),
            ci_high=float(np.quantile(col, 0.975)),
            binCenters=centers.tolist(),
            counts=counts.tolist(),
        ))
    return out
```

QML: a `Repeater` over `bayesianMarginals` that creates one `ChartView` per
parameter, arranged in a `Flow` / `GridLayout`.

### 6.3 Future iteration: corner plot

A full corner / pair-plot view (using `BarSeries` for the diagonals and
`ScatterSeries` for the off-diagonals) is feasible with Qt Charts but
expensive. Recommended phase-2: render a corner plot offline (the
`reflectometry-lib` analysis module already wraps `corner.corner`) into a
PNG and display it via `Image`. This keeps the GUI responsive and reuses the
library implementation.

### 6.4 Convergence diagnostics

A small text panel at the top of `BayesianPosteriorView`:

- Number of samples (after burn / thin)
- Acceptance rate (`state.acceptance_rate` if available)
- Per-parameter R-hat (Gelman-Rubin), via `arviz` if installed (graceful
  fallback otherwise)

Source these directly from the `state` object returned by
`MultiFitter.sample()`.

---

## 7. Files to add / modify

### Add

- `EasyReflectometryApp/Backends/Py/logic/bayesian.py` (state container)
- `EasyReflectometryApp/Gui/Pages/Analysis/MainContent/BayesianPosteriorView.qml`

### Modify

- `EasyReflectometryApp/Backends/Py/logic/minimizers.py` — virtual Bayesian
  entry, `is_bayesian_selected()`, guarded `selected_minimizer_enum()`.
- `EasyReflectometryApp/Backends/Py/logic/fitting.py` —
  `collect_selected_experiments_datagroup()` helper,
  `prepare_threaded_sample()` (two methods: model/data prep + state flags),
  `on_sample_finished()`.
- `EasyReflectometryApp/Backends/Py/analysis.py` — Bayesian properties / slots,
  `_start_threaded_sample()`, `_on_sample_finished()`,
  posterior-predictive publishing.
- `EasyReflectometryApp/Backends/Py/plotting_1d.py` — posterior-predictive
  arrays + signal + clear.
- `EasyReflectometryApp/Backends/Mock/Analysis.qml` — mirror the new
  properties so the mock backend remains usable.
- `EasyReflectometryApp/Gui/Globals/BackendWrapper.qml` — forward the new
  properties / slots.
- `EasyReflectometryApp/Gui/Pages/Analysis/Sidebar/Advanced/Groups/Minimizer.qml`
  — Bayesian-only sub-group, conditional visibility.
- `EasyReflectometryApp/Gui/Pages/Analysis/MainContent/AnalysisView.qml`
  — overlay series + legend toggle.
- `EasyReflectometryApp/Gui/Pages/Analysis/Analysis.qml` (or equivalent
  page host) — switch between reflectivity view and posterior view.
- `EasyReflectometryApp/Gui/Pages/Analysis/Sidebar/Advanced/Dialogs/FitStatusDialog.qml`
  — indeterminate progress bar when Bayesian mode is active.

### Tests

- `tests/backend/test_bayesian_logic.py` — defaults, validation, set/get.
- `tests/backend/test_minimizers_bayesian.py` — combobox content, selection
  routing, `project.minimizer` falls back to `Bumps_simplex` when Bayesian
  is selected.
- `tests/backend/test_analysis_sample_dispatch.py` — `_start_threaded_fit`
  routes to the sample path when Bayesian is selected; worker is invoked
  with `method_name='sample'` and the configured kwargs.

---

## 8. Implementation Order

1. Library prerequisite check: confirm `MultiFitter.sample()` exists with the
  signature in §1, and that `posterior_predictive_reflectivity` is available
  in `easyreflectometry.analysis.bayesian`.
2. `logic/bayesian.py` + `logic/minimizers.py` virtual entry + guarded
  `selected_minimizer_enum()` + tests.
3. `FittingLogic.collect_selected_experiments_datagroup()` +
  `FittingLogic.prepare_threaded_sample()` (model/data prep + state flags) —
  test this from Python directly before wiring QML.
4. `analysis.py` properties / slots + dispatch to `sample` via the existing
  `FitterWorker` using the new `prepare_threaded_sample()` path.
5. QML wiring of the Minimizer combobox conditional sub-group + indeterminate
  progress bar in `FitStatusDialog.qml`.
6. Posterior-predictive computation, `Plotting1d` signal, `AnalysisView.qml`
  overlay + legend.
7. `BayesianPosteriorView.qml` with marginal histograms and convergence panel.
8. Phase 2 (separate ticket): corner-plot image + R-hat / ESS surfacing,
  optional `Seed` field, save/load DREAM state via the project file.

---

## 9. Risks & Open Questions

| # | Risk / question | Mitigation |
|---|-----------------|-----------|
| 1 | Sampling can take many minutes; `FitterWorker.stop()` cannot interrupt DREAM. | Show explicit *"Sampling cannot be cancelled mid-run"* warning in the stop dialog. |
| 2 | Multi-experiment posterior — single joint posterior or per-experiment? | `MultiFitter.sample()` already returns a joint posterior; overlay the credible band on the currently selected experiment only (others can be selected from the existing experiment combo). |
| 3 | Posterior arrays may be large (`samples × n_params`). | Keep raw `draws` in Python; only push summary statistics + downsampled curves to QML. |
| 4 | `BUMPS-DREAM` shown as a "minimizer" may confuse users. | Label includes the explicit `(Bayesian)` suffix; help-tooltip explains it runs MCMC sampling, not optimisation. |
| 5 | QML `AreaSeries` requires both `upperSeries` and `lowerSeries` on the same axis range; log-Q mode needs the band recreated against `axisXLog`. | Rebuild the three series in `recreateForLogMode()` alongside the existing `logModeSeries`. |
| 6 | Corner plot in pure Qt Charts is heavy. | Defer to phase 2 — render via `corner.corner()` to PNG. |
| 7 | Mock backend must not break. | Add stub properties returning sensible defaults / empty data. |

---

## 10. Implementation Status (completed 2026-05-07)

### Completed (Phase 1)

All items in the implementation plan (§1–§7) have been implemented, with two
minor deviations from the original plan:

| Deviation | Plan | Actual |
|---|---|---|
| Progress bar location | `FitStatusDialog.qml` | `Fitting.qml` group box (the FitStatusDialog is only visible after completion, not during fitting) |
| Log-Q axis posterior overlay | Deferred | Deferred — overlay added to `CombinedView.qml` only; log-axis recreation of posterior series is a follow-up |

### Files changed / added

| File | Action | Description |
|---|---|---|
| `logic/bayesian.py` | **Added** | State container for DREAM hyper-parameters and posterior |
| `logic/minimizers.py` | Modified | Virtual Bayesian sentinel, `is_bayesian_selected()`, guarded `selected_minimizer_enum()` |
| `logic/fitting.py` | Modified | `collect_selected_experiments_datagroup()`, `prepare_threaded_sample()`, `prepare_for_threaded_sample()`, `on_sample_finished()` |
| `analysis.py` | Modified | Bayesian properties/slots, `_start_threaded_sample()`, `_on_sample_finished()`, `_compute_and_publish_posterior_predictive()`, `set_plotting()` |
| `plotting_1d.py` | Modified | `posteriorPredictiveDataChanged` signal, 4 posterior properties, `set_posterior_predictive()`, `clear_posterior_predictive()` |
| `py_backend.py` | Modified | `self._analysis.set_plotting(self._plotting_1d)` wiring |
| `Minimizer.qml` | Modified | Bayesian-only controls group, `visible` binding on classical fields, fixed duplicate `onAccepted` bug |
| `BackendWrapper.qml` | Modified | Bayesian forwarding properties + posterior predictive plotting properties |
| `CombinedView.qml` | Modified | `LineSeries`/`AreaSeries` posterior overlay, legend visibility toggle |
| `Fitting.qml` | Modified | Inline `ProgressBar` (indeterminate for Bayesian) + progress message label |
| `FitStatusDialog.qml` | Modified | Conditional Bayesian results content |
| `BayesianPosteriorView.qml` | **Added** | Marginal histogram grid with `Repeater` over `bayesianMarginals` |
| `Layout.qml` | Modified | "Bayesian Posterior" tab (enabled when `bayesianResultAvailable`) |
| `Mock/Analysis.qml` | Modified | Bayesian stub properties + setter functions |
| `Mock/Plotting.qml` | Modified | Posterior predictive stub properties + signal |
| `tests/test_logic_minimizers.py` | Modified | Updated for Bayesian sentinel at index 0 |
| `tests/test_analysis.py` | Modified | Added `is_bayesian_selected()` to `StubMinimizersLogic` |

### Remaining for Phase 2

- Corner plot image (render offline via `corner.corner()`, display as `Image`)
- `Seed` field in the GUI
- Save/load DREAM state via project file
- Log-Q axis posterior overlay in `AnalysisView.qml` / `CombinedView.qml`
- Full R-hat / ESS convergence diagnostics from `arviz`
- SLD profile posterior overlay

---

## 11. Phase 2 — Bayesian Posterior Subtabs & Full Diagnostics

### 11.0 Requirements Coverage

This phase-2 plan explicitly covers every item from the original GUI request.

| Original requirement | Covered by | Delivery mode |
|---|---|---|
| Pairwise correlations and marginal distributions | §11.3 `Marginals` + §11.4 `Corner Plot` | Subtabs inside the existing **Bayesian Posterior** tab |
| MCMC chains for convergence | §11.5 `Traces` | Subtab inside the existing **Bayesian Posterior** tab |
| 2D parameter heatmap | §11.6 `2D Heatmap` | Subtab inside the existing **Bayesian Posterior** tab |
| Gelman-Rubin convergence diagnostic | §11.7 `Diagnostics` | Subtab inside the existing **Bayesian Posterior** tab |
| Posterior-predictive reflectivity with credible intervals | §11.8.1 | Overlay on the main reflectivity chart, matching the notebook workflow |
| Posterior-predictive SLD profile with credible intervals | §11.8.2 | Overlay on the main SLD chart, matching the notebook workflow |

Interpretation of the requirement:

- The **existing Bayesian Posterior tab** becomes a container for Bayesian-analysis subtabs.
- The **posterior-predictive reflectivity** and **posterior-predictive SLD profile** are intentionally **not** separate Bayesian subtabs, because the requirement says those credible intervals should be overlaid on the main charts as in the notebook.
- The notebook in [reflectometry-lib/docs/src/tutorials/advancedfitting/bayesian_bumps.ipynb](../reflectometry-lib/docs/src/tutorials/advancedfitting/bayesian_bumps.ipynb) is used as the behaviour reference for both the reflectivity and SLD overlays.

### 11.1 Motivation

Phase 1 delivered the minimum viable Bayesian GUI: sampling dispatch, marginal
histograms, and a posterior-predictive reflectivity band overlay. However, the
Bayesian Posterior tab currently only shows a flat grid of per-parameter
histograms — the same information that classical fitting already provides via
parameter error bars. A proper Bayesian workflow requires:

- **Pairwise correlations & marginal distributions** — to see parameter
  degeneracies (the hallmark of Bayesian analysis).
- **MCMC trace plots** — to visually assess chain convergence.
- **2D parameter heatmap** — to zoom into a specific parameter pair.
- **Gelman-Rubin R-hat** — a quantitative convergence diagnostic.
- **Posterior-predictive SLD profile** — credible bands on the SLD chart,
  complementing the reflectivity overlay already in `CombinedView.qml`.

### 11.2 Architecture Decision: Subtabs within Bayesian Posterior

Currently `Layout.qml` defines two top-level tabs: **Reflectivity** and
**Bayesian Posterior**. The Bayesian Posterior tab loads
`BayesianPosteriorView.qml` as a single flat view.

**Proposed change**: Transform `BayesianPosteriorView.qml` into a tab
container with its own `TabBar` + `StackLayout` hosting these subtabs:

| # | Subtab Label               | Content                                              |
|---|----------------------------|------------------------------------------------------|
| 1 | **Marginals**              | Existing per-parameter histogram grid (refactored)   |
| 2 | **Corner Plot**            | Pairwise scatter matrix + 1D marginals on diagonal   |
| 3 | **Traces**                 | MCMC chain trace plots (one per parameter)           |
| 4 | **2D Heatmap**             | Joint posterior density for a user-selected pair     |
| 5 | **Diagnostics**            | Summary table: R-hat, ESS, acceptance rate, etc.     |

The subtab bar sits at the top of the Bayesian Posterior content area, above
the `StackLayout` that hosts each sub-view. This keeps the navigation flat
(one extra click from the main tab bar) and allows each sub-view to be
developed independently.

```
┌─ Analysis Page ─────────────────────────────────────────────┐
│ [Reflectivity]  [Bayesian Posterior]                         │
│                                                              │
│  ┌─ Bayesian Posterior Subtabs ────────────────────────────┐ │
│  │ [Marginals] [Corner Plot] [Traces] [2D Heatmap] [Diag] │ │
│  │                                                          │ │
│  │  (active sub-view content)                               │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

### 11.3 Subtab 1: Marginals (Refactor Existing)

Move the current `Flow` + `Repeater` over `bayesianMarginals` from
`BayesianPosteriorView.qml` into a dedicated `BayesianMarginalsView.qml`
component. Enhance it:

- Display 95% credible interval as vertical dashed lines on each histogram.
- Use `EaStyle.Colors` for histogram bar colour (not hardcoded `#3498db`).
- Show per-parameter summary text: `mean ± std [CI_low, CI_high]`.
- Use a responsive `GridLayout` (columns = `min(3, n_params)`) instead of
  `Flow` for a more structured grid.

**Backend**: No changes — the existing `bayesianMarginals` property already
provides `name`, `mean`, `std`, `ci_low`, `ci_high`, `binCenters`, `counts`.

**Files**:
- New: `BayesianMarginalsView.qml` (extracted from `BayesianPosteriorView.qml`)
- Modified: `BayesianPosteriorView.qml` — becomes the tab container

### 11.4 Subtab 2: Corner Plot (Pairwise Correlations)

#### 11.4.1 Strategy: PNG Rendering

Building a scatter-plot matrix in Qt Charts is feasible for ≤4 parameters but
becomes expensive for 6+ parameters (n² subplots, each a `ChartView`). The
standard scientific approach is to render a corner plot via the `corner`
Python library and display it as a QML `Image`.

**Approach**: Generate a PNG in the Python backend after sampling completes,
expose the file path or a base64 data URL to QML.

#### 11.4.2 Backend Changes

**`analysis.py`** — new property and helper:

```python
import io
import base64
import tempfile
from pathlib import Path

@Property(str, notify=fittingChanged)
def bayesianCornerPlotUrl(self) -> str:
    """Return a data: URL for the corner plot PNG, or empty string."""
    if not self._bayesian_logic.has_result:
        return ''
    return self._bayesian_logic.corner_plot_url or ''

# Called from _on_sample_finished():
def _render_corner_plot(self) -> None:
    """Render corner plot to a temporary PNG and store its data URL."""
    from easyreflectometry.analysis.bayesian import plot_corner
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    posterior = self._bayesian_logic.posterior
    fig = plt.figure(figsize=(max(6, len(posterior['param_names']) * 1.8),
                             max(6, len(posterior['param_names']) * 1.8)))
    plot_corner(posterior['draws'], posterior['param_names'])
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('ascii')
    self._bayesian_logic.corner_plot_url = f'data:image/png;base64,{b64}'
```

Add a `corner_plot_url: str` attribute to `logic/bayesian.py` (`Bayesian`
class), cleared in `clear()`.

**Important**: The corner plot rendering should be done **once** in
`_on_sample_finished()` (not on every property read) to avoid blocking the
GUI. The result is cached as a string.

#### 11.4.3 QML

**`BayesianCornerView.qml`** (new file):

```qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import Gui.Globals as Globals

Rectangle {
    color: EaStyle.Colors.chartBackground

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: EaStyle.Sizes.fontPixelSize
        spacing: EaStyle.Sizes.fontPixelSize

        EaElements.Label {
            text: qsTr("Pairwise Parameter Correlations & Marginal Distributions")
            font: EaStyle.Fonts.headingFont
        }

        Image {
            id: cornerImage
            Layout.fillWidth: true
            Layout.fillHeight: true
            fillMode: Image.PreserveAspectFit
            source: Globals.BackendWrapper.bayesianCornerPlotUrl || ''
            cache: false
            visible: source != ''

            BusyIndicator {
                anchors.centerIn: parent
                running: cornerImage.source == '' && Globals.BackendWrapper.bayesianResultAvailable
            }
        }

        EaElements.Label {
            visible: cornerImage.source == '' && !Globals.BackendWrapper.bayesianResultAvailable
            text: qsTr("No Bayesian results available.")
            color: EaStyle.Colors.themeForegroundMinor
        }
    }
}
```

**BackendWrapper.qml** — add forwarding:

```qml
readonly property string bayesianCornerPlotUrl: activeBackend.analysis.bayesianCornerPlotUrl
```

#### 11.4.4 Fallback: Interactive Qt Charts Corner (Optional Future)

If PNG rendering is not desired, a pure-QML corner plot can be built with a
`GridLayout` of `ChartView` instances. The diagonal shows a histogram
(`BarSeries`) and the off-diagonals show a `ScatterSeries`. This is deferred
to a future iteration because:

- Memory: `n_params²` `ChartView` instances, each with its own OpenGL context.
- Performance: Updating n² series with thousands of scatter points is slow.
- The `corner` library PNG is the standard in scientific Python.

### 11.5 Subtab 3: Trace Plots (MCMC Chain Convergence)

#### 11.5.1 Strategy

MCMC trace plots show the sampled parameter value vs. draw index. They let
users visually check that chains have converged (no drift, good mixing). The
standard approach uses `arviz.plot_trace`.

For the GUI we have two options:
1. **PNG rendering** via `arviz.plot_trace` — same pattern as corner plot.
2. **Qt Charts `LineSeries`** — push chain data as `QVariantList` to QML.

**Recommendation**: Use PNG rendering (consistent with corner plot, avoids
pushing large chain arrays to QML). The raw chain data stays in Python.

#### 11.5.2 Backend Changes

**`analysis.py`**:

```python
@Property(str, notify=fittingChanged)
def bayesianTracePlotUrl(self) -> str:
    if not self._bayesian_logic.has_result:
        return ''
    return self._bayesian_logic.trace_plot_url or ''
```

**`_render_trace_plot()`** (called from `_on_sample_finished()`):

```python
def _render_trace_plot(self) -> None:
    """Render MCMC trace plots to PNG via arviz."""
    try:
        from easyreflectometry.analysis.bayesian import plot_trace
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        posterior = self._bayesian_logic.posterior
        n_params = len(posterior['param_names'])
        fig, axes = plt.subplots(n_params, 1,
                                 figsize=(10, 2.5 * n_params),
                                 squeeze=False)
        plot_trace(posterior['draws'], posterior['param_names'])
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        b64 = base64.b64encode(buf.read()).decode('ascii')
        self._bayesian_logic.trace_plot_url = f'data:image/png;base64,{b64}'
    except ImportError:
        self._bayesian_logic.trace_plot_url = ''
        logger.info('arviz not installed — trace plot unavailable')
```

**`logic/bayesian.py`**: Add `trace_plot_url: str` attribute.

#### 11.5.3 QML

**`BayesianTraceView.qml`** — analogous to `BayesianCornerView.qml` but
displaying the trace plot PNG.

#### 11.5.4 Fallback When arviz Is Not Installed

Show a friendly message:
> *"Trace plots require the `arviz` library. Install it with:*
> *`pip install easyreflectometry[bayesian]`"*

### 11.6 Subtab 4: 2D Parameter Heatmap

#### 11.6.1 Strategy

Allow the user to select two parameters from dropdowns, then display their
joint posterior density as a 2D heatmap. This is the same as zooming into one
off-diagonal cell of the corner plot but with higher resolution.

#### 11.6.2 Backend Changes

**`analysis.py`** — new properties and a slot:

```python
@Property('QVariantList', notify=fittingChanged)
def bayesianParamNames(self) -> list[str]:
    """Return parameter names for the heatmap axis dropdowns."""
    if not self._bayesian_logic.has_result:
        return []
    return self._bayesian_logic.posterior['param_names']

# Heatmap data: computed on demand for a selected parameter pair
@Property('QVariant', notify=heatmapChanged)
def bayesianHeatmapData(self) -> dict | None:
    return self._bayesian_logic.heatmap_data

@Slot(int, int)
def computeBayesianHeatmap(self, paramX: int, paramY: int) -> None:
    """Compute 2D histogram for the selected parameter pair."""
    import numpy as np
    posterior = self._bayesian_logic.posterior
    if posterior is None:
        return
    draws = posterior['draws']
    x = draws[:, paramX]
    y = draws[:, paramY]
    H, xedges, yedges = np.histogram2d(x, y, bins=50, density=True)
    self._bayesian_logic.heatmap_data = {
        'xLabel': posterior['param_names'][paramX],
        'yLabel': posterior['param_names'][paramY],
        'xCenters': (0.5 * (xedges[:-1] + xedges[1:])).tolist(),
        'yCenters': (0.5 * (yedges[:-1] + yedges[1:])).tolist(),
        'zValues': H.T.tolist(),  # transposed for consistent display
    }
    self.heatmapChanged.emit()
```

A new signal `heatmapChanged = Signal()` is added to `Analysis`.

**`logic/bayesian.py`**: Add `heatmap_data: dict | None` attribute.

#### 11.6.3 QML

**`BayesianHeatmapView.qml`** (new file):

```qml
Rectangle {
    color: EaStyle.Colors.chartBackground

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: EaStyle.Sizes.fontPixelSize
        spacing: EaStyle.Sizes.fontPixelSize

        // Parameter selection row
        RowLayout {
            EaElements.Label { text: qsTr("X-axis:") }
            EaElements.ComboBox {
                id: paramXCombo
                model: Globals.BackendWrapper.bayesianParamNames
                onCurrentIndexChanged: updateHeatmap()
            }
            EaElements.Label { text: qsTr("Y-axis:") }
            EaElements.ComboBox {
                id: paramYCombo
                model: Globals.BackendWrapper.bayesianParamNames
                currentIndex: Math.min(1, model.length - 1)
                onCurrentIndexChanged: updateHeatmap()
            }
        }

        // 2D Heatmap using Qt Charts (or Plotly WebEngineView)
        // Use a colour-mapped grid. Qt Charts does not have a native heatmap
        // series, so two alternatives:
        //
        // Option A (recommended): Plotly2dHeatmap from EasyApp, using the
        //   existing Plotly WebEngineView infrastructure.
        //
        // Option B: Render as PNG via matplotlib imshow and display as Image.
    }
}
```

**Recommendation**: Use **Option A** (Plotly WebEngineView) since EasyApp
already ships `Plotly2dHeatmap.qml` and `Plotly2dHeatmap.html`. This provides
interactive hover, zoom, and pan for free.

**If Plotly not desired**, Option B is simpler: render via matplotlib and
display as `Image`. This is the pragmatic choice for a first iteration.

#### 11.6.4 BackendWrapper.qml Additions

```qml
readonly property var bayesianParamNames: activeBackend.analysis.bayesianParamNames
readonly property var bayesianHeatmapData: activeBackend.analysis.bayesianHeatmapData
function bayesianComputeHeatmap(x, y) { activeBackend.analysis.computeBayesianHeatmap(x, y) }
```

### 11.7 Subtab 5: Convergence Diagnostics

#### 11.7.1 Content

A scrollable text panel presenting:

| Diagnostic | Source | Description |
|---|---|---|
| **R-hat (Gelman-Rubin)** | `arviz.rhat` / `PosteriorResults.gelman_rubin()` | Per-parameter convergence; <1.1 = good |
| **Effective Sample Size (ESS)** | `arviz.ess` (future) | Number of independent draws |
| **Acceptance Rate** | BUMPS `state.acceptance_rate` | DREAM proposal acceptance fraction |
| **Number of Draws** | `draws.shape[0]` | After burn-in and thinning |
| **Number of Parameters** | `draws.shape[1]` | Dimensionality |
| **Burn-in Steps** | User setting | From Bayesian controls |
| **Thinning** | User setting | From Bayesian controls |
| **Population (Chains)** | User setting | DREAM population count |

#### 11.7.2 Backend Changes

**`analysis.py`** — compute once in `_on_sample_finished()` and store as dict:

```python
@Property('QVariant', notify=fittingChanged)
def bayesianDiagnostics(self) -> dict:
    return self._bayesian_logic.diagnostics or {}

def _compute_diagnostics(self) -> None:
    """Compute convergence diagnostics from the posterior and state."""
    posterior = self._bayesian_logic.posterior
    diagnostics = {
        'nDraws': int(posterior['draws'].shape[0]),
        'nParams': int(posterior['draws'].shape[1]),
        'burnIn': self._bayesian_logic.burn,
        'thin': self._bayesian_logic.thin,
        'population': self._bayesian_logic.population,
        'samples': self._bayesian_logic.samples,
    }

    # Extract acceptance rate from BUMPS state if available
    state = posterior.get('state')
    if state is not None:
        try:
            diagnostics['acceptanceRate'] = float(state.acceptance_rate)
        except (AttributeError, TypeError):
            pass

    # R-hat via arviz (wrapped in PosteriorResults)
    try:
        from easyreflectometry.analysis.bayesian import PosteriorResults
        pr = PosteriorResults(posterior['draws'], posterior['param_names'])
        rhat = pr.gelman_rubin()
        if rhat is not None:
            diagnostics['rhat'] = rhat
    except ImportError:
        pass

    self._bayesian_logic.diagnostics = diagnostics
```

**`logic/bayesian.py`**: Add `diagnostics: dict` attribute, cleared in `clear()`.

#### 11.7.3 QML

**`BayesianDiagnosticsView.qml`** (new file):

```qml
Rectangle {
    color: EaStyle.Colors.chartBackground

    Flickable {
        anchors.fill: parent
        anchors.margins: EaStyle.Sizes.fontPixelSize
        contentHeight: diagColumn.implicitHeight

        ColumnLayout {
            id: diagColumn
            width: parent.width
            spacing: EaStyle.Sizes.fontPixelSize

            EaElements.Label {
                text: qsTr("MCMC Convergence Diagnostics")
                font: EaStyle.Fonts.headingFont
            }

            // Sampling settings section
            EaElements.GroupBox {
                title: qsTr("Sampling Configuration")
                ColumnLayout {
                    Repeater {
                        model: [
                            { label: qsTr("Requested samples"), key: "samples" },
                            { label: qsTr("Burn-in steps"), key: "burnIn" },
                            { label: qsTr("Thinning"), key: "thin" },
                            { label: qsTr("Population (chains)"), key: "population" },
                            { label: qsTr("Retained draws"), key: "nDraws" },
                            { label: qsTr("Parameters"), key: "nParams" },
                        ]
                        RowLayout {
                            EaElements.Label { text: modelData.label; Layout.fillWidth: true }
                            EaElements.Label {
                                text: Globals.BackendWrapper.bayesianDiagnostics[modelData.key] ?? '—'
                                font.bold: true
                            }
                        }
                    }
                }
            }

            // Acceptance rate
            EaElements.GroupBox {
                title: qsTr("Acceptance Rate")
                visible: Globals.BackendWrapper.bayesianDiagnostics.acceptanceRate !== undefined
                EaElements.Label {
                    text: (Globals.BackendWrapper.bayesianDiagnostics.acceptanceRate * 100).toFixed(1) + '%'
                }
            }

            // Gelman-Rubin R-hat table
            EaElements.GroupBox {
                title: qsTr("Gelman-Rubin R̂ (Convergence)")
                visible: Globals.BackendWrapper.bayesianDiagnostics.rhat !== undefined
                ColumnLayout {
                    Repeater {
                        model: Object.keys(Globals.BackendWrapper.bayesianDiagnostics.rhat || {})
                        RowLayout {
                            EaElements.Label { text: modelData; Layout.fillWidth: true }
                            EaElements.Label {
                                text: Globals.BackendWrapper.bayesianDiagnostics.rhat[modelData].toFixed(4)
                                color: Globals.BackendWrapper.bayesianDiagnostics.rhat[modelData] < 1.1
                                       ? EaStyle.Colors.success : EaStyle.Colors.warning
                                font.bold: true
                            }
                        }
                    }
                }
            }
        }
    }
}
```

**BackendWrapper.qml** — add:

```qml
readonly property var bayesianDiagnostics: activeBackend.analysis.bayesianDiagnostics
```

### 11.8 Posterior-Predictive Overlays on Main Charts

#### 11.8.1 Reflectivity Overlay (Already Implemented)

`CombinedView.qml` already has `ppMedianSerie` (LineSeries), `ppBandSerie`
(AreaSeries with upper/lower LineSeries), connected to
`posteriorPredictiveDataChanged`. This is functional.

**Remaining work**:
- Add the same overlay to the standalone `AnalysisView.qml` (currently only in
  `CombinedView.qml`).
- Support the log-Q axis mode (recreate the series against `axisXLog` when
  `useLogQAxis` toggles).
- Ensure the overlay series are cleared when a new fit/sample starts.

#### 11.8.2 SLD Profile Overlay (New)

The SLD chart (in `SldView.qml` / the lower panel of `CombinedView.qml`)
currently shows only the classical SLD profile. We need to add a posterior
predictive SLD band — analogous to the reflectivity overlay.

##### Backend

**`analysis.py`** — extend `_compute_and_publish_posterior_predictive()` to
also compute the SLD profile:

```python
def _compute_and_publish_posterior_predictive(self) -> None:
    """Compute posterior predictive reflectivity AND SLD, publish to plotting."""
    if self._plotting is None:
        return
    from easyreflectometry.analysis.bayesian import (
        posterior_predictive_reflectivity,
        posterior_predictive_sld_profile,
    )
    posterior = self._bayesian_logic.posterior
    if posterior is None:
        return

    experiments = self._ordered_experiments()
    if not experiments:
        return

    experiment = experiments[0]
    model = experiment.model
    q = experiment.x

    # Reflectivity
    r_median, r_lo, r_hi = posterior_predictive_reflectivity(
        posterior['draws'], posterior['param_names'],
        model=model, q_values=q, n_samples=200,
    )
    self._plotting.set_posterior_predictive(q, r_median, r_lo, r_hi)

    # SLD profile
    z, sld_median, sld_lo, sld_hi = posterior_predictive_sld_profile(
        posterior['draws'], posterior['param_names'],
        model=model, n_samples=200,
    )
    self._plotting.set_posterior_predictive_sld(z, sld_median, sld_lo, sld_hi)
```

**`plotting_1d.py`** — add SLD posterior predictive support (parallel to the
existing reflectivity posterior predictive):

```python
# New signal
posteriorPredictiveSldDataChanged = Signal()

# New state
self._posterior_sld_z: list = []
self._posterior_sld_median: list = []
self._posterior_sld_lower: list = []
self._posterior_sld_upper: list = []

def set_posterior_predictive_sld(self, z, median, lo, hi) -> None:
    self._posterior_sld_z = z.tolist() if hasattr(z, 'tolist') else list(z)
    self._posterior_sld_median = median.tolist() if hasattr(median, 'tolist') else list(median)
    self._posterior_sld_lower = lo.tolist() if hasattr(lo, 'tolist') else list(lo)
    self._posterior_sld_upper = hi.tolist() if hasattr(hi, 'tolist') else list(hi)
    self.posteriorPredictiveSldDataChanged.emit()

def clear_posterior_predictive_sld(self) -> None:
    self._posterior_sld_z = []
    self._posterior_sld_median = []
    self._posterior_sld_lower = []
    self._posterior_sld_upper = []
    self.posteriorPredictiveSldDataChanged.emit()

@Property('QVariantList', notify=posteriorPredictiveSldDataChanged)
def posteriorPredictiveSldZ(self): return self._posterior_sld_z

@Property('QVariantList', notify=posteriorPredictiveSldDataChanged)
def posteriorPredictiveSldMedian(self): return self._posterior_sld_median

@Property('QVariantList', notify=posteriorPredictiveSldDataChanged)
def posteriorPredictiveSldLower(self): return self._posterior_sld_lower

@Property('QVariantList', notify=posteriorPredictiveSldDataChanged)
def posteriorPredictiveSldUpper(self): return self._posterior_sld_upper
```

##### QML — SldView.qml overlay

Add the same `LineSeries` + `AreaSeries` pattern to the SLD chart:

```qml
// Posterior predictive SLD overlay (Bayesian)
LineSeries {
    id: ppSldMedianSerie
    name: qsTr("Posterior median SLD")
    axisX: chartView.axisX
    axisY: chartView.axisY
    color: "#E67E22"
    width: 2
    visible: Globals.BackendWrapper.bayesianResultAvailable
}

AreaSeries {
    id: ppSldBandSerie
    name: qsTr("95% credible interval")
    axisX: chartView.axisX
    axisY: chartView.axisY
    color: Qt.rgba(0.902, 0.494, 0.133, 0.25)
    borderWidth: 0
    upperSeries: LineSeries { id: ppSldUpperSerie }
    lowerSeries: LineSeries { id: ppSldLowerSerie }
    visible: Globals.BackendWrapper.bayesianResultAvailable
}

Connections {
    target: Globals.BackendWrapper.activeBackend?.plotting ?? null
    enabled: target !== null
    function onPosteriorPredictiveSldDataChanged() {
        ppSldMedianSerie.clear()
        ppSldUpperSerie.clear()
        ppSldLowerSerie.clear()
        var z  = Globals.BackendWrapper.posteriorPredictiveSldZ
        var m  = Globals.BackendWrapper.posteriorPredictiveSldMedian
        var lo = Globals.BackendWrapper.posteriorPredictiveSldLower
        var hi = Globals.BackendWrapper.posteriorPredictiveSldUpper
        if (!z || !m || !lo || !hi) return
        for (var i = 0; i < z.length; ++i) {
            ppSldMedianSerie.append(z[i], m[i])
            ppSldLowerSerie.append(z[i], lo[i])
            ppSldUpperSerie.append(z[i], hi[i])
        }
    }
}
```

The same overlay must be added to the SLD chart in `CombinedView.qml`'s lower
panel (`SldView.qml`), and to any standalone SLD chart view.

### 11.9 Data Flow Summary

```
Sampling completes
  │
  ├─► _on_sample_finished()
  │     ├─► Store posterior dict in Bayesian state
  │     ├─► _compute_diagnostics()        → bayesianDiagnostics (dict)
  │     ├─► _render_corner_plot()         → bayesianCornerPlotUrl (base64 PNG)
  │     ├─► _render_trace_plot()          → bayesianTracePlotUrl (base64 PNG)
  │     └─► _compute_and_publish_posterior_predictive()
  │           ├─► posterior_predictive_reflectivity()
  │           │     → Plotting1d.set_posterior_predictive()
  │           │       → posteriorPredictiveDataChanged signal
  │           │         → CombinedView.qml refreshes ppMedianSerie/ppBandSerie
  │           └─► posterior_predictive_sld_profile()
  │                 → Plotting1d.set_posterior_predictive_sld()
  │                   → posteriorPredictiveSldDataChanged signal
  │                     → SldView.qml refreshes ppSldMedianSerie/ppSldBandSerie
  │
  └─► fittingChanged.emit()
        → QML bindings refresh
          → BayesianPosteriorView subtabs show new data
```

### 11.10 Files to Add / Modify (Phase 2)

#### New Files

| File | Description |
|---|---|
| `Gui/Pages/Analysis/MainContent/BayesianMarginalsView.qml` | Refactored marginal histogram grid |
| `Gui/Pages/Analysis/MainContent/BayesianCornerView.qml` | Corner plot PNG display |
| `Gui/Pages/Analysis/MainContent/BayesianTraceView.qml` | Trace plot PNG display |
| `Gui/Pages/Analysis/MainContent/BayesianHeatmapView.qml` | 2D parameter heatmap |
| `Gui/Pages/Analysis/MainContent/BayesianDiagnosticsView.qml` | Convergence diagnostics panel |

#### Modified Files

| File | Change |
|---|---|
| `Backends/Py/logic/bayesian.py` | Add `corner_plot_url`, `trace_plot_url`, `heatmap_data`, `diagnostics` attributes |
| `Backends/Py/analysis.py` | Add corner/trace PNG rendering, heatmap computation, diagnostics computation, SLD posterior predictive, `heatmapChanged` signal |
| `Backends/Py/plotting_1d.py` | Add SLD posterior predictive properties + signal, `set_posterior_predictive_sld()`, `clear_posterior_predictive_sld()` |
| `Gui/Globals/BackendWrapper.qml` | Forward `bayesianCornerPlotUrl`, `bayesianTracePlotUrl`, `bayesianParamNames`, `bayesianHeatmapData`, `bayesianDiagnostics`, `posteriorPredictiveSld*`, `bayesianComputeHeatmap()` |
| `Gui/Pages/Analysis/MainContent/BayesianPosteriorView.qml` | Become a tab container with `TabBar` + `StackLayout` hosting the 5 sub-views |
| `Gui/Pages/Analysis/MainContent/CombinedView.qml` | Add SLD posterior overlay to lower panel |
| `Gui/Pages/Analysis/MainContent/SldView.qml` | Add SLD posterior overlay |
| `Gui/Pages/Analysis/MainContent/AnalysisView.qml` | Add reflectivity posterior overlay (mirror CombinedView) |
| `Mock/Analysis.qml` | Stub new properties |
| `Mock/Plotting.qml` | Stub SLD posterior predictive properties |

### 11.11 Implementation Order (Phase 2)

1. **Refactor BayesianPosteriorView** into a tab container. Create the 5 stub
   sub-views. Wire the `TabBar` + `StackLayout`. This unblocks parallel
   development of each sub-view.

2. **Backend: bayesian.py attributes** — add `corner_plot_url`,
   `trace_plot_url`, `heatmap_data`, `diagnostics` to the `Bayesian` state
   container. Wire `clear()` to reset all.

3. **Diagnostics subtab** — simplest to implement (text-only). Add
   `_compute_diagnostics()` to `analysis.py`, expose `bayesianDiagnostics`
   property, build `BayesianDiagnosticsView.qml`.

4. **Corner plot subtab** — add `_render_corner_plot()` to `analysis.py`,
   expose `bayesianCornerPlotUrl`, build `BayesianCornerView.qml`.

5. **Trace plot subtab** — add `_render_trace_plot()` to `analysis.py`,
   expose `bayesianTracePlotUrl`, build `BayesianTraceView.qml`.

6. **2D Heatmap subtab** — add `bayesianParamNames`, `bayesianHeatmapData`,
   `computeBayesianHeatmap()` to `analysis.py`, build `BayesianHeatmapView.qml`
   with combo boxes and Plotly/Image display.

7. **SLD posterior predictive overlay** — add SLD data to `plotting_1d.py`,
   overlay series to `SldView.qml` and `CombinedView.qml` lower panel.

8. **Reflectivity overlay in AnalysisView.qml** — mirror the existing
   CombinedView overlay into the standalone AnalysisView.

9. **Mock backend stubs** — add stub properties to `Mock/Analysis.qml` and
   `Mock/Plotting.qml`.

10. **Integration testing** — run a full DREAM sampling workflow in the GUI
    and verify all 5 subtabs populate correctly.

### 11.12 Risks & Mitigations

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | `matplotlib.use('Agg')` may conflict if the GUI imports matplotlib elsewhere. | Use a subprocess or render in the worker thread before the main thread touches matplotlib. Alternatively, use a `matplotlib` lock. |
| 2 | Corner/trace PNGs may be large (several MB as base64). | Use 100 DPI and `bbox_inches='tight'`. Consider writing to a temp file and exposing a `file://` URL instead of a data URL. |
| 3 | `corner` or `arviz` may not be installed on user machines. | All rendering methods catch `ImportError` and expose an empty URL; QML shows a helpful install message. |
| 4 | The 2D heatmap via Plotly WebEngineView adds a dependency on the WebEngine module. | Fall back to PNG rendering (matplotlib `imshow`) if WebEngine is not preferred. |
| 5 | `posterior_predictive_sld_profile()` calls `model.interface.sld_profile()` which may mutate internal model state. | The library function already saves/restores parameter state in a `try/finally` block (see `bayesian.py` lines 331-369). |
| 6 | Rendering corner/trace plots on the main thread could block the UI for seconds. | Defer rendering to a `QTimer.singleShot` after `fittingChanged` is emitted, or render in a background `QThread`. For the first iteration, rendering with 100 DPI for ≤10 params takes <1s, which is acceptable. |
| 7 | The posterior dict may contain `logp` and `state` that are not JSON-serializable (BUMPS objects). | These stay in Python; only primitive types (lists of floats, strings) are pushed to QML properties. |

### 11.13 Future Enhancements (Phase 3)

- **Interactive corner plot** in Qt Charts (GridLayout of scatter+histogram
  ChartViews) for users who prefer native widgets over PNG.
- **Save/load DREAM state** — serialize `state` (BUMPS `DreamState`) to the
  project file so users can resume or extend a sampling run.
- **Per-experiment posterior** — when multiple experiments are loaded, allow
  selecting which experiment's model to use for posterior predictive checks.
- **Live sampling progress** — if BUMPS DREAM eventually supports a
  per-iteration callback, show a live-updating trace plot that grows as
  samples are drawn.
- **Prior specification GUI** — allow users to set prior distributions on
  parameters (beyond simple uniform bounds).
- **Model comparison** — WAIC/LOO cross-validation statistics for comparing
  competing models.
