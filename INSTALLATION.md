# Installation

## Installers

To make installing EasyReflectometry as easy as possible, packaged releases are built for three operating systems.
Download them from the [latest release](https://github.com/EasyScience/EasyReflectometryApp/releases/latest):

| Operating system | Release asset (zip file whose name contains) |
| --- | --- |
| Windows | `windows-2022` |
| macOS (Apple Silicon) | `macos-14-AppleSilicon` |
| Linux, built on Ubuntu 22.04 | `ubuntu-22.04` |
| Linux, built on Ubuntu 24.04 | `ubuntu-24.04` |

Unzip the archive and run the installer inside it. On Linux, make the installer executable first (`chmod +x <installer>`).
On macOS, see the note on unidentified developers in the [README](./README.md#installing).

If no installer works on your system, install from source as described below.

## Installation from source

EasyReflectometry needs Python 3.12 or newer (3.12 and 3.13 are tested).

1. Clone the **EasyReflectometryApp** repository from GitHub and go to its directory:
   ```
   git clone https://github.com/easyScience/EasyReflectometryApp
   cd EasyReflectometryApp
   ```
2. Create and activate a Python environment, for example with [Miniforge](https://github.com/conda-forge/miniforge):
   ```
   conda create --name era python=3.12
   conda activate era
   ```
3. Install **EasyReflectometryApp** and its dependencies with **pip**:
   ```
   pip install -e .
   ```
   The clone checks out the `master` branch, the latest release, which installs the released [easyreflectometry](https://github.com/easyscience/reflectometry-lib) library from PyPI.
4. Launch **EasyReflectometry**:
   ```
   python EasyReflectometryApp/main.py
   ```

On Linux, Qt needs some system libraries that minimal installations may lack. On Ubuntu:

```
sudo apt-get install libegl1 libgl1 libfontconfig1 libdbus-1-3 libxkbcommon0 libxkbcommon-x11-0 \
  libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
  libxcb-shape0 libxcb-xfixes0 libxcb-xinerama0
```

See [Qt's Linux requirements](https://doc.qt.io/qt-6/linux-requirements.html) for other distributions.

## Development installation

Development happens on the `develop` branch, which installs the [easyreflectometry](https://github.com/easyscience/reflectometry-lib) library from its `develop` branch on GitHub, so **git** must be available.
In the cloned repository, switch to `develop` and install the app with the test dependencies and the linter, then run the test suite:

```
git switch develop
pip install -e ".[test]" ruff
python -m pytest tests
```

When a change also touches the [easyreflectometry](https://github.com/easyscience/reflectometry-lib) library or the [easyscience](https://github.com/easyscience/core) core, install local checkouts of them in editable mode, after installing the app:

```
pip install -e ../reflectometry-lib
pip install -e ../core
```

The app then runs and is tested against those checkouts instead of the versions pinned in `pyproject.toml`. See [CONTRIBUTING.md](./CONTRIBUTING.md) for the development workflow.
