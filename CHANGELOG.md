# Unreleased

- Interactive tutorials: the `Home` page lists tutorials that can be followed
  step by step in the app. A panel on the left of the pages gives each step,
  frames the control to use, and ticks the step off when the app reaches the
  expected state; **Show me** performs a step, **Skip step** and
  **Restart tutorial** get out of one that cannot be completed. The first
  tutorial is *Simple fitting*. Its steps are written in the online
  documentation, which shows them too, and a test runs every tutorial to the
  end in the application window. A tutorial finished without skipping is
  marked with a tick on the `Home` page.
- An interactive tutorial, *Fitting several contrasts*, starts from an empty
  project: it builds a film model from `film_contrasts.ort` (shipped with the
  app), makes two water contrasts with **Add contrast**, loads and pairs the
  three datasets, fits them together and detaches one parameter. The
  tutorial's page now gives the χ² per point of the three datasets as 0.83
  to 0.92 (it said 0.8 to 0.9).
- An interactive tutorial, *Building a model*, adds a polystyrene layer to the
  polymer film example: a new material in the `Material editor`, a new layer in
  the `Layer editor`, and the result on the `Structure` tab.
- A second interactive tutorial, *Magnetic layers*, works on the iron film
  example: it shows the `ρM` profile, turns the moment with the slider, shows
  it as an arrow on the `Structure` tab and reverses the guide field.
- A layer of a repeating multilayer repeated more than once can no longer be
  made magnetic, and such a stack holding a magnetic layer can no longer be
  repeated: refl1d cannot calculate it, and the whole model then had no
  reflectivity or SLD curve, with only "Repeated magnetic layers not
  implemented" as an explanation. The `Magnetism` group says why the change
  was refused. ORSO imports already warned about this case.
- The θM curve of the SLD chart is drawn against its own axis on the right, as
  intended. The axis used to stack on the left, next to the SLD axis.
- The *Polarised data* tutorial has screenshots of the channel assignment
  dialog, the channel chart, the `Polarization channels` group, the spin
  asymmetry and a fit of the iron example. It lists the file name parts the
  channel detection recognises, says that the spin asymmetry chart plots
  `|SA|`, that the `Analysis` page draws the channels in shades of the
  experiment's colour, and that the model's resolution follows the `pp`
  channel when there is one.
- The *Simple fitting* tutorial walks through a fit of the *Polymer film on
  silicon* example, with new screenshots of both sidebar tabs, the
  `Refinement Results` dialog and the residuals. It describes the `Data
  Explorer`, the parameter table and its slider, the cancel dialog, every
  minimiser setting (`Zero-variance points`, `Preview every (s)` and the
  per-minimiser options) and the `SLD z range` group, and refers to the
  `Sample` page by its current name.
- The *Settings* tutorial has screenshots of the `Preferences` dialog and says
  what each setting does. It notes that the update check, the language and the
  logging level have no effect in this version and that the zoom is not kept.
- The *Summary* tutorial has screenshots of the report, its `Experiments` and
  `Refinement` sections and the exported figure. It says what each row of the
  report means (the "Measured intensity range" is the reflectivity range, not
  the `q` range), what the HTML and PDF exports contain, and how the exported
  figure shifts several experiments and models.
- The *Demo datasets* tutorial covers all seven simulated files, including
  `linked_film_contrasts.ort`, the measured and polarised data and the example
  project built from each. It has screenshots of a sample loaded from a file,
  the warning for a file without a sample model, and the three experiments of
  `film_contrasts.ort`. It no longer says that `ni_ti_multilayer.ort` loads as
  flat layers (it loads as a repeating multilayer), and it corrects what the
  `swapped_layers.ort` demo shows.
- The *Magnetic layers* tutorial has screenshots of the `Magnetism` group, the
  `Magnetic profile` group and the moment arrows on the `Structure` tab, and
  names the page, groups and buttons as the app does.
- The `Instrumental parameters` on the `Experiment` page show the scale,
  background and resolution of the selected experiment's model. Before, they
  showed (and edited) the model selected on the `Sample` page, so with several
  contrasts, selecting e.g. the H2O experiment showed the D2O model's
  background and resolution.
- The background on the `Experiment` page is shown with four significant
  digits (e.g. `9.27e-8`). Before, it was rounded to two decimals, so every
  realistic background showed as `0.00`, and clicking into the field and out
  again set the background to 0. The scale was rounded to three decimals the
  same way. A field now changes the value only when its text was edited, and
  text that is not a number is ignored.
- The *Loading experimental data* tutorial has new screenshots and describes
  the page as it is: the button names, the file formats and columns, where
  the instrumental parameters come from, and adding files to an experiment.
