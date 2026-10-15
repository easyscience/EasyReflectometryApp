# Unreleased

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

