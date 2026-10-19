# Summary

The `Summary` tab collects everything the project knows after a fit into a single report:
the project information, the sample parameters, the loaded experiments and the refinement
result. The report is shown in the main window, and the sidebar exports it - as a document,
or as figures.

## The report
The main window renders the report with four sections:

- **Project information**: title, description and the number of loaded experiments.
- **Sample**: every parameter of the current model, as `Name`, `Value`, `Unit` and `Error`.
  The `Error` column shows the uncertainty determined by the fit. Parameters that were not
  fitted (fixed parameters, and everything before the first fit) have no uncertainty, so
  their `Error` cell is left **empty**.
- **Experiments**: one row per measured dataset, with its q-range, number of points and
  resolution function. A polarized experiment contributes one row per measured spin
  channel, named after the channel (`pp`, `pm`, `mp`, `mm`).
- **Refinement**: calculation engine, minimizer, goodness of fit, and the number of total,
  free, fixed and constrained parameters.

Long experiment names are truncated in the table; hover over one to see the full name.

## Export summary
The **Export summary** group in the sidebar writes the report to disk.

- **Name**: the file name, without extension.
- **Format**: `HTML` or `PDF`. The HTML export embeds interactive plotly charts; the PDF
  export embeds static images of the same charts, because the PDF converter cannot run the
  JavaScript behind the interactive ones.
- **Location**: the full output path. Use the folder icon to pick a different directory. The default location is the project home directory.
- **Save**: writes the file and confirms the result in a dialog.

## Export plots
The **Export plots** group saves the reflectivity and SLD charts as a two-panel matplotlib
figure. Both panels are drawn from the current project: the measured data with its error
bars, the calculated curve for each spin channel, and the SLD profile of every model.

- **Open in matplotlib**: opens the figure in an interactive matplotlib window without
  writing anything to disk. Useful for a quick look, and for matplotlib's own zoom, pan and
  save-image tools.
- **Name**: the figure file name, without extension.
- **Format**: `PDF`, `PNG`, `SVG` or `PICKLE` (see below).
- **Location**: the full output path, extension included. Use the folder icon to pick a
  different directory.
- **Width (cm)** / **Height (cm)**: the size of the saved figure. Images are written at
  600 dpi.
- **Save plot**: writes the figure and confirms the result in a dialog.

### Saving charts as matplotlib objects
`PDF`, `PNG` and `SVG` are rendered images: what you see is all you get. Choosing **PICKLE**
instead writes the live matplotlib `Figure` object itself, as a `.pickle` file, so the chart
can be reopened and reworked in any Python session:

```python
import pickle
import matplotlib.pyplot as plt

with open('plots.pickle', 'rb') as handle:
    figure = pickle.load(handle)

plt.show()
```

The figure comes back attached to `pyplot`, with its axes, artists, scales and data intact.
That makes it the format to pick when the chart is a starting point rather than a final
result - for example to

- restyle it for a paper or a talk (colors, fonts, legend, axis limits),
- add curves from another source to the same axes,
- read the plotted values back out of the artists, e.g.
  `figure.axes[0].lines[0].get_xydata()`,
- and re-export it to any image format afterwards with `figure.savefig(...)`.

The file is written with the standard library `pickle` module, so reading it back requires
matplotlib to be installed - and, as with any pickle, only load files you trust.
