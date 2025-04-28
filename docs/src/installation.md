# Installation

To make the installation of EasyReflectometry as easy as possible, we prepare packaged releases for three major operating systems:
- [Windows](https://github.com/EasyScience/EasyReflectometryApp/releases/download/v1.0.0/EasyReflectometryApp_v1.0.0_windows-2022.exe)
- [MacOS (Intel)](https://github.com/EasyScience/EasyReflectometryApp/releases/download/v1.0.0/EasyReflectometryApp_v1.0.0_macos-13-Intel.zip)
- [MacOS (Silicon)](https://github.com/EasyScience/EasyReflectometryApp/releases/download/v1.0.0/EasyReflectometryApp_v1.0.0_macos-14-AppleSilicon.zip)
- [Linux (built on Ubuntu-24.04)](https://github.com/EasyScience/EasyReflectometryApp/releases/download/v1.0.0/EasyReflectometryApp_v1.0.0_ubuntu-22.04)
- [Linux (built on Ubuntu-22.04)](https://github.com/EasyScience/EasyReflectometryApp/releases/download/v1.0.0/EasyReflectometryApp_v1.0.0_ubuntu-24.04)

If the relevant EasyReflectometry installation does not work on your system, then please try installation from source.

## Installation from source

1. Clone EasyReflectometryApp repo from GitHub
    > git clone https://github.com/easyScience/EasyReflectometryApp
2. Clone EasyApp repo from GitHub
    > git clone https://github.com/easyScience/EasyApp
3. Go to EasyReflectometryApp directory
4. Create miniforge conda environment with the name era_311 for EasyReflectometryApp
    > conda create --name era_311 python=3.11
5. Create environment for EasyReflectometryApp and install it and its dependences using pip
    > pip install -e .
6. Launch EasyReflectometry application in the created environment
    > python EasyReflectometryApp/main.py
