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
