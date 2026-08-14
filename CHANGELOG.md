# Unreleased

- Added polarized (spin-channel) experiment import and display:
  - New "Load polarized experiment (file per channel)" import flow: multi-select
    one file per spin channel, then review and edit the automatic channel
    assignment (from the ORSO `polarization` header or the file name) in the
    assignment dialog. Any number of channels may be assigned — a single-channel
    experiment is allowed — and files can be excluded with "not used". Invalid
    assignments (duplicate or unknown channels, missing files, nothing assigned)
    are rejected with a message instead of quietly loading nothing.
  - The experiment chart draws one measured series (plus error bounds) per
    visible spin channel in a fixed channel palette (↑↑ pp, ↑↓ pm, ↓↑ mp,
    ↓↓ mm), with a channel selector in the experiment sidebar and a per-channel
    legend. At least one measured channel always stays visible. With several
    experiments selected, each polarized experiment contributes one series per
    visible channel, keeping the experiment color as hue base.
  - Experiment lists mark polarized experiments with a `⇅N` badge showing the
    number of measured spin channels.
  - Report figures plot each channel's own spin cross-section in its channel
    color; a channel that cannot be calculated (e.g. spin-flip on a
    non-magnetic model) is shown as measured data without a calculated overlay.
  - **Limitations:** one resolution function is used per polarized experiment
    (taken from the first assigned channel — stated in the import dialog);
    fitting and Bayesian sampling of polarized experiments are not supported yet
    and report a clear message; the analysis and residual charts show the first
    visible channel only; polarized experiments are not yet saved in project
    files.
  - Requires an `easyreflectometry` version with the per-channel experiment API;
    the app reports a clear error instead of drawing empty charts if it is
    missing.

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

