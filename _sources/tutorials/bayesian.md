# Bayesian analysis

Next to the classical minimisers the app can sample the posterior distribution of the fitted
parameters with the BUMPS DREAM sampler. Instead of a single best value per parameter you
get a distribution: a median, a credible interval, and the correlations between parameters.

## Starting a sampling run

Bayesian sampling is selected like a minimiser. In `Analysis` › `Advanced` ›
**Minimization method**, pick **BUMPS-DREAM (Bayesian)** - the first entry of the
**Minimizer** drop-down.

<!-- TODO: screenshot of the Minimization method group in Bayesian mode -> _images/anal_bayesian_settings.png -->

The settings below the drop-down change with the choice. Instead of the classical
**Tolerance** and **Max evaluations**, the sampler shows:

| Setting | Meaning |
|---|---|
| **Samples** | Total number of samples to draw. |
| **Burn-in steps** | Initial steps discarded before the chains are recorded. |
| **Population** | Number of chains walking the parameter space. |
| **Thinning** | Keep every n-th draw, to reduce autocorrelation. |
| **Initializer** | How the starting population is spread over the parameter ranges. |

The parameters that are sampled, and the ranges they are sampled in, are the ones ticked
for fitting in the `Basic controls`, exactly as for a classical fit.

With the Bayesian minimiser selected, the fit button in `Basic controls` reads
**Start sampling** instead of **Start fitting**. It becomes **Cancel fitting** while a run
is in progress; cancelling keeps the interface locked until the worker has actually
stopped, so a superseded run can never write into the parameters of the next one.

## Reading the results

### On the reflectivity chart

When a run finishes, the `Reflectivity` tab of the `Analysis` page gains two extra items,
with their own legend entries:

- **Posterior median** - the median calculated curve over the retained draws.
- **95% credible interval** - the band containing 95 % of the posterior predictive curves.

### The Bayesian Posterior tab

The `Analysis` page has a second main tab, **Bayesian Posterior**, holding five views.
Until a run has finished, it shows *"No Bayesian results available. Run a BUMPS-DREAM
sampling to see posterior distributions."*

<!-- TODO: screenshot of the Bayesian Posterior tab -> _images/anal_bayesian_posterior.png -->

| View | Shows |
|---|---|
| **Marginals** | Marginal posterior distribution of each sampled parameter. |
| **Corner Plot** | Pairwise parameter correlations together with the marginals. |
| **Traces** | The MCMC chain traces, for eyeballing mixing and burn-in. |
| **2D Heatmap** | Joint posterior density of any two chosen parameters - pick them with the **X-axis** and **Y-axis** selectors. |
| **Diagnostics** | Convergence diagnostics, see below. |

Each view has a **Save** button that writes the plot to disk.

```{note}
The **Marginals**, **Corner Plot** and **Traces** views are rendered with `plotly`. If it is
not installed the view says so and gives the install command; the rest of the app is
unaffected.
```

### Diagnostics

The **Diagnostics** view reports whether the run can be trusted:

- **Sampling Configuration** - requested samples, burn-in steps, thinning, population
  (chains), retained draws and number of parameters, as actually used by the run.
- **Acceptance Rate** of the sampler.
- **Gelman-Rubin R̂** per parameter. Values close to 1 indicate that the chains have
  converged on the same distribution.

## When results are discarded

Posterior results describe one specific run of one specific model, so the app clears them -
the overlays, the plots and the results dialog - as soon as they would become stale:

- when a project is created, loaded or reset,
- when a classical fit is started,
- when a new sampling run is started.

## Limitations

- **Polarised experiments cannot be sampled yet.** Fitting them classically is supported,
  see [polarised data](./polarized_data.md), but a Bayesian run over a polarised experiment
  is not available.
- Data files without an uncertainty column are sampled with zero variances, which the
  sampler reports with a message. The fit is still performed, but the resulting credible
  intervals should not be read as measurement uncertainties.
