# Magnetic layers

A layer can be given a magnetisation, so that the two neutron spin states see different
scattering length densities. This page covers the **Model** page controls; loading and
fitting measured spin channels is described in
[polarised data](./polarized_data.md).

```{note}
Magnetic layers can only be calculated by `refl1d`. `refnx` has no magnetism, so the app
asks to switch the project's calculation engine the first time a layer is made magnetic.
```

## The Magnetism group

The **Magnetism** group is in the basic controls of the **Model** page, below the layer
editor. It is titled after the assembly currently selected in the `Layer editor`, for
example `Magnetism: Multi-layer`, and shows one row per layer of that assembly.

<!-- TODO: screenshot of the Magnetism group -> _images/sample_magnetism.png -->

| Column | Meaning |
|---|---|
| **No.** | Position of the layer in the assembly. |
| **Layer** | Layer name, as in the `Layer editor`. |
| **ρM/10⁻⁶Å⁻²** | Magnetic scattering length density of the layer. |
| **θM/°** | In-plane angle of the magnetic moment. |
| **Magn.** | Makes the layer magnetic. Unticking it removes the magnetisation. |

`ρM` and `θM` are only editable once **Magn.** is ticked.

```{note}
With the default in-plane guide field (270°), `θM = 270°` aligns the moment with the
field, which produces no spin-flip scattering. This is the value to start from for a
simple saturated film.
```

### ρM from a magnetic material

`ρM` can also come from the layer's material instead of being typed. **Add magnetic
material** in the **Materials** group creates a material with a formula, a mass density
and a **Moment** in Bohr magnetons per formula unit (bulk iron to start with: Fe,
7.874 g/cm³, 2.2 µB). The material editor shows the resulting `ρM` and the number density
`N`: `ρM = N × moment × 2.6991·10⁻⁵ Å`.

Give a layer that material, make it magnetic, select its row and tick **ρM from material**
below the table. The layer's `ρM` then follows the material's moment and density and is no
longer editable in the table; `θM` stays the layer's own, so two layers of one material can
point different ways. Unticking keeps the current value.

The moment is the effective in-plane net moment per formula unit, which is the moment per
atom only for a formula unit of one atom, such as Fe (`Fe2` is one element but two atoms).
In the `Analysis` table it is greyed out until some layer takes `ρM` from the material, and
when the last such layer stops doing so the moment is taken out of the fit. If the
material's SLD is set directly (unticked **SLD computed from formula and density**), its
density still sets `ρM` while a layer takes `ρM` from it; the data then constrain only
density × moment, so ticking one of the two for fitting unticks the other. Without such a
layer the density sets nothing and is greyed out too.

A layer whose `ρM` is given a constraint in the `Analysis` page no longer takes it from the
material: **ρM from material** is unticked, and the constraint is kept when the layer's
material changes.

### The guide field

