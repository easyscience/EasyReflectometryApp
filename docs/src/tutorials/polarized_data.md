# Polarised data

A polarised measurement records up to four spin channels of the same sample. The app loads
them as a single experiment, draws them separately, and fits them together against one
model.

| Channel | Meaning |
|---|---|
| `pp` ↑↑ | non-spin-flip, both incoming and outgoing spin up |
| `mm` ↓↓ | non-spin-flip, both incoming and outgoing spin down |
| `pm` ↑↓ | spin-flip |
| `mp` ↓↑ | spin-flip |

## Loading one file per channel

The **Experimental data** group on the `Experiment` page has a second button,
**Load polarized experiment (file per channel)**, below the ordinary
**Load experiment(s) from file(s)**. Select one file per spin channel - the file picker
allows multiple selection - and the **Assign spin channels** dialog opens.

<!-- TODO: screenshot of the Assign spin channels dialog -> _images/exp_polarized_assign.png -->

Each file gets a channel drop-down, pre-assigned from the ORSO `polarization` header or,
failing that, from the file name. Adjust anything that came out wrong. Any number of
channels may be assigned, a single one included, and a file that should be ignored is set
to **not used**.

The dialog refuses to continue and explains why if a channel is assigned to more than one
file, if a file is missing, or if nothing at all is assigned.

```{note}
One resolution function is used for the whole polarised experiment, taken from the first
assigned channel. Differing per-channel resolution metadata in the other files is ignored;
the dialog says so.
```

If the project's calculation engine cannot model magnetism, the dialog also notes that the
channels will be loaded and displayed but not modelled until the sample has magnetic layers
and the engine is switched - see [magnetic layers](./magnetism.md).

## Seeing the channels

- The experiment chart draws one measured series, with its error bounds, per **visible**
  channel, in a fixed palette (↑↑ `pp`, ↑↓ `pm`, ↓↑ `mp`, ↓↓ `mm`), with a per-channel
  legend.
- The **Polarization channels** group in the advanced controls of the `Experiment` page
  toggles which channels are drawn. At least one measured channel always stays visible.
- Experiment lists mark a polarised experiment with a `⇅N` badge, `N` being the number of
  measured spin channels.
- With several experiments selected, each polarised experiment contributes one series per
  visible channel, using the experiment colour as the hue base.

## Spin asymmetry

The spin asymmetry

```
SA(q) = (R↑↑ − R↓↓) / (R↑↑ + R↓↓)
```

is available as a **Spin asymmetry** tab next to **Reflectivity** on the `Experiment` page
(measured data only) and as a third tab of the lower panel on the `Analysis` page (measured
data plus the model). Neither tab is shown unless the experiment measured **both**
non-spin-flip channels; without one, the `Experiment` page has no tab strip at all.

<!-- TODO: screenshot of the spin asymmetry tab -> _images/exp_spin_asymmetry.png -->

Error bars are propagated from the channel uncertainties. Two kinds of point are dropped,
with a note of how many:

- points where `R↑↑ + R↓↓` is not significantly above zero - the background-dominated tail,
  which would otherwise wreck the axis;
- points where the two channels do not share the same `q`.

The axis shows the full `[−1, 1]` window and expands only if background-subtracted data go
outside it.

## Fitting a polarised experiment

Fitting a polarised experiment fits **all** its measured spin channels at once against the
shared model. Thickness, roughness, nuclear SLD, scale and background are common to every
channel; `ρM` and `θM` are constrained by all of them. Polarised and ordinary experiments
can be fitted together in the same refinement.

The analysis and residual charts draw one measured/calculated pair per visible channel,
each with that channel's cross-section. A channel the model cannot calculate - a spin-flip
channel on a non-magnetic sample - shows its measured points only and contributes no
residuals.

In the `Summary` report a polarised experiment contributes one row per measured spin
channel, named after the channel, and the report figures plot each channel in its channel
colour.

## Limitations

- One resolution function per polarised experiment, taken from the first assigned channel.
- Bayesian sampling of polarised experiments is not supported yet; see
  [Bayesian analysis](./bayesian.md).
