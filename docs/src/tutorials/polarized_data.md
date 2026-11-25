# Polarised data

A polarised measurement records up to four spin channels of the same sample. The app loads
them as one experiment, draws each channel separately, and fits all of them together
against one model.

| Channel | Meaning |
|---|---|
| `pp` ↑↑ | non-spin-flip, both incoming and outgoing spin up |
| `mm` ↓↓ | non-spin-flip, both incoming and outgoing spin down |
| `pm` ↑↓ | spin-flip |
| `mp` ↓↑ | spin-flip |

## Loading one file per channel

In the **Experimental data** group on the `Experiment` page, below the ordinary
**Load experiment(s) from file(s)** button, there is a second button:
**Load polarized experiment (file per channel)**. Select one file per spin channel (the
file picker accepts several files at once), and the **Assign spin channels** dialog opens.

<!-- TODO: screenshot of the Assign spin channels dialog -> _images/exp_polarized_assign.png -->

Each file gets a channel drop-down. The app fills it in from the ORSO `polarization`
header, or from the file name if there is no header. Correct any wrong assignments. You
can assign any number of channels, including just one, and set a file you want to ignore
to **not used**.

The dialog will not continue if a channel is assigned to more than one file, if a file is
missing, or if nothing is assigned, and it tells you which of these is the problem.

```{note}
Each channel keeps the resolution of its own file. The fit, the per-channel curves on the
`Analysis` page and the report all smear a channel with its measured resolution. The
model's resolution field on the `Experiment` page follows the first assigned channel, and
is used for simulations and for files without a resolution column.
```

If the project's calculation engine cannot model magnetism, the dialog also tells you that
the channels will be loaded and displayed, but not modelled until the sample has magnetic
layers and you switch the engine. See [magnetic layers](./magnetism.md).

## Seeing the channels

- The experiment chart draws one measured series with error bounds for each visible
  channel, in a fixed palette (↑↑ `pp`, ↑↓ `pm`, ↓↑ `mp`, ↓↓ `mm`), with a legend entry per
  channel.
- The **Polarization channels** group in the advanced controls of the `Experiment` page
  sets which channels are drawn. At least one measured channel always stays visible.
- Experiment lists mark a polarised experiment with a `⇅N` badge, where `N` is the number
  of measured spin channels.
- When several experiments are selected, each polarised experiment adds one series per
  visible channel, with colours based on the experiment's colour.

## Spin asymmetry

The spin asymmetry is

```
SA(q) = (R↑↑ − R↓↓) / (R↑↑ + R↓↓)
```

It is shown in a **Spin asymmetry** tab next to **Reflectivity** on the `Experiment` page
(measured data only), and in a third tab of the lower panel on the `Analysis` page
(measured data and the model). Both tabs appear only if the experiment measured both
non-spin-flip channels. If one is missing, the `Experiment` page shows no tab strip.

<!-- TODO: screenshot of the spin asymmetry tab -> _images/exp_spin_asymmetry.png -->

Error bars are propagated from the channel uncertainties. Two kinds of points are left
out, and a note says how many:

- points where `R↑↑ + R↓↓` is not significantly above zero, i.e. the background-dominated
  tail, which would otherwise ruin the axis scaling;
- points where the two channels do not have the same `q`.

The axis shows the full `[−1, 1]` range and widens only if background-subtracted data
fall outside it.

## Fitting a polarised experiment

When you fit a polarised experiment, all of its measured spin channels are fitted at once
against the shared model. Thickness, roughness, nuclear SLD, scale and background are
common to every channel, and all channels together constrain `ρM` and `θM`. You can fit
polarised and ordinary experiments together in the same refinement.

The analysis and residual charts draw one measured and calculated pair for each visible
channel, each with that channel's cross-section. If the model cannot calculate a channel,
for example a spin-flip channel on a non-magnetic sample, the chart shows only its measured
points and the channel adds no residuals.

In the `Summary` report a polarised experiment has one row per measured spin channel,
named after the channel, and the report figures plot each channel in its own colour.

## Limitations

- Bayesian sampling does not support polarised experiments yet; see
  [Bayesian analysis](./bayesian.md).
