# EasyReflectometry

**EasyReflectometry** is scientific software for modelling and analysing reflectometry data from layered structures. It handles single and multiple contrasts, unpolarised and polarised measurements, and both classical fitting and Bayesian sampling.

![EasyReflectometry Screenshot](./resources/images/er_analysis_dark.png)

## What is EasyReflectometry for?

**EasyReflectometry** simulates reflectometry profiles of layered structures and refines their structural parameters against measured data. Refinement uses one of several fitting engines (minimizers), or Bayesian sampling when the uncertainty of each parameter is wanted.

**EasyReflectometry** offers a graphical user interface built on established reflectometry packages, [refnx](https://refnx.readthedocs.io/en/latest/) and [refl1d](https://refl1d.readthedocs.io/en/latest/), through the [easyreflectometry](https://github.com/easyscience/reflectometry-lib) library.
This brings their functionality together in a single, intuitive interface.
The calculation engines are included in the installer, so nothing else has to be downloaded or compiled.

## Main features

**EasyReflectometry** is open source and cross-platform, with support for Windows, macOS (Apple Silicon) and Linux (Ubuntu).

The tabbed interface guides a clear modelling and analysis workflow: Project, Sample, Experiment, Analysis and Summary.

- **Sample models**: materials defined by their scattering length density (SLD), layers, repeating multilayers, and _items_ such as surfactant layers with chemically consistent constraints.
- **Data import**: text files and [ORSO](https://www.reflectometry.org/) `.ort` files. A file with a q-resolution column keeps the resolution of every point, and several files of one contrast (other angles or wavelength bands) can be merged into one experiment.
- **Multiple contrasts**: contrasts share one structure, and all of them are refined together.
- **Magnetism and polarisation**: a magnetic SLD and in-plane moment angle per layer, refined with refl1d. Polarised data is imported as one file per spin channel, with spin-asymmetry views and simultaneous refinement of all channels against a single model.
- **Fitting**: [lmfit](https://lmfit.github.io/lmfit-py), [bumps](https://github.com/bumps/bumps) and [DFO-LS](https://github.com/numericalalgorithmsgroup/dfols) minimizers, with adjustable fit settings, parameter constraints and links between contrasts.
- **Bayesian analysis**: Markov chain Monte Carlo (MCMC) sampling with bumps DREAM, with posterior bands on the reflectivity and SLD charts and per-parameter distributions.
- **Reports**: interactive HTML and PDF reports of the model, data and fit results.
- **Projects**: saving and loading of complete projects.

Planned improvements are listed in the [roadmap](./ROADMAP.md) and the [issue tracker](https://github.com/easyScience/EasyReflectometryApp/issues).

## Documentation

The [user documentation](https://easyscience.github.io/EasyReflectometryApp/) has step-by-step tutorials on loading data, defining models, fitting, polarised data, magnetism and Bayesian analysis.

## Getting started

### Downloading

[Download](https://github.com/easyScience/EasyReflectometryApp/releases/latest) the **EasyReflectometry installer** for your operating system. See [INSTALLATION.md](./INSTALLATION.md) for details and for installation from source.

### Installing

Unzip the downloaded archive, run the **EasyReflectometry installer** and follow the instructions.

macOS: the installer is not notarised by Apple, so macOS may refuse to open it as coming from an unidentified developer. Try to open it once, then open **System Settings** → **Privacy & Security**, scroll to the message about the installer and click **Open Anyway**. On macOS 14 and older, _control-click_ the installer in the **Finder**, choose _Open_ and confirm with _Open_.

### Uninstalling

Run **MaintenanceTool** from the **EasyReflectometry** installation directory, select _Remove all components_ and follow the instructions.

## Get in touch

For bug reports and feature requests, please use the [issue tracker](https://github.com/easyScience/EasyReflectometryApp/issues).

Contributions are welcome; see [CONTRIBUTING.md](./CONTRIBUTING.md).
