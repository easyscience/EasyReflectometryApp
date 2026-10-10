# Demo datasets for the constraints and multiple-contrast functionality

Six simulated neutron reflectometry files (ORSO `.ort`, 4 % noise, 5 % dQ/Q
resolution) for demonstrating the constraint features in the application:
inequality constraints, the derived total film thickness, and the physics-constraint
recipes; and fitting several contrasts of one sample jointly (datasets 5 and 6). Every file was simulated from a **known structure**: the actual values are
recorded in each file's header (`sample.description`) and in the tables below — so
each demo has correct answers to compare against.

Regenerate with `python examples/datasets/generate_datasets.py`.

The files are **self-describing**: each header also contains the sample structure in
the ORSO model language, so there are two ways to load them:

- **Sample › Load a sample › Load sample from file** builds the layer stack for you
  (superphase / one "Loaded layer" assembly with the film layers / subphase), with
  the correct thicknesses, roughnesses and SLDs as starting values. Change the starting
  values before fitting so there is something to find.
- **Experiment › Import experiment data** loads the reflectivity curve (works with a
  hand-built sample too).

For dataset 3 the loaded stack arrives flattened (8 × [Ti | Ni] becomes 16 layers in
one assembly); rebuild it as a `RepeatingMultilayer` by hand for the constant-period
recipe demo. For dataset 4 the loaded stack is the slab-equivalent of the surfactant;
replace it with a Surfactant Layer assembly for the recipe demo. Datasets 5 and 6
hold three datasets each; the sample is loaded from the first one's header (dataset 6
has none, see there).

---

## 1. `two_layer_film.ort` — thickness + derived total thickness

| layer | material (SLD / 10⁻⁶ Å⁻²) | value |
|---|---|---|
| superphase | air (0.0) | ∞ |
| Film A | MatA (3.0) | **35 Å**, roughness 3 Å |
| Film B | MatB (5.0) | **55 Å**, roughness 3 Å |
| subphase | Si (2.07) | ∞, roughness 2 Å |

The total film thickness is **exactly 90 Å** — think of it as known from
ellipsometry or a QCM measurement.

**Demo script**
1. Load the sample from the file (or build it by hand); set both thicknesses to a
   deliberately wrong 50 / 50 (fit only the two thicknesses, fix everything else;
   scale 1, background 1e-7).
2. *Sample › Advanced › Single constraints*: note the read-only **total_thickness**
   parameter (ƒ badge in the Analysis table) and the "Insert total film thickness"
   button in the expression editor.
3. Add two inequality constraints:
   - ordering: dependent `Film A thickness`, relation **≤**, expression
     `model_film_b_thickness`;
   - budget (`t_A + t_B ≤ 90` rearranged for the editor): dependent
     `Film A thickness`, relation **≤**, expression `90 - model_film_b_thickness`
     (the literal `90` is read in Å, the unit of the dependent parameter).
4. The feasibility warning appears while 50 + 50 > 90 — the fit refuses to start.
   Set the thicknesses to 30 / 50 to make the start point feasible.
5. Select a **Bumps** minimizer (with LMFit the warning badge shows and the fit is
   refused) and fit: the result lands on the 90 Å boundary at the true 35 / 55 split.

Verified: starting from 30 / 50 under both constraints, the
BUMPS fit returns t_A = 35.0, t_B = 55.0 (sum 90.0).

## 2. `swapped_layers.ort` — layer-ordering inequality

| layer | material (SLD) | value |
|---|---|---|
| superphase | air (0.0) | ∞ |
| Top | TopMat (2.5) | **20 Å**, roughness 3 Å |
| Bottom | BottomMat (4.2) | **60 Å**, roughness 3 Å |
| subphase | Si (2.07) | ∞, roughness 2 Å |

**Demo script**: start the fit from the *swapped* guess (60 / 20). Without
constraints the optimizer can wander into an unphysical local minimum; with
`Top thickness ≤ Bottom thickness` the feasibility check first makes you swap the
start values back, and the fit then converges to 20 / 60. Good for showing that
inequalities encode prior knowledge ("the capping layer is thin").

## 3. `ni_ti_multilayer.ort` — physics recipes on a repeating multilayer

