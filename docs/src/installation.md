# Installation

To make the installation of EasyReflectometry as easy as possible, we prepare packaged releases for three major operating systems:
- [Windows](https://github.com/EasyScience/EasyReflectometryApp/releases/download/v1.6.0/EasyReflectometryApp_v1.6.0_windows-2022.exe)
- [MacOS (Silicon)](https://github.com/EasyScience/EasyReflectometryApp/releases/download/v1.6.0/EasyReflectometryApp_v1.6.0_macos-14-AppleSilicon.zip)
- [Linux (built on Ubuntu-22.04)](https://github.com/EasyScience/EasyReflectometryApp/releases/download/v1.6.0/EasyReflectometryApp_v1.6.0_ubuntu-22.04)
- [Linux (built on Ubuntu-24.04)](https://github.com/EasyScience/EasyReflectometryApp/releases/download/v1.6.0/EasyReflectometryApp_v1.6.0_ubuntu-24.04)

## Upgrading from an earlier version

Installers newer than version 1.6.0 can install over an earlier version. When the chosen folder already holds one, the installer asks whether to remove it first:
- _Yes_ replaces the earlier version with the new one in the same folder.
- _No_ keeps the earlier version; the new one is installed into a separate folder named after its version, such as `EasyReflectometryApp-1.6.0`.

Close EasyReflectometry before upgrading: an earlier version that is still running cannot be removed.

Installers of version 1.6.0 and older stop with the message _"The directory you selected already exists and contains an installation"_. With those, remove the earlier version first: run **MaintenanceTool** from its installation folder, select _Remove all components_ and follow the instructions. Alternatively, choose a different installation folder.

If the relevant EasyReflectometry installation does not work on your system, then please try installation from source.

## Installation from source

1. Clone EasyReflectometryApp repo from GitHub
    > git clone https://github.com/easyScience/EasyReflectometryApp
2. Go to EasyReflectometryApp directory
3. Create miniforge conda environment with the name era_312 for EasyReflectometryApp
    > conda create --name era_312 python=3.12
4. Create environment for EasyReflectometryApp and install it and its dependences using pip
    > pip install -e .
5. Launch EasyReflectometry application in the created environment
    > python EasyReflectometryApp/main.py
