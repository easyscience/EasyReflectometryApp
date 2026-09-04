# Material and model setup
When a project is initialised it is then possible to define material and set the model.  

Let us first look at the general layout of the `Model` page, which is split up into two parts, the main window showing the graphs and the sidebar being the control panel for variables and data.

![Model overview](./_images/sample_overview.png)

- **A**: Graph change between the Reflectivity- and Scattering Length Density (SLD) curve.
- **B**: Graph control of ledger, visible coordinates on hower, zoom and pan control, and reset.
- **C**: Basic controls, for defining material and model, and advanced controls for further setting parameters.

## Basic controls
### Material editor
To construct a model in the app, first, you add the materials that will compose the layers in `Material Editor`.  
The materials are added by the real and imaginary components of the scattering length density (in units of 10<sup>-6</sup>Å<sup>-2</sup>) and given a name for the material.  

![Material editor](./_images/sample_material.png)

- **A**: For adding more material.
- **B**: Duplicating the last clicked material.
- **C**: Changes the ordering of materials.

### Density materials
A material can also be defined by its **chemical formula and mass density** instead of a
numeric SLD. Such *density materials* enter a project when a sample is loaded from an ORSO
model that defines a material this way (`Load a sample`), and they are marked with a **ρ**
badge next to their row number in the Material editor table.

Selecting a ρ row reveals a detail panel below the table with the material's chemical
formula, its mass density (in g/cm³) and the checkbox **SLD computed from formula and
density**:

<!-- TODO: screenshot of the density material panel -> _images/sample_material_density.png -->

- **Checked** (the default): the SLD is physics, not an input - it is computed as
  `SLD = Nᴀ · ρ · b / M` from the density ρ, the formula's coherent neutron scattering
  length *b* and molecular weight *M*. The SLD/iSLD cells in the table are therefore
  read-only, and on the `Analysis` page the material's `sld`/`isld` parameters are shown
  greyed as dependent while **`density` is the parameter to fit**. Editing the formula
  updates the scattering length and molecular weight (an invalid formula is rejected and
  the field snaps back).
- **Unchecked**: `sld`/`isld` become ordinary independent parameters - editable here and
  fittable on the `Analysis` page exactly like a plain material's (they arrive fixed, so
  tick their `Fit` box). The `density`, `molecular_weight` and scattering-length rows are
  greyed with the note `unused (SLD is fitted directly)`, because they no longer affect
  the reflectivity - they cannot be fitted or edited until the box is checked again.

```{warning}
Re-checking the box restores the coupling by **recalculating** SLD/iSLD from the current
formula and density - manually entered or fitted SLD values are discarded.
```

The choice is per material and is saved with the project; projects saved before this
feature load with the coupling enabled. Note that toggling the coupling is not undoable.
If you add a constraint on `sld`/`isld` while unchecked and then re-check the box, that
constraint is silently discarded - re-checking always recomputes SLD/iSLD from the
formula and density. The `Active Constraints` table refreshes after a toggle, but it does
not flag rows that the toggle invalidated, so review it yourself after switching modes.

### Model creation and editing
For creating new models, the `Models selector` tab is used, and then for setting the assemblies in the model the `Model editor` is used.  

![Model creation](./_images/sample_model.png)

- **A**: Renaming model.
- **B**: Removing the specific model.
- **C**: Adding more models.
- **1**: Renaming/naming the assembly.
- **2**: Setting the type of assembly; Multilayer, Repeating Multilayer or Surfactant layer.
- **3**: Removing the specific assembly.
- **4**: Adding more asseblies.

### Layer editor
Then for editing the assemblies in the model, the `Layer editor` is used.  
By clicking an assembly, the `Layer editor` is specified and changes can be made to that assembly.

![Layer editor](./_images/sample_layer.png)

- **A**: Pick the desired assembly to modify.
- **1**: Choose a material from materials in the `Material Editor`.
- **2**+**3**: Setting the Thickness and Upper Roughness of the material in Angstrom, Å.

### Magnetism
A layer can also be given a magnetisation, in the `Magnetism` group below the layer editor.
This needs the `refl1d` calculation engine and is described in
[magnetic layers](./magnetism.md).

## Structure view
The main window has a **Structure** tab next to **Reflectivity** showing a schematic of
the current model's layer stack: one colored box per layer, ambient medium on top, substrate
at the bottom. Boxes share a color per material (see the legend), box heights follow layer
thickness, and repeated multilayers with many repetitions are drawn once with a "× N" badge.

