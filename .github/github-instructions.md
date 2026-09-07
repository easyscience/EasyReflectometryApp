# EasyReflectometryApp Project Gist

## Project Purpose

EasyReflectometryApp is the Qt/QML desktop application for EasyReflectometry. It provides a GUI for modelling, simulation, fitting, and reporting of reflectometry data. The app focuses on an intuitive workflow around projects, samples, experiments, analysis, and summaries.

Core user-facing capabilities include:

- Loading reflectometry datasets and project files.
- Building layered sample structures with materials, models, assemblies, and constraints.
- Simulating reflectivity and SLD profiles.
- Fitting single and multiple experiments through EasyReflectometryLib and EasyScience fitting backends.
- Switching calculators/minimizers where supported.
- Producing HTML/PDF reports and plot exports.
- Packaging cross-platform installers for Windows, macOS, and Linux.

## Repository Shape

Important paths:

- `EasyReflectometryApp/main.py`: runtime entry point. Registers `PyBackend` as the QML singleton module `Backends` and loads `Gui/ApplicationWindow.qml`.
- `EasyReflectometryApp/Gui/`: Qt6/QML UI. Pages follow the workflow: Project, Sample, Experiment, Analysis, Summary.
- `EasyReflectometryApp/Gui/Globals/BackendWrapper.qml`: the GUI-facing wrapper around the active backend. QML should access backend data and methods through this wrapper.
- `EasyReflectometryApp/Backends/Py/`: Python backend adapters exposed to QML through PySide6 properties, slots, and signals.
- `EasyReflectometryApp/Backends/Py/logic/`: app-specific backend logic without PySide/QML dependencies. Prefer adding business logic here.
- `EasyReflectometryApp/Backends/Py/workers/`: threaded/background workers, especially fitting.
- `EasyReflectometryApp/Backends/Mock/`: QML mock backend for UI development without the Python backend.
- `tests/`: pytest coverage for Python backend logic, workers, QML-facing adapters, and selected QML UI behavior.
- `src_qt5/`: legacy Qt5 implementation. Use as a migration reference only; do not extend it for new Qt6 behavior.
- `tools/Scripts/`: installer and CI helper scripts.
- `.github/workflows/`: installer, docs, and snap workflows.

## Main Architecture

The application is a PySide6/QML frontend over a Python backend that uses `easyreflectometry` from EasyReflectometryLib and EasyScience/core underneath.

Backend layering matters:

- Root modules in `Backends/Py/*.py` are QML API adapters. They expose `Property`, `Signal`, and `Slot` definitions and should stay thin.
- Domain behavior belongs in `Backends/Py/logic/*.py` where it can be tested without QML or PySide.
- `PyBackend` owns one shared `easyreflectometry.Project` instance and constructs page-specific backend adapters: `Home`, `Project`, `Sample`, `Experiment`, `Analysis`, `Summary`, `Status`, and `Plotting1d`.
- `PyBackend._connect_backend_parts()` is the cross-page signal hub. When sample, experiment, analysis, or project state changes, make sure the relevant status, summary, parameter cache, and plot refresh signals are emitted.
- `Gui/Globals/BackendWrapper.qml` intentionally flattens backend access for QML. When adding a backend property or method that QML uses, add the Python backend API, the BackendWrapper bridge, and the mock backend equivalent.

Typical data flow:

1. QML calls a `Globals.BackendWrapper.*` function.
2. The wrapper delegates to `activeBackend`, normally `PyBackend` or `MockBackend`.
3. A root Python adapter validates/coerces QML-friendly values and delegates to a logic module.
4. Logic mutates or queries the shared EasyReflectometryLib project.
5. The adapter emits signals so QML bindings, status text, summaries, and plots refresh.

## Local Multi-Repository Context

This workspace usually contains related repositories side by side:

