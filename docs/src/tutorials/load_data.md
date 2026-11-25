# Loading experimental data
## Load data
EasyReflectometryApp loads experimental data from .dat, .txt and .ort files.
To load a file, go to the `Experimental` page and press `Import experimental data`.

![Loading data](./_images/exp_load.png)

- **A**: Opens a file dialog for choosing a data file.

The loaded data is drawn in the main window. To read the coordinates of a measured point,
move the cursor near it. The tooltip snaps to the nearest visible point, so you do not have
to hit the marker exactly. The Plot control group in the advanced controls switches the
R(q) axis between logarithmic and linear, see [simple fitting](./simple_fitting.md).

## Instrumental parameters
Once data is loaded, you can change the instrumental parameters that apply to it.

![Setting experimental parameters](./_images/exp_data.png)

- **A**: Scale factor applied to the data.
- **B**: Level at which the data meets the experimental background.
- **C**: Instrumental resolution, as a percentage of Q.

## Resolution of the data
If a file has a fourth column (`sQz`, the q-resolution of each point), the app keeps that
resolution. The fit, the calculated curve and residuals on the `Analysis` page, the Bayesian
sampling and its band, and the report all smear each dataset with its measured resolution.
This applies to every dataset, including several datasets sharing one model (other angles
or contrasts) and each channel of a polarised experiment.

The resolution field (**C**) belongs to the model. Its value comes from the first dataset
loaded onto the model, and it shows `Spline` when that dataset has a measured resolution.
The `Sample` page uses it for simulations, and datasets without a resolution column are
smeared with the model's percentage.

## Several files of one contrast
A contrast is often measured as several curves, one per incident angle or wavelength band.
Load the first file, keep its experiment selected, and press
`Add file(s) to the selected experiment` to merge the other files into it. The points are
sorted by q and each keeps its own resolution, so overlapping q ranges measured with
different widths fit correctly. If you add a file without a resolution column to measured
data, its points get the model's percentage resolution (5 % when the model holds a measured
resolution), and the app tells you. The button is disabled for polarised experiments,
because their channels are separate datasets.

## Polarised data
To load a measurement with several spin channels, use the second button,
`Load polarized experiment (file per channel)`. It takes one file per channel and asks how
to assign them. See [polarised data](./polarized_data.md).