<!-- TODO: screenshot of the Structure tab -> _images/sample_structure.png -->

Hover a box for its material, SLD, thickness and roughness; click it to select that layer in
the sidebar editor. The view updates immediately when the model changes, including after a fit.

Note the view is a schematic, not a to-scale cross-section: heights are clamped so very thin
layers stay visible and very thick ones do not crowd out the rest.

## Advanced controls
In the advanced controls, it is possible to apply a specific Q-range of interest, to choose
the calculation engine, and to constrain the parameters of the model.

![Advanced controls](./_images/sample_adv.png)

- **A**: Setting min. Q value of interest.
- **B**: Setting max. Q value of interest.
- **C**: Setting Q-resolution.

The **Calculation engine** group selects between `refnx` and `refl1d` for this project. The
same selector is available on the `Analysis` page. Only `refl1d` can model magnetic layers,
so selecting `refnx` while the sample has magnetic layers is refused - see
[magnetic layers](./magnetism.md).

Below these sit three constraint groups, from the most specific to the most general.

### Physics constraints
The `Physics constraints` group applies physically motivated constraints to an assembly with
one click. The list is per assembly of the current model, and only shows the recipes that
make sense for that assembly type; a recipe that cannot be applied right now is marked
`n/a` with the reason, and one that is always in force is marked `always on`.

<!-- TODO: screenshot of the Physics constraints group -> _images/sample_physics_constraints.png -->

| Recipe | Effect |
|---|---|
| **Conformal roughness** | Every interface of the assembly shares the roughness of its first layer. |
| **Conformal thickness** | Every layer of the assembly shares the thickness of its first layer. |
| **Constant period Λ** | The summed thickness of the layers stays constant: the last layer absorbs whatever the others change by. |
| **Equal head/tail area per molecule** | The head layer takes the area per molecule of the tail layer (surfactant layers). |
| **Symmetric head groups** | The back head layer follows the front head layer thickness and area per molecule (bilayers). |
| **Solvent roughness follows the surfactant** | The roughness of the first layer below the surfactant follows the tail roughness. Needs **Conformal roughness**. |
| **Mixture fractions sum to 1** | Material mixtures and solvated materials keep their fractions normalised. Always on, not toggleable. |

Each active recipe appears as a single row in the `Active Constraints` table of the
`Single constraints` group, of type `physics`, counting the parameters it ties together.

### Single constraints
The `Single constraints` group creates numeric or symbolic relationships between individual
parameters.

<!-- TODO: screenshot of the Single constraints group -> _images/sample_constraints.png -->

1. Pick the **dependent parameter** from the drop-down.
2. Pick the relation: `=`, `≤` or `≥`.
3. Type the **expression**, for example `np.sqrt(1 / sld_ni) + 4`. Use
   **Insert parameter alias…** to paste the alias of another parameter rather than typing
   it, and **Insert total film thickness** to use the read-only sum of all layer thicknesses
   between superphase and subphase.
4. Check the **Preview** line, which shows how the constraint will read - and, for an
   inequality, that numeric literals are interpreted in the dependent parameter's unit.
5. Press **Add constraint**.

`=` ties the parameter to the expression, so it is no longer free. `≤` and `≥` against other
parameters become **inequality constraints**, which are enforced as penalties during
fitting.

```{warning}
Inequality constraints need a BUMPS minimizer (`Analysis` › `Minimization method`). With
`lmfit` or `DFO-LS` selected the group shows a warning and fits are refused until the
minimizer is changed or the inequality is removed. A warning also appears when the current
parameter values violate an inequality, and again fits will not start until they hold.
```

Existing constraints are listed in the `Active Constraints` table, with columns `No.`,
`Type`, `Parameter` and `Expression`. The `Type` column tells the kinds apart - `expr` for a
plain equality, `≤ ≥` for an inequality, `physics` for a recipe from the group above,
`bound` for an upper bound and `value` for a fixed value - and each row can be removed
individually.

### Model constraints
The `Model constraints` group ties whole models together rather than single parameters:
select two or more models and press **Constrain models parameters** to constrain all of
their matching parameters at once. This is the tool for co-refining several contrasts that
share a structure. The resulting constraints are listed in the `Model Constraints` table
below the selector and can be removed there.

<!-- TODO: screenshot of the Model constraints group -> _images/sample_model_constraints.png -->

### Trying the constraints out
Four simulated datasets with a known ground truth are provided for exercising these
features - see [demo datasets](./datasets.md).
