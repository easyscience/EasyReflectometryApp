# EasyReflectometry

**EasyReflectometry** is a scientific software for modelling and analysis of reflectometry data. Currently, **EasyReflectometry** covers single contrast measurements of layered structures.

![EasyReflectometry Screenshot](./resources/images/er_analysis_dark.png) 

## What is EasyReflectometry for?

**EasyReflectometry** allows simulation of reflectometry profiles based on layered structures and the refinements of the structural parameters. For refinement, the program uses a number of fitting engines (minimizers).

**EasyReflectometry** offers a graphical user interface for the analysis of reflectometry data, built on _external_ reflectometry packages such as [refnx](https://refnx.readthedocs.io/en/latest/) and [refl1d](https://refl1d.readthedocs.io/en/latest/). 
This allows **EasyReflectometry** to cover different functionality aspects within a signle, intuitive, and user-friendly interface.  
The reflectomety packages are included with the installation so there is no need to download andn compile any additional components. 

## Example of usage

https://github.com/EasyScience/EasyReflectometryApp/wiki/Testing-in-Hand

## Main features

**EasyReflectometry** is open source and cross-platform, with support for Windows, macOS and Linux (Ubuntu).

The intuitive tabbed interface allows for a clear and defined data modelling and analysis workflow. 
There are also built-in step-by-step user guides and video tutorials for new users.

Current main features of **EasyReflectometry**:

- Support for the analysis of a single contrast of reflectometry data.
- Creation of materials to be used in structure from scattering length density.
- The ability to define repeating multi-layers of materials and refine these structures using [refnx](https://refnx.readthedocs.io/en/latest/) or [refl1d](https://refl1d.readthedocs.io/en/latest/). 
- Growing support for flexible _item_ types, including chemically consistent models.
- Ability to corefine multiple contrasts of reflectometry data.
- Multiple minimization engines: [lmfit](https://lmfit.github.io/lmfit-py), [bumps](https://github.com/bumps/bumps) and [DFO-LS](https://github.com/numericalalgorithmsgroup/dfols) (including the differential evolution method).
- Interactive HTML and standard PDF report generation.
- Undo/redo for both parameter changes and fitting.
- Saving and loading of projects.

Planned improvements / new functionality for **EasyReflectometry**:

- Support for magnetic structures and polarised reflectometry measurements.
- Support for mixed model reflectometry datasets.
- Reading of q-dependent resolution from a file.

Full details of the future plans for EasyReflectometry is available in the [roadmap](./ROADMAP.md).

## Getting Started

### Downloading

[Download](https://github.com/easyScience/EasyReflectometryApp/releases) the official **EasyReflectometry installer** for your operating system.

### Installing

Run **EasyReflectometry installer** and follow the instructions.

macOS: If you see the message _EasyReflectometrySetup.app can't be opened because it is from an unidentified developer_, do the following:
In the **Finder**, locate the **EasyReflectometry installer app**, then _control-click_ the app icon, then choose _Open_ from the shortcut menu and finally click _Open_.

### Uninstalling

Run **MaintenanceTool** from the **EasyReflectometry** installation directory, select _Remove all components_ and follow the instructions.

## Get in touch

<!---For general questions or comments, please contact us at [support@EasyReflectometry.org](mailto:support@EasyReflectometry.org).--->

For bug reports and feature requests, please use [Issue Tracker](https://github.com/easyScience/EasyReflectometryApp/issues) instead.