- `EasyReflectometryApp`: this GUI app.
- `EasyApplication`: shared QML/GUI shell and components.
- `reflectometry-lib`: EasyReflectometryLib domain package.
- `core`: EasyScience core framework and fitting internals.

`pyproject.toml` currently depends on:

- `easyapplication`
- `easyreflectometry @ git+https://github.com/EasyScience/EasyReflectometryLib.git@interim_updates`
- `PySide6`, `toml`, and `asteval`

When debugging runtime behavior, verify the active Python environment imports the intended local editable packages. Fitting progress and minimizer behavior can depend on matching changes in `core` and `reflectometry-lib`.

Useful local environment note from this workspace: the `era` conda environment is commonly used. If fit-progress support looks stale, reinstall local core with the selected environment, for example:

```powershell
C:/Users/piotrrozyczko/.conda/envs/era/python.exe -m pip install -e C:/projects/easy/ERA/core
```

## Development Commands

Install for development from the app repo:

```powershell
pip install -e .
```

Install test extras:

```powershell
pip install -e .[test]
```

Run the app locally:

```powershell
python EasyReflectometryApp/main.py
```

Run in test mode:

```powershell
python EasyReflectometryApp/main.py --testmode
```

Run tests:

```powershell
pytest
pytest --cov=EasyReflectometryApp --cov-report=term-missing
```

Run Ruff formatting/linting:

```powershell
python -m ruff .
python -m ruff . --fix
python -m ruff format .
```

## Code Style

Follow the project `pyproject.toml` settings:

- Python 3.11+.
- Line length: 127.
- Single quotes for Python strings.
- Ruff is the formatter/linter.
- Imports are sorted by Ruff/isort with forced single-line imports.
- Test assertions are allowed in `test_*.py` files.

General style:

- Keep QML-facing adapters small and explicit.
- Put testable behavior in `Backends/Py/logic`.
- Avoid PySide imports in logic modules.
- Prefer meaningful names and explicit state transitions over hidden side effects.
- Use existing EasyApp QML components and project layout patterns rather than inventing new UI primitives.
- Keep legacy `src_qt5` as read-only reference unless an explicit migration task says otherwise.

## QML And Backend Contracts

When adding or changing a GUI feature, usually update all of these together:

- Python adapter in `EasyReflectometryApp/Backends/Py/*.py`.
- Logic module in `EasyReflectometryApp/Backends/Py/logic/*.py` if behavior is non-trivial.
- `Gui/Globals/BackendWrapper.qml` bridge.
- `Backends/Mock/*.qml` equivalent for mock mode.
- Affected page/component under `Gui/Pages/...`.
- Tests under `tests/`.

QML binding guidance:

- Access backend state through `Globals.BackendWrapper`, not directly through `PyBackend`, unless the local pattern already requires direct signal connections.
- Prefer backend signals over polling when state changes originate in Python.
- Avoid binding loops by making ownership of writable state clear. Writable backend values should normally have explicit setter functions in `BackendWrapper.qml`.
- Dynamic chart series need careful timing. If QML creates series dynamically, ensure series are registered with the backend before Python plotting code attempts to populate them.
- Keep Mock backend APIs in sync with PyBackend APIs so UI work can continue without the Python backend.

## Fitting And Plotting Notes

Fitting is one of the highest-risk areas:

- `Analysis` orchestrates fitting state and worker lifecycle.
- `Backends/Py/logic/fitting.py` prepares data, models, weights, minimizer options, and fit result state.
- `Backends/Py/workers/fitter_worker.py` runs fitting off the UI thread and emits result/failure/progress signals.
- Multi-experiment fitting uses EasyReflectometryLib `MultiFitter`, then often calls into the underlying EasyScience/core fitter.
- Avoid UI-thread reads of worker-mutated model state during a fit. Prefer immutable snapshots or explicit preview state for interim plotting.
- Cancellation has historically been tricky. Do not assume forceful `QThread.terminate()` is safe; prefer cooperative callback-based cancellation where the minimizer supports it.
- Always clear stale fit result state on failure or cancellation.
- If fitting behavior changes, add tests for success, failure, zero-variance data, cancellation, and repeated start/stop cycles.