Below the table, **Guide field angle** and **Applied field (T)** set the field of the
current model (refl1d's `Aguide` and `H`). They are shown while the current model has a
magnetic layer and the engine is `refl1d`:

| Guide field angle | Field direction |
|---|---|
| 270° or −90° (default) | in the sample plane |
| 90° | in the sample plane, reversed |
| 0° or 180° | along the surface normal |
| anything else | tilted out of the sample plane |

The applied field adds a Zeeman term along the field, so its effect depends on the field
and its direction relative to the moments. Both appear in the `Analysis` parameter table,
named after the model, and can be fitted; they are shown only while the model is magnetic
and the engine is `refl1d`, and are taken out of the fit otherwise. The ORSO model language
has no field, so model export warns when it is not the default.

### Magnetic samples from ORSO files

**Load sample** reads an ORSO model's `magnetic_moment`: a material with a formula, a
density and a moment becomes a magnetic material, and its layer is magnetic with
**ρM from material** ticked and `θM = 270°`, since the file has no direction. Whatever the
import could not carry over (a moment without a density, an unknown unit, an ignored
`relative_density`, magnetic layers in a repeated stack) is listed in a warning after the
sample loads. A magnetic sample cannot be loaded while the engine cannot model magnetism:
the load is refused with a message naming the engine to switch to, and the project is left
as it was.

### The moment angle slider

Selecting a magnetic row shows a slider below the table, spanning the whole `0-360°`
range of `θM`, with the guide field reference **H →** and the resulting arrow beside it -
the same arrow the [Structure tab](#moment-arrows-on-the-structure-tab) draws. Its
tooltip gives the angle both ways: `φ` from **H**, and the `θM` the table edits.

Dragging the slider sets `θM`, snapped to 5°; the text field remains the precise input.
The slider is read-only - and says so in its tooltip - while a fit is running, or when
`θM` follows a constraint, because then the parameter is not the user's to set.

The slider edits `θM` itself, exactly as the table column does. The arrow beside it shows
`φ`, the direction the moment physically points, so with a **negative `ρM`** the arrow
points opposite the angle on the slider - the moment is reversed while the parameter
stays where it was put.

### Switching the calculation engine

Ticking **Magn.** while the project uses an engine that cannot model magnetism opens the
**Switch calculation engine?** dialog. Accepting it makes the layer magnetic *and* switches
the project to `refl1d` in one step - the page does not change under you.

Switching recalculates the reflectivity and makes any existing fit result stale; the sample
and the loaded data are untouched. The engine can be switched back once no layer is
magnetic any more.

The engine itself lives in the **Calculation engine** group of the advanced controls on the
**Model** page (and in `Analysis` › `Advanced`, see
[simple fitting](./simple_fitting.md)). Selecting an engine that cannot model magnetism
while the sample still has magnetic layers is refused, with a message on both pages.

## Fitting ρM and θM

`ρM` and `θM` appear in the `Analysis` parameter table like any other layer parameter,
named after their assembly and model - for example `Model Fe rho_m`. They come with default
limits, a fit checkbox and can be used in constraints. The parameter name filter accepts
`magnetic` as a keyword to show only the magnetic parameters: `ρM`, `θM`, the material
moments and the field.

## Magnetic depth profiles

Once at least one layer is magnetic, the **Magnetic profile** group appears in the basic
controls, below **Magnetism**. The same switches are repeated in `Analysis` ›
`Advanced` › `Plot control`, and the two share one selection.

<!-- TODO: screenshot of the Magnetic profile group -> _images/sample_magnetic_profile.png -->

- **Show ρ ± ρM∥** - adds the nuclear SLD plus and minus the magnetic SLD along the
  field for each magnetic model to the SLD chart, dashed in the model's colour. These are
  the potentials of the two spin states only when every moment is parallel to the field
  and there is no applied field; a moment across the field mixes the spin states instead.
  For non-magnetic layers, and for moments across the field, the two curves collapse onto
  the nuclear SLD.
- **Show ρM** - the magnetic SLD profile on its own.
- **Show θM** - the in-plane moment angle, on its own right-hand axis. `θM` is only defined
  where there is a moment, so the curve is drawn in pieces rather than joined across the
  gaps.
- **Show R↑↑ and R↓↓** - splits each magnetic model's reflectivity into its two
  non-spin-flip cross-sections on the **Model** page reflectivity chart, dashed in the
  model's colour with their own legend rows. Off by default.

The y-range of the SLD chart covers every visible curve and grows when a curve is switched
on, so `ρ + ρM` is never clipped. If no model is magnetic, the chart, its legend and the
sidebar are unchanged.

```{note}
The `refl1d` calculator cannot repeat slabs that carry magnetism, so a magnetic model with
a repeating multilayer has no magnetic depth profile at all - and therefore none of these
curves. The **Magnetic profile** group reports the reason.
```

```{note}
For a magnetic sample the plain model curve is **not** an unpolarised average - the
calculator returns the ↑↑ cross-section - so `R↑↑` is drawn on top of it. The sidebar says
so as well.
```

The `Analysis` reflectivity chart is unaffected by this switch: it already draws one
calculated curve per measured spin channel when the experiment is polarised.

## Which way the moments point

`θM` is a number, and a stack of numbers does not show at a glance whether a model is
collinear, canted or twisted. The app therefore draws the moment as an arrow, in a single
convention shared by every view:

- the arrows are a **top view along the surface normal** - a compass laid over the sample;
- screen **right is the default guide field H** (in the sample plane at 270°), and the angle
  drawn is `φ`, measured from it counterclockwise: `φ = θM − 270°`. The arrows stay in this
  frame when the field is changed; the **H** reference follows the field instead, pointing
  left for a reversed in-plane field and replaced by its angle when the field is tilted out
  of the sample plane;
- a **negative `ρM`** is the same moment reversed, so the arrow points the opposite way
  and the tooltip carries the signed parameter;
- a magnetic layer whose `ρM` is below 1 % of the largest one in the model gets a **hollow
  dot** - "magnetic, but no moment": the direction of a zero-length vector means nothing.
  A layer with no magnetism at all gets nothing.

| `θM` | Arrow | Physics |
|---|---|---|
| 270° (default) | → along **H** | collinear, no spin flip |
| 90° | ← against **H** | collinear reversed, no spin flip |
| 0° / 180° | ↑ / ↓ | fully transverse, maximal spin flip |
| 40° | ↖ (`φ` = 130°) | canted |

Every arrow view shows the **H** reference on screen. Tooltips lead with `φ`, then the
`θM` and signed `ρM` the sidebar edits, then the part of the moment along the field and the
size of the part across it - what the non-spin-flip and the spin-flip channels mostly see.

Arrows are constant length everywhere: they encode direction only. The magnitude is the
`ρM` curve's job, and the exact value is in the tooltip.

(moment-arrows-on-the-structure-tab)=
### On the Structure tab

Each magnetic layer's box gets an arrow between its name and its thickness annotation.
This needs no switch: attaching magnetism *is* the request to see it. Boxes too short for
a readable glyph drop the arrow and keep it in the tooltip, and the box layout of a
non-magnetic sample is unchanged.

The Structure tab draws the **current model**; switch models in the header to inspect
another one. A repeating multilayer that the tab collapses to its repeat unit shows one
arrow per drawn box - the direction of the repeat unit, which every repeat shares.

Gradient layers get no arrow. A gradient has no single moment of its own, and one
"representative" arrow would be actively misleading when its slices oppose; the `ρM(z)`
and `θM(z)` curves remain the truth for graded structures.

