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

