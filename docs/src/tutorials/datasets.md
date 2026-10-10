# Demo datasets

The repository ships six simulated neutron reflectometry files for trying out the
constraint and multiple-contrast features described in [material and model setup](./model_def.md). They live in
[`examples/datasets`](https://github.com/easyScience/EasyReflectometryApp/tree/master/examples/datasets),
together with a
[full write-up](https://github.com/easyScience/EasyReflectometryApp/blob/master/examples/datasets/README.md)
of each demo and the script that regenerates them.

All six are ORSO `.ort` files simulated from a **known structure** with 4 % noise and 5 %
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
| `film_contrasts.ort` | Three contrasts (D2O, H2O, CMSi) of a film on silicon in one file. Each dataset carries its exact slab model, so **Load sample from file** builds the D2O model. It demonstrates **Add contrast**, pairing experiments with models, per-contrast scale and background, and a joint fit. Start here for multiple contrasts. |
| `dppc_contrasts.ort` | Three contrasts of one DPPC monolayer in one file (d-DPPC on D2O, d-DPPC on air-contrast-matched water, h-DPPC on D2O). It demonstrates **Add contrast**, pairing experiments with models, and a joint fit that separates head hydration from head thickness, which no single contrast can do. |

```{note}
For `ni_ti_multilayer.ort` the loaded stack arrives flattened (8 × [Ti | Ni] becomes 16
layers in one assembly); rebuild it as a `Repeating Multi-layer` by hand for the
constant-period demo. For `dppc_monolayer.ort` the loaded stack is the slab equivalent of
the surfactant; replace it with a `Surfactant layer` assembly for the surfactant recipes.
`dppc_contrasts.ort` has no sample model in its header (the import builds plain slabs
only, not a solvated monolayer): build the reference contrast by hand and derive the
other two with **Add contrast**.
```