- Bayesian sampling of data without uncertainties (every point zero) is
  refused with a message that says what to do: load the data with an
  uncertainty column, or set **Zero-variance points** to mighell. Before, the
  message named a Python argument. **Zero-variance points** stays in
  `Extra controls` › `Minimization method` when BUMPS-DREAM is selected,
  since sampling uses it too; before, it was hidden there.
- A cancelled sampling run, or a fit cancelled before its first step, is
  reported in a dialog titled *Cancelled* with "Sampling cancelled by user"
  (or "Fitting cancelled by user"). Before, the dialog was titled
  *Refinement Failed* and showed the message as an error.
- The `Diagnostics` view of a Bayesian run shows the number of chains next to
  the population. The population is a factor per parameter (the sampler runs
  population × parameters chains), but the view labelled it as the number of
  chains. Its three sections (configuration, acceptance rate, R̂) are all
  shown at once. Before, they started collapsed and opening one closed the
  others. The sampler's settings have tooltips that say what each one counts.
- The sampling progress bar reaches the end when the run does. It counted
  the population as the number of chains, so with several parameters the
  total number of generations was far too high (e.g. "generation 229 of
  4500" for a run of 1000), and the bar stopped at a fraction of its length.
  The fix is in easyscience.
- The headings of the Bayesian `Marginals`, `Corner Plot`, `Traces` and
  `Diagnostics` views are bold, as intended. The font they asked for did not
  exist, which also logged a QML warning per view.
- The *Bayesian analysis* tutorial walks through a full sampling run on the
  *Polymer film on silicon* example, with screenshots, settings that converge
  in minutes instead of the defaults' hour, and how long a run takes. It
  corrects what the settings mean, where the controls are, when the
  `Bayesian Posterior` tab can be opened, and what happens to data without
  uncertainties.
- The **Add contrast** dialog is half as wide: the name field lines up with
  the replacement choices, and the explanation above wraps to the same width.
- Hovering the **⇄** marker of a shared assembly in the `Model editor` shows
  which other models share it. The tooltip existed but never appeared.
- A model whose sample was loaded from an ORSO file (**Load sample from file**)
  can be renamed in the `Models selector`. Before, it kept showing the
  sample name from the file: every key typed in its name was undone at once.
- **Add contrast** works with a material made with **Add material**. Before,
  choosing such a material as the replacement (e.g. H2O for D2O) left the new
  contrast with a copy of the material it should have replaced, without any
  message: the "H2O" contrast was calculated as D2O, and only a poor fit gave
  it away. Contrasts made with a material loaded from a file, or with a
  duplicated one, were not affected. The fix is in easyreflectometry.
- New tutorial, *Fitting several contrasts together*, which walks through the
  multiple-contrast workflow on the *Film in three water contrasts* and
  *DSPC monolayer, three contrasts* examples (#396): building one model and
  its contrasts with **Add contrast**, what is shared (⇄) and what each
  contrast keeps, pairing experiments with models, the joint fit, detaching a
  shared parameter, when to use **Link contrasts** instead and why shared
  parameters are not in its table, and constraints between contrasts. The
  `Material and model setup` page now has its screenshots of the
  **Add contrast** dialog and the constraint groups.
- The reflectivity plots on the `Sample`, `Experiment` and `Analysis` pages
  show their legend from the start (#400), so with several contrasts on one
  plot each curve can be identified without opening the plot options. The SLD
  and spin asymmetry charts, which share the same toggle, show theirs too. The
  legend button in each chart's toolbar still hides it.
- The `Experiment` plot shows only the current project's data after a project
  is reset or another project or example is loaded. With **Logarithmic
  q-axis** on, the previous project's points used to stay on the plot next to
  the new ones. After **Reset view** (or toggling a plot option) had been used
  once, the axes also kept the previous data's range, so new data could be out
  of view until **Reset view** was clicked again. The axes now follow the data
  whenever its range changes, and a zoom is kept when nothing about the data
  changed.
- Plots are closer to publication-ready (#401). Every chart (reflectivity,
  residuals, SLD and spin asymmetry) is framed on all four sides instead of
  only along the left and bottom axes. With **Logarithmic q-axis** on, minor
  grid lines mark 2×…9× of each decade (and fill the gaps between ticks when
  zoomed in), so values between 0.01 and 0.1 can be read off. A new
  **Marker size** setting next to **Marker style** in the `Experiment` page's
  **Plot control** scales the measured-data markers (or line width) from ×0.5
  to ×4, on the `Experiment` and `Analysis` plots alike.
- Quitting the application while a fit or a Bayesian sampling run is in
  progress no longer crashes it (`QThread: Destroyed while thread is still
  running`). The run is stopped and the application waits for it to end, up
  to 30 s, before exiting; nothing from the stopped run is recorded. Bayesian
  sampling stops only after its current generation, which can take several
  seconds for a multi-contrast model.
- The parameter table on the `Analysis` page names each layer of a multilayer
  (or a surfactant's head and tail) after the layer, e.g. `SiO2 thickness` and
  `Film thickness`, instead of naming both after the assembly. A layer shared
  by several models is no longer prefixed with all their names (the ⇄ marker
  and its tooltip say which models share it), so in *Film in three water
  contrasts* its rows are no longer shortened to an indistinguishable
  `Film in … thickness`. Typing a model's name in the filter still finds the
  layers it shares. Layer rows that would still read alike are numbered.
- With several experiments selected (or a polarized experiment's spin
  channels shown), the reflectivity plots on the `Experiment` and `Analysis`
  pages redraw their data when **Plot R(q)×q⁴** or **Linear R(q)-axis** is
  toggled. Before, the axes changed but the data kept its previous values and
  disappeared from view until the q-axis type was changed, and **Reset view**
  could not bring it back. On the `Experiment` page, **Reset view** also fits
  the y-axis to staggered curves.
- The project name, description and location on the `Project` page wrap onto
  several lines instead of being cut off at the edge of the page, so long
  names and descriptions (such as those of the examples) can be read in full,
  also at the minimum window size.
- Loading an example over an example you have not changed no longer warns
  that unsaved work will be discarded. The warning now appears only once you
  have changed something in the example (or have unsaved work of your own).
- Faster startup. The pages behind the `Project`, `Sample`, `Experiment`,
  `Analysis` and `Summary` tabs are built the first time each tab is opened
  rather than all before the main window appears, and the web engine behind
  the Bayesian plots is loaded only when those plots are first shown, which
  most helps the first launch after a reboot.
- The **Data Explorer** table on the `Analysis` page marks the selected
  experiment(s) again, as the one on the `Experiment` page does.
- A splash screen appears within about a second of launching the application
  and stays animated, with a line naming the current loading step and a
  progress bar showing how much of the startup is left, until the main window
  is drawn. Before, nothing was shown for the 10–40 s the
  application takes to start. `--no-splash` (or the environment variable
  `EASYREFLECTOMETRY_NO_SPLASH=1`) starts without it.
- Linux installer: installing now adds an EasyReflectometryApp icon to the
  desktop and an entry with the app's logo to the Applications menu.
  Uninstalling removes both.

# Version 1.6.1 (22 Nov 2026)

- Example projects: a new **Examples** group on the Project page lists eight
  ready-to-fit projects, from a single polymer film to joint fits of several
  contrasts (derived with Add contrast, or built separately and tied with Link
  contrasts and constraints across contrasts), inequality constraints and
  polarized neutrons, with measured (Platypus, SURF) and simulated data.
  Clicking one loads its sample, data and fit settings. An example is not a saved project: Save stays unavailable until
  **Create a new project** (keeping the sample and data) gives it a location of
  your own, so the shipped files cannot be overwritten. Loading an example over
  unsaved work asks first. The examples are rebuilt with
  `python examples/make_example_projects.py`.
- The Surfactant Layer table shows the area per molecule and the solvation
  again; both read `--` since the move to easyscience 3.
- Adding a contrast of a model with a surfactant layer no longer breaks the
  Material editor, and a project saved in that state opens with a working one.

# Version 1.6.0 (21 Nov 2026)

- Live preview of a running fit: the Analysis page's reflectivity, residual and
  SLD curves are redrawn with the best values found so far, at most once per
  second and only when the fit has improved. **Preview every (s)**, in the
  Minimization method group of the `Extra controls` tab, sets the interval in
  whole seconds (empty: back to 1 s, 0: no preview); it applies from the next fit.
- **Cancel fitting** no longer throws away the progress of a fit. A dialog
  reports the reduced χ² and the number of evaluations (steps for BUMPS) reached,
  with the parameters already at the best values found, and asks:
  - **Keep current values**: the values stay, their uncertainties are cleared (a
    cancelled fit has none), and the run is recorded as cancelled; the status
    bar shows its reduced χ² marked `(cancelled)`.
  - **Revert to starting values**: values and uncertainties go back to what they
    were when the fit started, and the last completed fit stays the recorded one.

  Before, LMFit and DFO went back to the starting values and BUMPS kept its last
  point, with uncertainties. A fit cancelled before its first progress report
  goes back to the starting values without asking.
- The status bar no longer shows the previous project's reduced χ² after a
  project is loaded or reset.
- SLD charts: the z range can be set by hand. A new **SLD z range** group in
  the `Advanced controls` tab of the Sample and Analysis pages has an **Auto**
  box, on by default, which fits the z axis to the calculated profiles as
  before. With **Auto** unchecked, **z-min** and **z-max** set the range that
  **Reset axes** returns to; the first time, they start from the calculated
  range. A range wider than the calculated profile extends the SLD, ρ ± ρM∥
  and ρM curves flat with the fronting and backing values. The setting is
  shared by both pages and is not saved in the project.
- Automatic saving: once a project has been created, it is saved when you leave
  a page, after a successful fit or a Bayesian sampling run, and just before a
  fit, a calculation engine switch or replacing the sample from an ORSO file.
  Each automatic save keeps the file it replaces as `project.json.bak`. The
  status bar marks an automatic save with `(auto)` and shows **Autosave failed**
  while one is failing. **Save automatically**, in the new `Advanced controls`
  tab of the Project page, switches it off.
- Parameter limits are kept as entered (#374):
  - A min or max typed in the Analysis table is no longer refused when the
    current value lies outside it; the value is moved onto the new limit.
  - A value typed on the Sample page (thickness, roughness, SLD, ρM) is no
    longer clamped to the default limits; the limit it passes is moved out.
  - A limit outside the physical range (a negative thickness or roughness, an
    SLD outside -1 to 10, a scale outside 0 to 10) is shown in red, with the
    reason in its tooltip, and is still used by the fit.
- Analysis parameter table: the variability filter has a new default choice,
  **Active parameters**, which hides the greyed rows (constrained, derived and
  unused parameters). **All parameters** shows them as before.
- The new project dialog has a **Cancel** button. (#371)
- Experiment chart: the coordinates tooltip snaps to the nearest measured point,
  so the cursor no longer has to be exactly on a marker.
- Progress of a fit or a Bayesian sampling run:
  - A thin bar along the top of the status bar shows it on every page except
    Home. For sampling it fills up with the generations run so far; a fit has
    no knowable end, so its bar only shows that it is running.
  - Under the **Start/Cancel** button of the Analysis sidebar, now on both the
    `Basic controls` and `Extra controls` tabs: the same bar and a line of text
    with the phase (**Burn-in**, **Sampling**, **Fitting**, **Cancelling…**),
    the generation or evaluation count, the reduced χ² of a fit, and the time
    elapsed. It replaces the bar of the `Basic controls` Fitting group, which
    stood at a fixed 50 % during a fit.
  - The status bar shows the short form (`Sampling 42 %`,
    `132 evaluations · reduced χ² 1.2345`) and hides the Calculator and
    Minimizer items during a run. A sampling run is labelled as one even if
    the minimizer selection is changed while it runs.
- Reflectivity plots on the Sample, Experiment and Analysis pages can show
  R(q) on a linear y-axis: **Linear R(q)-axis** next to **Plot R(q)×q⁴**. The
  two are exclusive, so checking one unchecks the other. The log axis is now
  titled log₁₀(R(q)) or log₁₀(R(q)×q⁴). (#378)
- **Cancel fitting** now stops every minimizer within one evaluation or step.
  LMFit and DFO fits used to run to the end before the cancellation took effect.
  What happens to the parameters is described under the cancel dialog above. A
  cancelled Bayesian sampling run is reported as cancelled instead of as a
  failed fit.
- Sample page: picking a model in the Models table draws only that model in the
  reflectivity and SLD charts, with the axes fitted to it. **Show all models**,
  under the table, draws every model again.
- Analysis page: the SLD chart shows the models of the experiments selected in
  the Data Explorer, like the reflectivity chart, instead of every model. (#462)
- Measured data legends: the symbol matches the chosen marker style (dots,
  circles or line), and the error bounds have their own legend entry. (#457)
- Error bounds (±1σ) are drawn in the colour of their measured points instead of
  a darker shade, and the Analysis reflectivity chart now draws them too. (#460)
- Material editor:
  - **Add material** creates `New material` with its SLD and iSLD entered
    directly, so they can be typed into the table at once. Tick **SLD computed
    from formula and density** to compute them from the formula again.
  - The material move up and move down buttons are removed: layers refer to
    materials directly, so the order of the table has no effect.
- Analysis parameter table, constrained and shared parameters:
  - The dependency of a constrained parameter shows the other parameters by
    their table names, also for a parameter of another model, and replaces
    only whole variable names, so an expression such as `max(a, 0)` is no
    longer garbled. (#365, #366)
  - Hovering the name shows the constraint (`Constrained, read-only: …`), the
    models sharing the parameter, and how many parameters of other models are
    tied to it, even when the name is not shortened.
- A new project now fits with `Bumps_lm` (Levenberg–Marquardt) by default,
  instead of `Bumps_simplex`. Loaded projects keep their own minimizer.
- **Create a new project** now asks first when the session already holds a
  sample, data or fit settings of your own: **Keep sample and data** starts the
  new project with them (as before), **Start from scratch** begins with the
  default sample and no data. The reset only happens once the new project's
  details are confirmed, so cancelling keeps everything as it was.
- Installing over an earlier version:
  the installer no longer stops with "The directory you selected already exists
  and contains an installation". When the chosen folder holds an earlier
  version, it offers to remove that version with its own MaintenanceTool and
  install in its place; declining, or a failed removal, sets a separate folder
  named after the new version instead (e.g. `EasyReflectometryApp-1.6.0`).
- Link contrasts: preview, choose and undo ties:
  - A preview table, **Parameters to tie (n of m ticked)**, lists every parameter
    of the following models that linking would tie, each with a tick box. Untick the
    ones that should stay free, or tick a single material row to tie only that
    material. **Tick all** and **Untick all** set every row; **Show the parameters
    that cannot be tied** adds the rows linking leaves alone, with the reason
    (`per contrast`, `not used`, `material chemistry`, ...).
  - **Reference model** picks which of the ticked models the others follow;
    before, it was always the ticked model highest in the list. The reference is
    marked `(reference)` in the model table.
  - **Also tie material SLDs and densities** now ticks the material rows of the
    preview, so its effect is visible before linking.
  - The preview follows the project: it is updated when the ticked models, the
    reference or the constraints change, and keeps the user's ticks. Why models
    cannot be linked (different layouts) is shown before **Link selected models**
    is pressed. Adding, removing or renaming a model clears the selection.
  - Each link is one row of the new *Model links* table (e.g.
    `Film in CMSi → Film in D2O (5 tied)`) and one row of type `link` in
    *Active Constraints*, instead of one row per tied parameter. Removing it
    removes the whole link; selecting it lists its parameters under **Tied
    parameters of link n**, where each one can be untied on its own. An untied
    parameter gets back the value and bounds it had before the link.
  - The *Model links* table replaces the *Model Constraints* table, which listed
    every constraint of the project, not only the links.
- Equality constraints: the expression placeholder shows a parameter alias
  (`2 * model_d2o_roughness`) instead of `np.sqrt(1 / sld_ni) + 4`, and the
  model-definition tutorial now explains aliases and what an `=` expression may
  contain (units, plain numbers, `pi`, `e`, `sqrt`, ...).
- Superphase and subphase stay fixed when layers change:
  the layer table decided which thicknesses and roughnesses could be edited from
  the assembly alone, locking every layer of the first and last assemblies, and
  adding, removing, duplicating or moving a layer did not move the lock to the
  new first or last layer. Now only the superphase (first layer of the first
  assembly: thickness and roughness) and the subphase (last layer of the last
  assembly: thickness) are locked, the table shows exactly what the fit uses,
  and the lock is set again after every layer change.
- Adding a layer or an assembly to a project that has no `Si` material still
  creates one for the new layer, and the Materials table now shows it at once
  instead of after the next unrelated refresh.
- Bayesian results: the marginal-distribution plot is rendered together with the
  corner and trace plots when sampling finishes, so its tab no longer renders on
  first open, and a plot that failed to render is not retried on every redraw.
- Analysis parameter filters: **model** and **experiment** now go by what owns a
  parameter. Only a model's scale and background are experiment parameters;
  before, any parameter whose name or group contained words such as `scale` or
  `background` (for example one of a material named "Background Material") was
  counted as one. A parameter that is only named `thickness` or `roughness`,
  outside a layer, is no longer labelled with its assembly's name.
- Source cleanup : duplicated
  code and dead code removed (one shared plot-control group for the Experiment,
  Sample and Analysis pages, one definition of the experiment order), typed
  backend slots and properties, and misspelt names corrected. No change in
  behaviour, except that converged R̂ values in the Bayesian diagnostics are now
  shown in green rather than the blue accent colour.
- Built on easyreflectometry 2 and easyscience 3:
  - Projects saved by EasyReflectometry 1.5 or earlier no longer open. Re-create
    them, or open them with EasyReflectometry 1.5.
  - The refl1d engine now smears the curve properly (it oversamples the
    resolution kernel), so refl1d fits give different, more accurate results,
    and they take longer.
  - Removing the last magnetic layer, its assembly or its model now always
    switches magnetism off in the calculation engine.

# Version 1.5.0 (19 Oct 2026)

- Magnetism parameterisation and guide field ([#425](https://github.com/easyscience/reflectometry-lib/issues/425), requirement 4):
  - **Add magnetic material** in the Materials group creates a material with a
    formula, a density and a moment in Bohr magnetons per formula unit (bulk iron
    to start with); the editor shows its ρM and number density.
  - **ρM from material** in the Magnetism group makes the selected layer take its
    ρM from that moment; the ρM cell is then read-only. The moment is greyed in the
    Analysis table until a layer uses it, and with the material's SLD set directly,
    density and moment cannot both be fitted.
  - **Guide field angle** and **Applied field (T)** set the current model's field.
    They appear in the Analysis table while the model is magnetic and the engine is
    refl1d. The H reference follows the field: reversed in-plane, or its angle when
    tilted out of the sample plane; arrows stay in the sample plane, and tooltips
    give the parts of the moment along and across the field.
  - The ρ↑/ρ↓ curves are now labelled ρ ± ρM∥: the nuclear SLD plus and minus the
    magnetic SLD along the field, which are the spin potentials only for moments
    parallel to the field.
  - The `magnetic` parameter filter also shows material moments and the field. A magnetic
    material's derived magnetic SLD is listed as `material rho_m`.
  - Parameters that act on nothing leave the fit, not only the table: a material moment no
    layer takes ρM from, the density of such a material with its SLD set directly, and the
    field of a non-magnetic model. The field controls are shown only for a magnetic model.
  - **Load sample** lists the importer's warnings after a successful load, and refuses a
    magnetic sample under an engine without magnetism without changing the project.
  - The Magnetism table follows density and formula edits of a magnetic material.
- Moment direction is now drawn, not just numbered. One convention, defined once
  in the library: arrows are a top view along the surface normal, screen right is
  the guide field H, and the angle drawn is φ = θM − 270° (a negative ρM points
  the other way, with the signed parameter in the tooltip). A magnetic layer with
  a negligible moment gets a hollow dot; a non-magnetic layer gets nothing, and a
  gradient assembly - which has no single moment - gets nothing either.
  - **Structure tab**: an arrow in every magnetic layer's box, between the name
    and the thickness annotation, with no switch to find - attaching magnetism is
    the request. Tooltips lead with φ, then θM and signed ρM, then the M∥/M⊥ split.
    A magnetism edit now refreshes the boxes; previously a θM change updated the
    chart while the boxes kept the old value.
  - **Magnetism group**: the selected magnetic layer's angle as a 0-360° slider,
    with the H reference and the resulting arrow beside it. Dragging it sets θM
    in 5° steps - the same write the θM column makes - and it is read-only while
    a fit runs or θM follows a constraint.
  - An "H →" reference is on screen wherever an arrow is.
  - A project with no magnetic layer is unchanged: no arrows, no slider, and the
    same Structure and SLD layout as before.
- Variable resolution ([#425](https://github.com/easyscience/reflectometry-lib/issues/425), item 3):
  - Every dataset is shown with the resolution it was measured with. The
    calculated curve and residuals on the Analysis page, the report figures and
    the Bayesian posterior band used the model's resolution, which follows the
    first dataset loaded onto it; a second angle, contrast or spin channel on
    the same model was drawn with the wrong smearing although the fit used the
    right one.
  - Bayesian sampling compares each dataset to the curve the classical fit
    does: it now goes through the library's `Project.prepare_sample()` instead
    of building a `DataGroup` that carried no resolution, so the posterior no
    longer disagrees with the fit when a model has several datasets.
  - "Add file(s) to the selected experiment" on the Experiment page merges more
    measured curves of one contrast (other angles or wavelength bands) into the
    selected experiment; every point keeps its own resolution. A file that
    cannot be added is reported and skipped; one without a resolution column is
    added with an assumed resolution, and a message says so.
  - The model spin cross-sections on the Sample page are calculated without
    smearing by passing a zero width to the one calculation; the model's
    resolution is no longer swapped back and forth, which could disturb a fit
    running at the same time.
  - The polarized import dialog and the polarized-data guide no longer say that
    one resolution is used for the whole experiment.
- Multiple contrasts ([#425](https://github.com/easyscience/reflectometry-lib/issues/425)):
  - New demo files `examples/datasets/film_contrasts.ort` (a film on silicon in
    D2O, H2O and CMSi, with its slab model in the header) and `dppc_contrasts.ort`
    (three contrasts of a DPPC monolayer) for trying Add contrast and a joint fit
    (see the datasets README).
  - "Add contrast of the selected model…" on the Sample page creates a model
    sharing the selected one's structure, with chosen materials replaced (e.g.
    D2O by H2O, which also changes every hydrated layer) or re-formulated
    (isotopic substitution). Its scale, background and resolution are its own.
    A shared assembly is marked ⇄ in the model editor: editing it edits every
    model sharing it.
  - "Model constraints" is now "Link contrasts": it ties the selected models'
    corresponding parameters, but no longer their scale and background, and
    their material SLDs only on request. Layouts that do not correspond are
    reported instead of being tied partially. Removing a tie restores the
    parameter's value and bounds from before the link.
  - The parameters table lists a parameter shared by several models once,
    marked ⇄ with the models in its tooltip; a shared layer parameter can be
    detached for one model.
  - Each experiment's model is chosen per row on the Experiment and Analysis
    pages and shows the stored pairing (the combo used to reset to the first
    model and could change another experiment).
  - A "Fit" checkbox per experiment chooses what the next fit, or Bayesian
    sampling, includes; a parameter that an included model follows stays
    fitted even when its own model is left out. The pre-fit bound checks look
    only at the parameters the fit varies. The results dialog lists each
    dataset's χ² per point and share of the total; the statistics come from
    the library's record of the last completed run, so they survive switching
    the current model and are not replaced by a failed or cancelled run.
  - The Analysis chart has the staggered view too (not in the R·q⁴ view).
  - Linking several models links all of them or, when one cannot be linked,
    none.
  - Removing a model that experiments use asks whether to remove them or fit
    them with another model; experiments are no longer removed by position.
  - A data file that cannot be read is reported in a dialog.
  - The HTML report lists all models, with the model each contrast was derived
    from.
- The legacy synchronous fit path (`Fitting.start_stop`) was removed; the GUI
  always fitted in a worker thread.

- Added a **Structure** tab on the Model page: a schematic view of the layer stack with one
  colored box per layer (colors per material, heights following thickness, "× N" badges for
  collapsed repeating multilayers, legend and total-thickness caption). Boxes show tooltips
  with material/SLD/thickness/roughness, clicking selects the layer in the sidebar editor,
  and the view updates live on edits and after fits ([#242](https://github.com/easyscience/reflectometry-lib/issues/242)).
- Enabling magnetism no longer jumps to another page. Ticking a layer's
  "Magn." box while the current engine cannot model magnetism now asks whether
  to switch the project to refl1d and does both in one step. 
  The calculation engine has its own group on the Sample page.
- Selecting an engine that cannot model magnetism, while the sample already has
  magnetic layers, is refused with a message on both pages.
- Fixed the calculation-engine selector showing the wrong engine after loading
  a project that used a different one.
- Magnetic depth profiles on the SLD chart (Sample and Analysis share the
  chart):
  - Once a layer is magnetic, the chart adds the spin-up and spin-down
    potentials ρ ± ρM·cos(θM − A) for each magnetic model, dashed in the
    model's colour. ρM and the moment angle θM each have a checkbox; θM uses
    its own right-hand axis. The y-range covers every visible curve and grows
    when a curve is switched on, so ρ + ρM is not clipped. θM is only defined
    where there is a moment, and that curve is drawn in pieces, not joined
    across the gaps.
  - The switches are in a new "Magnetic profile" group under Magnetism on the
    Sample page, and in Analysis under "Plot control". Both use the same
    selection.
  - If no model is magnetic, the chart, legend and sidebar are unchanged.
- The "Magnetic profile" group gained a "Show R↑↑ and R↓↓" switch: the Sample
  page reflectivity chart then splits each magnetic model into its two
  non-spin-flip cross-sections, dashed in the model's colour with their own
  legend rows. Off by default, and hidden while no model is magnetic. Note that
  for a magnetic sample the plain model curve is **not** an unpolarized average
  — the calculator returns the up-up cross-section — so R↑↑ is drawn on top of
  it; the sidebar says so. The Analysis chart is unaffected: it already draws
  one calculated curve per measured spin channel when the experiment is
  polarized.
- Spin-asymmetry view, SA(q) = (R↑↑ − R↓↓)/(R↑↑ + R↓↓):
  - A "Spin asymmetry" tab on the Experiment page (measured data) and a third
    tab on the Analysis page's lower panel (measured data plus the model).
    Neither is shown unless the experiment measured both non-spin-flip
    channels. Without one, Experiment has no tab strip.
  - Error bars come from the channel uncertainties. Points where R↑↑ + R↓↓ is
    not significantly above zero (the background-dominated tail) are dropped,
    with a note of how many, so they do not wreck the axis. Same for points
    where the two channels do not share the same q. The axis shows the full
    [−1, 1] window and expands if background-subtracted data go outside it.
- Polarized (spin-channel) experiment import and display:
  - New "Load polarized experiment (file per channel)" flow: multi-select one
    file per spin channel, then review and edit the automatic assignment (from
    the ORSO `polarization` header or the file name). Any number of channels
    can be assigned, including a single channel. Files can be marked "not
    used". Duplicate or unknown channels, missing files, or nothing assigned
    are rejected with a message.
  - The experiment chart draws one measured series (plus error bounds) per
    visible spin channel in a fixed palette (↑↑ pp, ↑↓ pm, ↓↑ mp, ↓↓ mm), with
    a channel selector in the sidebar and a per-channel legend. At least one
    measured channel stays visible. With several experiments selected, each
    polarized experiment contributes one series per visible channel, using the
    experiment colour as the hue base.
  - Experiment lists mark polarized experiments with a `⇅N` badge for the
    number of measured spin channels.
  - Report figures plot each channel's spin cross-section in its channel
    colour. A channel that cannot be calculated (for example spin-flip on a
    non-magnetic model) is shown as measured data only.
  - Each channel is fitted, drawn and reported with the resolution of its own
    file (see "Variable resolution" above).
  - **Limitation:** Bayesian sampling of polarized experiments is not
    supported yet.
  - Project save/load now fully supports polarized experiments.
- Magnetism editing and polarized fitting:
  - New "Magnetism" group on the Sample page: one row per layer of the current
    assembly, with a magnetic on/off checkbox, magnetic SLD (ρM) and in-plane
    moment angle (θM). Only refl1d can model magnetic layers. The group says
    so and offers to switch the project's calculation engine when a layer is
    made magnetic (see above).
  - ρM and θM appear in the Analysis parameter table like other layer
    parameters, named after their assembly and model (`Model Fe rho_m`), with
    default limits, fit checkboxes and constraints. The name filter accepts
    "magnetic" as a keyword.
  - Fitting a polarized experiment fits all its measured spin channels at once
    against the shared model. Thickness, roughness, nuclear SLD, scale and
    background are common to every channel; ρM and θM are constrained by all
    of them. Polarized and ordinary experiments can be fitted together. This
    used to report "not supported yet".
  - The analysis and residual charts draw one measured/calculated pair per
    visible spin channel, each with that channel's cross-section. Previously
    only the first visible channel was shown. A channel the model cannot
    calculate (spin-flip on a non-magnetic sample) shows measured points only
    and contributes no residuals.
- Density materials (formula + mass density, as loaded from ORSO) now have a
  detail panel on the Sample page: an editable chemical formula and density,
  and a **"SLD computed from formula and density"** checkbox. Checked
  (default), SLD/iSLD are read-only and derived; unchecked, they become
  ordinary fittable parameters while density and the scattering lengths are
  greyed out as unused. The molecular weight is a formula constant and never
  appears as a fittable parameter. A ρ badge marks density materials in the
  materials table. Re-checking the box recalculates SLD/iSLD, discarding any
  manually entered or fitted values and any constraint on them.
- Parameter table rows where the minimizer produced no error bars (e.g. some
  gradient-free methods) now show `n/a` instead of a blank/error cell.

# Version 1.4.0 (3 Aug 2026)

- Added Bayesian analysis: run MCMC sampling alongside classical fitting, with posterior median and credibility intervals on the main chart, trace/corner-style plots per parameter, a dedicated status display with cancellation support, and plot export.
- Bayesian results are now cleared whenever they become stale: on project create/load/reset, when a classical fit starts, and when a new sampling run starts. Previously the posterior overlays, plots and the "Bayesian Sampling Results" dialog could show results from a superseded run or a different project.
- Cancelling a fit now keeps the UI locked until the worker thread actually exits, and late signals from a superseded worker are ignored. This prevents two fits from mutating the shared parameters concurrently when the minimizer cannot abort mid-run (lmfit, DFO).
- Bayesian sampling no longer fails for data files without uncertainty/resolution columns: missing `ye` falls back to zero variances (reported by the sampler with a clear message) and the unused `xe` is no longer attached to the Q coordinate.
- Fixed wrong parameter group/display names for the first and last layers of each assembly: the parameter-tree walker now prefers the canonical `layers` container over the `front_layer`/`back_layer` alias properties.
- Removed the unused `corner` dependency.
- Migrated to the new `easyscience` core API surface exposed by `reflectometry-lib`:
  - Layer removal now calls `remove_at(index)`; the lib's index-based `remove` was replaced by standard `MutableSequence.remove(value)` semantics.
  - Parameter discovery uses `get_all_parameters()`.
- **Breaking:** project files saved by earlier versions (predating `file_format=2`) can no longer be opened. Opening one now shows a clear error dialog instead of failing uncaught; affected projects must be recreated.

# Version 1.3.0 (1 May 2026)

- Migrated the application to the new `EasyApplication` module and removed the old `EasyApp` footer dependency.
- Combined layer and model editors and fixed list handling/stability issues.
- Improved residuals display, including zero-value handling, correct scaling, and better log-scale support.
- Updated chart and analysis UI: dotted experiment lines, better legend symbols, and improved plot colors.
- Fixed experiment color display for partial experiment selections.
- Added a DFO-style fitting status display with animated "Fitting running ..." dots and a status-bar counter.
- Improved experiment tab behavior for changed resolution percentages.
- Updated chart reset controls and reset iconography.
- Improved app reset behavior and empty-project wording.
- Enabled Windows code signing and updated installation links for `v1.3.0`.
- Miscellaneous bug fixes and usability improvements.

# Version 1.2.0 (1 March 2026)

Added ORSO file parser
Added simple constraints
Added model-model constraints
Enabled multi-sample display
Enabled multi-experiment display
Improved plotting
Enhanced status bar display
Moved SLD plot to main display

