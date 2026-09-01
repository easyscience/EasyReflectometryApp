# Demo datasets

The repository ships four simulated neutron reflectometry datasets for trying out the
constraint features described in [material and model setup](./model_def.md). They live in
[`examples/datasets`](https://github.com/easyScience/EasyReflectometryApp/tree/master/examples/datasets),
together with a
[full write-up](https://github.com/easyScience/EasyReflectometryApp/blob/master/examples/datasets/README.md)
of each demo and the script that regenerates them.

All four are ORSO `.ort` files simulated from a **known structure** with 4 % noise and 5 %
`dQ/Q` resolution, so every demo has a right answer to compare the fit against. The ground
truth is recorded in each file's header, and each header also carries the sample structure
in the ORSO model language, so the files can be opened in two ways:

- **Model** › `Load a sample` › **Load sample from file** builds the layer stack for you,
  with the true thicknesses, roughnesses and SLDs as starting values. Change those starting
  values before fitting, so there is something to find.
- **Experiment** › **Load experiment(s) from file(s)** loads the reflectivity curve, which
  also works with a hand-built sample.

| Dataset | Demonstrates |
|---|---|
| `two_layer_film.ort` | A two-layer film whose total thickness is known (exactly 90 Å) - the thickness budget and the derived total film thickness. |
| `swapped_layers.ort` | A layer-ordering inequality: started from the swapped guess, the fit only recovers the truth with a `≤` constraint between the two thicknesses. |
| `ni_ti_multilayer.ort` | A `[Ti / Ni] × 8` repeating multilayer with a Bragg peak that pins the period - the **Constant period Λ** and **Conformal roughness** recipes. |
| `dppc_monolayer.ort` | A DPPC monolayer at the air/D2O interface - the surfactant recipes (equal head/tail area per molecule, solvent roughness). |

```{note}
For `ni_ti_multilayer.ort` the loaded stack arrives flattened (8 × [Ti | Ni] becomes 16
layers in one assembly); rebuild it as a `Repeating Multi-layer` by hand for the
constant-period demo. For `dppc_monolayer.ort` the loaded stack is the slab equivalent of
the surfactant; replace it with a `Surfactant layer` assembly for the surfactant recipes.
```
