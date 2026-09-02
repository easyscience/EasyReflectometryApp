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
