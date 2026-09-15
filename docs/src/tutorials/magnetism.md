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
`θM = 270°` aligns the moment with the guide field, which produces no spin-flip
scattering. This is the value to start from for a simple saturated film.
```

### The moment compass

Selecting a magnetic row shows a compass below the table: the same arrow the
[Structure tab](#moment-arrows-on-the-structure-tab) draws, with the guide field **H**
fixed pointing right and the `θM` values of the four cardinal directions on the rim, so
the convention is visible instead of remembered. Its tooltip gives the angle both ways -
`φ` from **H**, and the `θM` the table edits.

Dragging inside the circle sets `θM`, snapped to 5°; the text field remains the precise
input. The compass is read-only - and says so in its tooltip - while a fit is running, or
when `θM` follows a constraint, because then the parameter is not the user's to set.

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
`magnetic` as a keyword to show only the magnetic parameters.

## Magnetic depth profiles

Once at least one layer is magnetic, the **Magnetic profile** group appears in the basic
controls, below **Magnetism**. The same switches are repeated in `Analysis` ›
`Advanced` › `Plot control`, and the two share one selection.

<!-- TODO: screenshot of the Magnetic profile group -> _images/sample_magnetic_profile.png -->

- **Show ρ↑ and ρ↓** - adds the spin-up and spin-down potentials
  `ρ ± ρM·cos(θM − A)` for each magnetic model to the SLD chart, dashed in the model's
  colour. For non-magnetic layers the two curves collapse onto the nuclear SLD.
- **Show ρM** - the magnetic SLD profile on its own.
- **Show θM** - the in-plane moment angle, on its own right-hand axis. `θM` is only defined
  where there is a moment, so the curve is drawn in pieces rather than joined across the
  gaps.
- **Show moment arrows** - see [arrows on the SLD chart](#moment-arrows-on-the-sld-chart)
  below. Off by default.
- **Show R↑↑ and R↓↓** - splits each magnetic model's reflectivity into its two
  non-spin-flip cross-sections on the **Model** page reflectivity chart, dashed in the
  model's colour with their own legend rows. Off by default.

The y-range of the SLD chart covers every visible curve and grows when a curve is switched
on, so `ρ + ρM` is never clipped. If no model is magnetic, the chart, its legend and the
sidebar are unchanged.

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
- screen **right is the guide field H**, and the angle drawn is `φ`, measured from **H**
  counterclockwise: `φ = θM − 270°`;
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

Every arrow view shows the **H →** reference on screen. Tooltips lead with `φ`, then the
`θM` and signed `ρM` the sidebar edits, then the split `M∥` / `M⊥` - the components the
non-spin-flip and spin-flip channels see.

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

(moment-arrows-on-the-sld-chart)=
### On the SLD chart

**Show moment arrows** adds a band above the chart, one arrow per magnetic layer at its
depth - a ribbon of compasses over the `z` axis. It is off by default because that chart
is already dense.

- The band sits *above* the plot, so it never overlaps the curves and never changes the
  SLD y-range.
- Arrows follow zoom, pan and a reversed `z` axis.
- Each band is coloured and labelled with its model, so two `Fe` layers in two models are
  told apart. At most two bands are drawn; further magnetic models are reported as
  `+N models`.
- In a dense stack, an arrow that would collide with the previous one is skipped and
  counted as `+n` at the end of the band, whose tooltip lists which layers are hidden.
  Zooming in recovers them.

```{note}
The `refl1d` calculator cannot repeat slabs that carry magnetism, so a magnetic model with
a repeating multilayer has no magnetic depth profile at all - and therefore no arrow band.
The **Magnetic profile** group reports the reason.
```
