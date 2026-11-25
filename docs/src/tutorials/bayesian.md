# Bayesian analysis

Besides the classical minimisers, the app can sample the posterior distribution of the
fitted parameters with the BUMPS DREAM sampler. For each parameter you then get a
distribution instead of a single best value: a median, a credible interval, and the
correlations between parameters.

## Starting a sampling run

You select Bayesian sampling the same way as a minimiser. In `Analysis` › `Advanced` ›
**Minimization method**, choose **BUMPS-DREAM (Bayesian)**, the first entry of the
**Minimizer** drop-down.

<!-- TODO: screenshot of the Minimization method group in Bayesian mode -> _images/anal_bayesian_settings.png -->

The settings below the drop-down depend on the choice. Instead of the classical
**Tolerance** and **Max evaluations**, the sampler has these settings:

| Setting | Meaning |
|---|---|
| **Samples** | Total number of samples to draw. |
| **Burn-in steps** | Initial steps discarded before the chains are recorded. |
| **Population** | Number of chains walking the parameter space. |
| **Thinning** | Keep every n-th draw, to reduce autocorrelation. |
| **Initializer** | How the starting population is spread over the parameter ranges. |

As with a classical fit, the sampled parameters and their ranges are the ones ticked for
fitting in the `Basic controls`.

With the Bayesian minimiser selected, the fit button below the sidebar (on both the
`Basic controls` and the `Extra controls` tabs) reads **Start sampling** instead of
**Start fitting**. While a run is in progress it reads **Cancel fitting**. After you
cancel, the interface stays locked until the worker has stopped, so an old run cannot
write into the parameters of the next one. A cancelled run is reported as cancelled, not
as a failed fit.

While a run is in progress, a thin bar along the top of the status bar and a progress bar
with a line of text under the button show how far it has got. For sampling, the bar fills
up, and the text shows the phase (**Burn-in**, then **Sampling**), the current generation
out of the total, and the elapsed time. A classical fit has no known end, so its bar only
shows that it is running. Its text gives the number of evaluations (optimizer steps for a
BUMPS minimiser), the reduced χ² and the elapsed time. The status bar shows a short form,
for example `Sampling 42 %`, on every page except `Home`; see
[simple fitting](./simple_fitting.md).

## Reading the results

### On the reflectivity chart

When a run finishes, two curves are added to the `Reflectivity` tab of the `Analysis`
page, each with its own legend entry:

- **Posterior median**: the median calculated curve over the retained draws.
- **95% credible interval**: the band containing 95 % of the posterior predictive curves.

### The Bayesian Posterior tab

The `Analysis` page has a second main tab, **Bayesian Posterior**, with five views. Until a
run has finished, it shows *"No Bayesian results available. Run a BUMPS-DREAM sampling to
see posterior distributions."*

<!-- TODO: screenshot of the Bayesian Posterior tab -> _images/anal_bayesian_posterior.png -->

| View | Shows |
|---|---|
| **Marginals** | Marginal posterior distribution of each sampled parameter. |
| **Corner Plot** | Pairwise parameter correlations together with the marginals. |
| **Traces** | The MCMC chain traces, for checking mixing and burn-in by eye. |
| **2D Heatmap** | Joint posterior density of any two parameters, chosen with the **X-axis** and **Y-axis** selectors. |
| **Diagnostics** | Convergence diagnostics, see below. |

Each view has a **Save** button that saves the plot to disk.

```{note}
The **Marginals**, **Corner Plot** and **Traces** views use `plotly`. If it is not
installed, the view says so and shows the install command. The rest of the app works as
usual.
```

### Diagnostics

The **Diagnostics** view helps you judge whether the run can be trusted:

- **Sampling Configuration**: the samples, burn-in steps, thinning, population (chains),
  retained draws and number of parameters that the run actually used.
- **Acceptance Rate** of the sampler.
- **Gelman-Rubin R̂** for each parameter. Values close to 1 mean that the chains have
  converged on the same distribution.

## When results are discarded

Posterior results belong to one run of one model. The app therefore clears them (the
overlays, the plots and the results dialog) whenever they would become out of date:

- when a project is created, loaded or reset,
- when a classical fit is started,
- when a new sampling run is started.

## Limitations

- Polarised experiments cannot be sampled yet. You can fit them with a classical
  minimiser (see [polarised data](./polarized_data.md)), but not run a Bayesian analysis
  on them.
- Data files without an uncertainty column are sampled with zero variances, and the
  sampler shows a message about it. The run still completes, but do not read the resulting
  credible intervals as measurement uncertainties.
