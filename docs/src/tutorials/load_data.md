# Loading experimental data
## Load data
Experimental data must be **.dat**, **.txt**, or **.ort** to be loaded into the EasyReflectometryApp.  
Data is loaded in the `Experimental` page, by pressing the `Import experimental data`.

![Loading data](./_images/exp_load.png)

- **A**: Open your file manager to load data in the mentioned format.

## Instrumental parameters  
When data is loaded, it is possible to change instrumental parameters that affect the data.

![Setting experimental parameters](./_images/exp_data.png)

- **A**: Scale the data by the given value.
- **B**: Set the level where data merges into the experimental background.
- **C**: Instrumental resolution that percentage varies as a function of Q.

## Polarised data
A measurement that recorded several spin channels is loaded with the second button,
`Load polarized experiment (file per channel)`, which takes one file per channel and asks
how to assign them. See [polarised data](./polarized_data.md).
