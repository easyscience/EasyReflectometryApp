# Simple fitting with a slab model
For this purpose, we have created a simple slab model which is discussed in detail in the [model-dependent analysis](https://www.reflectometry.org/isis_school/2_model_dependent_analysis/what_is_model_dependent_analysis.html) and [reflectometry slab models](https://www.reflectometry.org/isis_school/3_reflectometry_slab_models/the_slab_model.html) sections of the ISIS Virtual Reflectometry Training Course on [neutron reflectometry fitting](https://www.reflectometry.org/isis_school/intro.html). 

The system that we are investigating consists of four layers (with the top and bottom as semi-finite super- and sub-phases). 
The super-phase (where the neutrons are incident first) is a silicon (Si) wafer and as a process of the sample preparation, there is anticipated to be a layer of silicon dioxide (SiO<sub>2</sub>) on this material.
Then a polymer film is attached to the silicon dioxide by some chemical method and this polymer film is solvated in heavy water (D<sub>2</sub>O) which also makes up the sub-phase of the system. 
This is shown pictorially below, as a slab model. 

![A slab model description of the polymer film system.](./_images/polymer_film.png)

Now for explaining the `Analysis` tab let's look at how the EasyReflectometryApp can fit. The tab is like the previous tabs split into two windows, a graph- and a data-window.<br>
The graph window has the same functionality as the previous tabs, so it will not be explained further. The data window has two categories: `Basic` and `Advanced` controls.

## Basic controls 
The basic controls is for fitting the variables.

![Basic analytics](./_images/anal_bsc.png)

- **A**: Picking the desired variable to use the slider for fine-tuning it.
- **B**: Able to change the specific variable.
- **C**: Setting the minimum variable for fitting.
- **D**: Setting the maximum variable for fitting.
- **E**: Choose the variable for fitting.
- **F**: Fit the chosen variable (**E**) between the min. (**C**) and max. (**D**).

### Filtering the parameter table
Two drop-downs above the table choose which parameters it lists. Each entry shows the
number of parameters it matches.

- **Filter by name**: `All names`, `Model`, `Experiment` or `Background`, or type part of a
  name in the field next to it. `Model` and `Experiment` go by what owns the parameter: only
  a model's scale and background are experiment parameters, whatever the others are called.
- **Filter by variability**:

| Choice | Lists |
|---|---|
| **Active parameters** (the default) | The parameters that can be edited and fitted. |
| **All parameters** | The same, plus the greyed rows: constrained and derived parameters, and parameters that currently do not affect the reflectivity. |
| **Free parameters** | The active parameters ticked for fitting. |
| **Fixed parameters** | The active parameters not ticked for fitting. |

A parameter that a constraint takes over disappears from the default view; switch to
**All parameters** to see its value.

### Limits
The app gives a new parameter default limits: -1 to 10 for an SLD (in
10<sup>-6</sup>Å<sup>-2</sup>), 0 to 10 for the scale, and 50 % to 200 % of the starting
value for a thickness or a roughness. These are starting points, not rules:

- A min (**C**) or max (**D**) you type is kept as typed. If the current value lies outside
  the new limit, the value is moved onto it. A min at or above the max (or a max at or below
  the min) is not accepted.
- A value typed in the table (**B**) stays within the limits next to it. Widen the limit
  first to go further.
- A value typed on the `Model` page - a thickness, a roughness, an SLD, a `ρM` - has no
  limits beside it, so there the value wins: a limit it passes is moved out to the new
  value.

A limit outside what is physically possible - a negative thickness or roughness, an SLD
outside -1 to 10, a scale outside 0 to 10 - is shown in red, and hovering it gives the
reason. The limit is still the one the fit uses; the colour only marks it as unusual.

A limit is also red when it is `inf` for a fitted parameter while the selected minimiser
needs finite limits for every fitted parameter.

### Starting, following and cancelling a fit
The **Start fitting** button sits below the sidebar on both the `Basic controls` and the
`Extra controls` (advanced) tabs. While a fit runs it reads **Cancel fitting**, and a progress bar
with a line of text appears under it: the number of evaluations so far (optimiser steps for
a BUMPS minimiser), the reduced χ² and the time elapsed. A fit has no knowable end, so the
bar only shows that it is running.

The same is shown in short form on every page except `Home`: a thin bar along the top of
the status bar, and a **Fit** item (e.g. `132 evaluations · reduced χ² 1.2345`) that takes
the place of the **Calculator** and **Minimizer** items for the duration of the run.

**Cancel fitting** stops any minimiser within one evaluation or step. A cancelled LMFit or
DFO fit puts the parameters back to the values they had before the fit.

## Advanced controls
The advanced control is then for changing the calculation engine and setting the minimisation method.

![Advanced analytics](./_images/anal_adv.png)

- **A**: Changing the calculation engine between `refnx` and `refl1d`.<br></br>
- **B**: Setting the minimisation method for minimising variables.
- **C**: Specifying the tolerance of the set minimiser.
- **D**: Setting the maximum number of iterations(evaluations) for the minimiser to run.

The calculation engine (**A**) is also available on the `Model` page, in its advanced
controls; both selectors change the same project setting. Note that only `refl1d` can model
magnetic layers, so a sample with magnetism cannot be calculated with `refnx` - see
[magnetic layers](./magnetism.md).

A new project fits with `Bumps_lm` (Levenberg-Marquardt) unless another minimiser is
chosen. A loaded project keeps the minimiser it was saved with.

The first entry of the minimiser list (**B**), `BUMPS-DREAM (Bayesian)`, does not minimise
but samples the posterior distribution of the fitted parameters; it replaces **C** and **D**
with its own sampling settings. See [Bayesian analysis](./bayesian.md).

### Plot control
The **Plot control** group of the advanced controls sets how the reflectivity chart is
drawn. The same group is in the advanced controls of the `Model` and `Experiment` pages,
and the choice applies to all three.

- **Plot R(q)×q⁴**: plots the reflectivity multiplied by q⁴, which flattens the Fresnel
  decay and brings out the fringes.
- **Linear R(q)-axis**: plots R(q) on a linear axis instead of a logarithmic one. This and
  **Plot R(q)×q⁴** exclude each other: ticking one unticks the other.
- **Logarithmic q-axis**: makes the q-axis logarithmic.
- **Show scale line** and **Show background line**: draw the model's scale and background
  as reference lines. They are not offered on the `Model` page, which shows no measured
  data.

The axis title says what is plotted: R(q) or R(q)×q⁴ on a linear axis, log₁₀(R(q)) or
log₁₀(R(q)×q⁴) on a logarithmic one.

## Residuals
The lower panel of the `Analysis` page has three tabs: `SLD`, `Residuals` and, for a
polarised experiment that measured both non-spin-flip channels, `Spin asymmetry`.

The `Residuals` tab plots the weighted residual `(M-E)/σ` against `q` - the difference
between the model and the experiment, in units of the measured uncertainty. A good fit
scatters evenly around zero with no structure left in it; a systematic wave or a drift means
the model is missing something. The tab has the same legend, hover, zoom, pan and reset
controls as the other charts, and its q-axis follows the logarithmic setting of the
reflectivity chart.

With several experiments, or with a polarised experiment, the tab draws one residual curve
per visible measured series. A spin channel the model cannot calculate contributes no
residuals.