| layer | material (SLD) | value |
|---|---|---|
| superphase | air (0.0) | ∞ |
| [Ti / Ni] × 8 | Ti (−1.95), Ni (9.41) | Ti **30 Å**, Ni **70 Å**, period **Λ = 100 Å**, conformal roughness 4 Å |
| subphase | Si (2.07) | ∞, roughness 4 Å |

The first-order Bragg peak at q ≈ 2π/Λ ≈ 0.063 Å⁻¹ pins the period.

**Demo script**: build a `RepeatingMultilayer` (2 layers, 8 repetitions). In
*Sample › Advanced › Physics constraints* toggle **Constant period Λ** (the Ni
thickness becomes dependent and absorbs whatever Ti changes by — one grouped row in
the constraints table) and **Conformal roughness**. Fit only the Ti thickness and
the roughness: the period stays at its set 100 Å while the Ti/Ni split refines to
30 / 70. Also a good dataset for showing `total_thickness` (800 Å of film).

## 4. `dppc_monolayer.ort` — surfactant recipes

| layer | value |
|---|---|
| superphase | air, ∞ |
| DPPC tails (C₃₂D₆₄) | default surfactant-layer geometry |
| DPPC heads (C₁₀H₁₈NO₈P) | — |
| subphase | D2O (6.36), roughness 3 Å |

Simulated from the default `SurfactantLayer` (DPPC) with **area per molecule
48 Å² shared by head and tail**, conformal roughness 3 Å extended to the D2O
subphase.

**Demo script**: build a Surfactant Layer assembly between air and D2O. In
*Physics constraints* toggle **Equal head/tail area per molecule**, **Conformal
roughness**, then **Solvent roughness follows the surfactant** (note it is
unavailable until conformal roughness is on). Fit the tail APM and roughness:
they refine to 48 Å² / 3 Å, and the constraints table shows three grouped recipe
rows instead of many individual ties. The "Mixture fractions sum to 1" card shows
as always-on because the solvated head material normalises internally.

## 5. `film_contrasts.ort` — multiple contrasts

One file, **three datasets**: a dense (non-swelling) film on silicon, measured
under three waters. Only the water changes, so the structure is plain slabs. Each
dataset's header carries its own exact stack. **Load sample from file** builds the
first one, the D2O stack.

| layer | material (SLD / 10⁻⁶ Å⁻²) | value |
|---|---|---|
| superphase (beam side) | Si (2.07) | ∞ |
| oxide | SiO2 (3.47) | **15 Å**, roughness 3 Å |
| film | Film (**2.0**) | **80 Å**, roughness **5 Å** |
| subphase | water | ∞, roughness 4 Å |

| dataset (`data_set`) | water (SLD) | scale | background |
|---|---|---|---|
| `1_D2O` (reference) | D2O (6.36) | 1.00 | 2e-7 |
| `2_H2O` | H2O (−0.56) | 0.95 | 5e-6 |
| `3_CMSi` | CMSi, water contrast-matched to Si (2.07) | 1.00 | 1e-6 |

**Demo script**
1. *Sample* › **Load sample from file** with `film_contrasts.ort`. This builds
   Si | SiO2 | Film | D2O; the palette is Si, SiO2, Film, D2O. Add two
   materials: `H2O` (−0.56) and `CMSi` (2.07).
2. **Add contrast of the selected model…** twice: replace D2O with H2O, then
   with CMSi. The new models share the D2O model's oxide and film. Editing the
   film thickness in one model changes all three. Only the subphase is the
   contrast's own.
3. *Experiment* › **Load experiment(s) from file(s)** with the same file. This
   creates three experiments ("Film on silicon in D2O / H2O / CMSi"), all bound
   to the current model. Pair the H2O and CMSi experiments with their contrasts.
4. *Analysis*: set each model's background to its value in the table above and
   keep it fixed. Free the oxide thickness, the film thickness, SLD and
   roughness, and the three scales. Start from a wrong guess, e.g. oxide 25 Å,
   film 70 Å, SLD 1.0, roughness 3 Å. Fit all three: oxide 15.2 Å, film 80.0 Å,
   SLD 2.00, roughness 5.0 Å. The scales come back per contrast (H2O 0.95), and
   each contrast's reduced χ² is about 0.9. The same result came from
   oxide 10 / film 90 / SLD 3.0 and from 20 / 75 / 1.5.
   - **Leave the backgrounds fixed.** With all three backgrounds free from a
     common 1e-6, LMFit ends in a local minimum: the D2O background drops to
     about 1e-11, its scale to 0.86, and reduced χ² goes up to 5–36.
   - **Untick Fit** on two experiments to fit one contrast alone. D2O alone or
     H2O alone also land near the original value. CMSi alone is weaker (scale 0.81,
     roughness 3.7 Å), because the substrate is invisible in that contrast.