Plotting notes:

- `Plotting1d` owns chart references, range properties, and QML-callable data point methods.
- Analysis, experiment, sample, SLD, residuals, and multi-experiment views share refresh paths. A change in one chart path can affect others.
- Residuals should be computed from aligned linear-space measured/model values, not from log-display values returned for the main analysis chart.
- Multi-experiment plotting should use separate series per experiment rather than concatenating datasets into one line.

## Tests To Add With Changes

Use focused tests proportional to risk:

- Logic-only changes: add or update `tests/test_logic_*.py`.
- Backend adapter changes: add or update `tests/test_py_*.py`.
- Worker/fitting changes: add or update `tests/test_workers_fitter_worker.py` and `tests/test_logic_fitting.py`.
- QML bridge or visible UI changes: add tests like `tests/test_qml_fitting_progress_ui.py` where feasible, and manually run the app if the change is visual.
- Plotting changes: cover empty data, single experiment, multi-experiment, range fallbacks, and mode toggles such as `R(q) x q^4`.

The existing `tests/conftest.py` provides a `QCoreApplication` fixture for PySide tests.

## CI And Packaging

Installer workflow:

- `.github/workflows/installer.yml` builds on Ubuntu 22.04, Ubuntu 24.04, Windows 2022, and macOS 14.
- It uses Python 3.12 in CI and installs dependencies before freezing with PyInstaller and building a Qt Installer Framework package.
- `utils.py --update` injects additional release/CI metadata into `pyproject.toml` during the workflow.
- Windows signing uses DigiCert Software Trust Manager when secrets are available.
- Non-master branch pushes publish draft prereleases named by branch; master publishes using release metadata.

Documentation workflow:

- `.github/workflows/documentation-build.yml` builds Sphinx docs on version tags and pushes to `gh-pages`.
- Docs dependencies are in `pyproject.toml` under `docs`.

Installer pitfall:

- Linux QtIFW installer scripts must create `@HomeDir@/.local/share/applications` before copying `.desktop` files. Do not rely on workflow-side `mkdir -p` masking installer script bugs.

## Common Pitfalls

- Forgetting to update `BackendWrapper.qml` after adding a Python property or slot.
- Forgetting to update `Backends/Mock/*.qml`, which breaks mock/UI development mode.
- Adding PySide dependencies to logic modules, which makes unit testing harder.
- Reading or mutating shared project/model state from both the UI thread and fitting worker.
- Leaving cached analysis parameter lists stale after sample/model/experiment changes.
- Emitting only final fit signals when status bars or charts need interim state.
- Treating `src_qt5` as active code instead of migration reference.
- Assuming the installed `easyreflectometry` or `easyscience` package is the local workspace version.
- Making chart refresh depend on dynamic QML series before those series have been created and registered.

## Release And Branch Notes

The package version and release metadata live in `pyproject.toml`. Release docs also mention updating `README.md`, `INSTALLATION.md`, and `CHANGELOG.md` when bumping versions.

The repository default branch may be `master`, while contribution documentation refers to `develop` for active development. Check the active branch and target branch before opening PRs or comparing behavior.

## Recommended First Steps For A New Feature Or Bug Fix

1. Reproduce or locate the behavior in the relevant page under `Gui/Pages` and its `BackendWrapper` calls.
2. Trace the corresponding Python adapter under `Backends/Py`.
3. Move business logic into or update the matching module under `Backends/Py/logic`.
4. Wire any new signals/properties through `PyBackend`, `BackendWrapper.qml`, and the mock backend.
5. Add focused tests before or alongside the implementation.
6. Run the smallest relevant pytest target first, then the broader suite if the change touches shared behavior.
7. For visual/QML work, run the app and verify the affected workflow manually.
