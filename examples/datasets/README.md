# Demo datasets for the constraints functionality

Four simulated neutron reflectometry datasets (ORSO `.ort`, 4 % noise, 5 % dQ/Q
resolution) for demonstrating the constraint features in the application:
inequality constraints, the derived total film thickness, and the physics-constraint
recipes. Every file was simulated from a **known structure** — the ground truth is
recorded in each file's header (`sample.description`) and in the tables below — so
each demo has a right answer to compare against.

Regenerate with `python examples/datasets/generate_datasets.py` (reproducible seeds).

The files are **self-describing**: each header also carries the sample structure in
the ORSO model language, so you have two ways in —

- **Sample › Load a sample › Load sample from file** builds the layer stack for you
  (superphase / one "Loaded layer" assembly with the film layers / subphase), with
  the true thicknesses, roughnesses and SLDs as starting values. Change the starting
  values before fitting so there is something to find.
- **Experiment › Import experiment data** loads the reflectivity curve (works with a
  hand-built sample too).

For dataset 3 the loaded stack arrives flattened (8 × [Ti | Ni] becomes 16 layers in
one assembly); rebuild it as a `RepeatingMultilayer` by hand for the constant-period
recipe demo. For dataset 4 the loaded stack is the slab-equivalent of the surfactant;
replace it with a Surfactant Layer assembly for the recipe demo.

---

## 1. `two_layer_film.ort` — thickness budget + derived total thickness

| layer | material (SLD / 10⁻⁶ Å⁻²) | truth |
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

Verified through the app backend: starting from 30 / 50 under both constraints, the
BUMPS fit returns t_A = 35.0, t_B = 55.0 (sum 90.0).

## 2. `swapped_layers.ort` — layer-ordering inequality

| layer | material (SLD) | truth |
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

| layer | material (SLD) | truth |
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

| layer | truth |
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

---

## Cross-cutting things to show with any of the datasets

- **Persistence**: save the project after setting up constraints, reload — the
  inequality rows, recipe toggles and the derived parameter all come back.
- **Engine screening**: with any inequality active, selecting an LMFit/DFO
  minimizer shows the warning badge and the fit is refused with a clear message;
  `Bumps_lm` warns that enforcement is weak.
- **Infeasible progress**: force a start just inside the boundary and watch the
  progress line switch to "outside the inequality constraints" when the optimizer
  probes the forbidden region (the meaningless penalty χ² is not displayed).
- **Bayesian**: the DREAM sampler honours the same constraints — the posterior is
  cut off at the constraint boundary (visible in the marginal of t_A + t_B).
