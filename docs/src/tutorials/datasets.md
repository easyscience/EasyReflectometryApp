# Demo datasets

The repository includes six simulated neutron reflectometry files for trying the
constraint and multiple-contrast features described in
[material and model setup](./model_def.md). They are in
[`examples/datasets`](https://github.com/easyScience/EasyReflectometryApp/tree/master/examples/datasets),
along with a
[full description](https://github.com/easyScience/EasyReflectometryApp/blob/master/examples/datasets/README.md)
of each demo and the script that regenerates the files.

All six are ORSO `.ort` files simulated from a known structure with 4 % noise and 5 %
`dQ/Q` resolution, so you can compare each fit against the true answer. The true values
are recorded in each file's header. The header also contains the sample structure in the
ORSO model language, so you can open the files in two ways:

- **Model** › `Load a sample` › **Load sample from file** builds the layer stack, with the
  true thicknesses, roughnesses and SLDs as starting values. Change these values before
  fitting, otherwise the fit has nothing to find.
- **Experiment** › **Load experiment(s) from file(s)** loads only the reflectivity curve,
  which you can fit with a sample you built yourself.

| Dataset | Demonstrates |
|---|---|
| `two_layer_film.ort` | A two-layer film with a known total thickness of exactly 90 Å, for the thickness budget and the derived total film thickness. |
| `swapped_layers.ort` | A layer-ordering inequality. Starting from the swapped guess, the fit finds the true structure only with a `≤` constraint between the two thicknesses. |
| `ni_ti_multilayer.ort` | A `[Ti / Ni] × 8` repeating multilayer whose Bragg peak fixes the period, for the **Constant period Λ** and **Conformal roughness** recipes. |
| `dppc_monolayer.ort` | A DPPC monolayer at the air/D2O interface, for the surfactant recipes (equal head and tail area per molecule, solvent roughness). |
| `film_contrasts.ort` | Three contrasts (D2O, H2O, CMSi) of a film on silicon in one file. Each dataset has its exact slab model, so **Load sample from file** builds the D2O model. Use it to try **Add contrast**, pairing experiments with models, per-contrast scale and background, and a joint fit. A variant shows **Link contrasts** for a contrast built as a separate model. Start here for multiple contrasts. |
| `dppc_contrasts.ort` | Three contrasts of one DPPC monolayer in one file (d-DPPC on D2O, d-DPPC on air-contrast-matched water, h-DPPC on D2O). Use it to try **Add contrast**, pairing experiments with models, and a joint fit that separates head hydration from head thickness, which no single contrast can do. |

```{note}
For `ni_ti_multilayer.ort` the loaded stack is flattened (8 × [Ti | Ni] becomes 16 layers
in one assembly). For the constant-period demo, rebuild it by hand as a
`Repeating Multi-layer`. For `dppc_monolayer.ort` the loaded stack is the slab equivalent
of the surfactant; for the surfactant recipes, replace it with a `Surfactant layer`
assembly. `dppc_contrasts.ort` has no sample model in its header, because the import
builds only plain slabs and cannot describe a solvated monolayer. Build the reference
contrast by hand and create the other two with **Add contrast**.
```
