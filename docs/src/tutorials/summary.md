# Summary

After a fit, the `Summary` tab puts the project information, the sample parameters, the
loaded experiments and the refinement result into one report. The report is shown in the
main window, and you can export it from the sidebar as a document or as figures.

## The report
The report in the main window has four sections:

- **Project information**: title, description and the number of loaded experiments.
- **Sample**: every parameter of the current model, as `Name`, `Value`, `Unit` and `Error`.
  The `Error` column shows the uncertainty from the fit. Parameters that were not fitted
  (fixed parameters, and all parameters before the first fit) have no uncertainty, so their
  `Error` cell is empty.
- **Experiments**: one row per measured dataset, with its q-range, number of points and
  resolution function. A polarized experiment has one row per measured spin channel, named
  after the channel (`pp`, `pm`, `mp`, `mm`).
- **Refinement**: calculation engine, minimizer, goodness of fit, and the number of total,
  free, fixed and constrained parameters.

Long experiment names are shortened in the table; hover over a name to see all of it.

## Export summary
The **Export summary** group in the sidebar saves the report to disk.

- **Name**: the file name, without extension.
- **Format**: `HTML` or `PDF`. The HTML export contains interactive plotly charts. The PDF
  export contains static images of the same charts, because the PDF converter cannot run
  the JavaScript that the interactive charts need.
- **Location**: the full output path. The default is the project home directory; use the
  folder icon to choose another one.
- **Save**: writes the file and shows the result in a dialog.

## Export plots
The **Export plots** group saves the reflectivity and SLD charts as a two-panel matplotlib
figure. Both panels are drawn from the current project: the measured data with error bars,
the calculated curve for each spin channel, and the SLD profile of every model.

- **Open in matplotlib**: opens the figure in an interactive matplotlib window without
  saving anything. Use it for a quick look, or to use matplotlib's own zoom, pan and
  save-image tools.
- **Name**: the figure file name, without extension.
- **Format**: `PDF`, `PNG`, `SVG` or `PICKLE` (see below).
- **Location**: the full output path, including the extension. Use the folder icon to
  choose another directory.
- **Width (cm)** / **Height (cm)**: the size of the saved figure. Images are saved at
  600 dpi.
- **Save plot**: writes the figure and shows the result in a dialog.

### Saving charts as matplotlib objects
`PDF`, `PNG` and `SVG` are rendered images, so the chart can no longer be edited. **PICKLE**
saves the matplotlib `Figure` object itself as a `.pickle` file, which you can open and
change in any Python session:

```python
import pickle
import matplotlib.pyplot as plt

with open('plots.pickle', 'rb') as handle:
    figure = pickle.load(handle)

plt.show()
```

The loaded figure is attached to `pyplot`, with its axes, artists, scales and data intact.
Choose this format when you want to keep working on the chart, for example to:

- restyle it for a paper or a talk (colors, fonts, legend, axis limits),
- add curves from another source to the same axes,
- read the plotted values back from the artists, e.g.
  `figure.axes[0].lines[0].get_xydata()`,
- export it to any image format later with `figure.savefig(...)`.

The file is written with the standard library `pickle` module, so you need matplotlib
installed to read it. As with any pickle file, only load files you trust.