5. Save and reload the project. The contrasts still share the structure, and
   each experiment keeps its model pairing.


## 6. `dppc_contrasts.ort` — multiple contrasts of a monolayer (advanced)

One file, **three datasets**: the same DPPC monolayer measured in three contrasts.
The structure is the same in all three; only the deuteration of the tails and the
water differ. Each contrast has its own scale and background.

| dataset (`data_set`) | tails | subphase and head solvent | scale | background |
|---|---|---|---|---|
| `1_dDPPC_D2O` (reference) | C₃₂D₆₄ | D2O (6.36) | 1.00 | 3e-7 |
| `2_dDPPC_ACMW` | C₃₂D₆₄ | ACMW, air-contrast-matched water (0.0) | 1.00 | 1e-6 |
| `3_hDPPC_D2O` | C₃₂H₆₄ | D2O (6.36) | 0.95 | 6e-7 |

Shared structure: area per molecule **52 Å²** (head and tail), tail
**15.0 Å**, head **9.5 Å** with head solvent fraction **0.30**, conformal roughness
**3.5 Å**, which the subphase follows. The water is one material used twice, as
the subphase and as the head-group solvent, so changing the contrast changes both.

The header has no sample model. The ORSO import builds plain slabs only, so it
cannot describe a solvated monolayer. Build the sample by hand. This demo also
exercises the formula substitution and a solvent shared by two layers.

**Demo script**
1. *Sample*: build air | Surfactant Layer | D2O. Use the **same** D2O material for
   the subphase and the head-group solvent. Turn on the **Equal head/tail area per
   molecule**, **Conformal roughness** and **Solvent roughness follows the
   surfactant** recipes. Start from a wrong guess, e.g. tail 20 Å, head 12 Å, APM
   45 Å², solvent fraction 0.1. Add an `ACMW` material with SLD 0.
2. **Add contrast of the selected model…** twice:
   - `d-DPPC / ACMW`: replace D2O with ACMW. This one change swaps both the
     subphase and the head solvent.
   - `h-DPPC / D2O`: give the tail layer the formula `C32H64`.

   The contrasts share the reference's structure. Editing the tail thickness in
   any model changes all three.
3. *Experiment* › **Load experiment(s) from file(s)** with `dppc_contrasts.ort`.
   This creates three experiments, named after the dataset titles and all bound to
   the current model. Pair each one with its contrast in the experiments list.
4. *Analysis*: free the tail and head thicknesses, the APM, the head solvent
   fraction, the roughness, and each model's scale and background. Fit.
   - **D2O contrast alone** (untick **Fit** on the other two): the head solvation
     runs to its bound of 0, the head thickness drops to about 8.4 Å, and no
     uncertainties come out. A single contrast cannot tell head hydration from
     head thickness.
   - **All three jointly**: tail 14.1 Å, head 9.25 Å, APM 51.7 Å², solvent
     fraction 0.21, roughness 3.9 Å, with finite uncertainties. Scales and
     backgrounds come back per contrast (h-DPPC scale 0.94). Each contrast's
     reduced χ² is about 1. Verified through the library API, starting from
     the wrong guess above.
5. Save and reload the project. The contrasts still share their structure, and
   each experiment keeps its model pairing.

---

## Other things to show with any of the datasets

- **Persistence**: save the project after setting up constraints, reload — the
  inequality rows, recipe toggles and the derived parameter all come back.
- **Engine screening**: with any inequality active, selecting an LMFit/DFO
  minimizer shows the warning message and the fit is refused with a clear message;
  `Bumps_lm` warns that enforcement is weak.
- **Infeasible progress**: force a start just inside the boundary and watch the
  progress line switch to "outside the inequality constraints" when the optimizer
  probes the forbidden region (the meaningless penalty χ² is not displayed).
- **Bayesian**: the DREAM sampler honours the same constraints — the posterior is
  cut off at the constraint boundary (visible in the marginal of t_A + t_B).
