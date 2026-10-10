# SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
"""Generate the demo datasets for the constraints and multiple-contrast functionality.

Each ``.ort`` file in this directory is simulated from a *known* structure
(documented in the file header and in ``README.md``) with reproducible 4 %
noise, so every constraint demo has a ground truth to compare against:

- ``two_layer_film.ort``        inequality budget + derived total thickness
- ``swapped_layers.ort``        layer-ordering inequality (t_top < t_bottom)
- ``ni_ti_multilayer.ort``      constant-period recipe on a repeating multilayer
- ``dppc_monolayer.ort``        surfactant recipes (equal APM, conformal / solvent roughness)
- ``dppc_contrasts.ort``        three contrasts of one monolayer in one file (joint fit)
- ``film_contrasts.ort``        three water contrasts of a film on silicon, slab model in each header

Re-run from the repository root to regenerate::

    python examples/datasets/generate_datasets.py
"""

import datetime
from pathlib import Path

import numpy as np
from easyreflectometry.calculators import CalculatorFactory
from easyreflectometry.contrasts import ReplaceFormula
from easyreflectometry.contrasts import ReplaceMaterial
from easyreflectometry.contrasts import derive_contrast
from easyreflectometry.model import Model
from easyreflectometry.model import PercentageFwhm
from easyreflectometry.sample import Layer
from easyreflectometry.sample import Material
from easyreflectometry.sample import Multilayer
from easyreflectometry.sample import RepeatingMultilayer
from easyreflectometry.sample import Sample
from easyreflectometry.sample import SurfactantLayer
from orsopy import fileio
from orsopy.fileio import model_language

OUTPUT_DIR = Path(__file__).parent
RESOLUTION_PERCENT = 5.0
NOISE_RELATIVE = 0.04
BACKGROUND = 1e-7


def simulate(model: Model, q: np.ndarray, seed: int) -> tuple[np.ndarray, np.ndarray]:
    """Reflectivity of `model` at `q` with reproducible multiplicative noise."""
    interface = CalculatorFactory()
    model.interface = interface
    reflectivity = interface.fit_func(q, model.unique_name)
    rng = np.random.default_rng(seed)
    sigma = NOISE_RELATIVE * reflectivity + 0.2 * BACKGROUND
    measured = np.clip(reflectivity + rng.normal(0.0, sigma), 0.1 * BACKGROUND, None)
    return measured, sigma


def orso_sample_model(stack: str, layer_definitions: dict, material_slds: dict) -> model_language.SampleModel:
    """ORSO model-language description of the simulated structure.

    This is what the application's *Sample > Load a sample* import parses to
    rebuild the layer stack (``load_orso_model``), so the demo files are
    self-describing: importing one also sets up the matching sample.

    ``layer_definitions``: name -> (material name, thickness / angstrom, roughness / angstrom)
    ``material_slds``: material name -> SLD in 1e-6 / angstrom^2 (written in absolute units)
    """
    materials = {
        name: model_language.Material(sld=fileio.Value(sld * 1e-6, '1/angstrom^2')) for name, sld in material_slds.items()
    }
    layers = {
        name: model_language.Layer(
            thickness=fileio.Value(thickness, 'angstrom'),
            roughness=fileio.Value(roughness, 'angstrom'),
            material=material,
        )
        for name, (material, thickness, roughness) in layer_definitions.items()
    }
    return model_language.SampleModel(
        stack=stack,
        layers=layers,
        materials=materials,
        globals=model_language.ModelParameters(length_unit='angstrom'),
        origin='simulated ground truth',
    )


def ort_dataset(title: str, sample_name: str, description: str, q, r, sr, sample_model=None, data_set=0):
    """One ORSO dataset with the ground truth recorded in its header."""
    header = fileio.Orso(
        data_source=fileio.DataSource(
            owner=fileio.Person(name='EasyReflectometry', affiliation='EasyScience'),
            experiment=fileio.Experiment(
                title=title,
                instrument='simulation',
                start_date=datetime.datetime(2026, 8, 24, 0, 0, 0),
                probe='neutron',
            ),
            sample=fileio.Sample(name=sample_name, description=description, model=sample_model),
            measurement=fileio.Measurement(
                instrument_settings=fileio.InstrumentSettings(
                    incident_angle=fileio.ValueRange(0.1, 3.0, 'deg'),
                    wavelength=fileio.Value(6.0, 'angstrom'),
                ),
                data_files=[],
            ),
        ),
        reduction=fileio.Reduction(software=fileio.Software(name='easyreflectometry (simulated)')),
        columns=[
            fileio.Column('Qz', '1/angstrom', 'normal wavevector transfer'),
            fileio.Column('R', None, 'reflectivity'),
            fileio.ErrorColumn('R', 'uncertainty', 'sigma'),
            fileio.ErrorColumn('Qz', 'resolution', 'sigma'),
        ],
        data_set=data_set,
    )
    # Gaussian sigma of the dQ/Q resolution (FWHM -> sigma).
    sq = (RESOLUTION_PERCENT / 100.0) * q / 2.355
    return fileio.OrsoDataset(header, np.array([q, r, sr, sq]).T)


def save(filename: str, datasets: list) -> Path:
    path = OUTPUT_DIR / filename
    fileio.save_orso(datasets, str(path))
    print(f'wrote {path.name}: {len(datasets)} dataset(s), {sum(len(d.data) for d in datasets)} points')
    return path


def write_ort(filename: str, title: str, sample_name: str, description: str, q, r, sr, sample_model=None) -> Path:
    """Write one ORSO file with the ground truth recorded in the header."""
    return save(filename, [ort_dataset(title, sample_name, description, q, r, sr, sample_model)])


def main() -> None:
    q = np.linspace(0.008, 0.30, 180)

    # ------------------------------------------------------------------ 1
    # Two-layer film: budget + derived total thickness.
    # Truth: t_A = 35 A (SLD 3.0) on t_B = 55 A (SLD 5.0), total exactly 90 A.
    film_a = Multilayer(Layer(Material(3.0, 0.0, 'MatA'), thickness=35.0, roughness=3.0, name='A'), name='Film A')
    film_b = Multilayer(Layer(Material(5.0, 0.0, 'MatB'), thickness=55.0, roughness=3.0, name='B'), name='Film B')
    model = Model(
        sample=Sample(
            Multilayer(Layer(Material(0.0, 0.0, 'Air'), thickness=0.0, roughness=0.0, name='Air'), name='Superphase'),
            film_a,
            film_b,
            Multilayer(Layer(Material(2.07, 0.0, 'Si'), thickness=0.0, roughness=2.0, name='Si'), name='Subphase'),
            populate_if_none=False,
        ),
        scale=1.0,
        background=BACKGROUND,
        resolution_function=PercentageFwhm(RESOLUTION_PERCENT),
    )
    r, sr = simulate(model, q, seed=1)
    write_ort(
        'two_layer_film.ort',
        'Two-layer film with a 90 A thickness budget',
        'air / MatA / MatB / Si',
        'TRUTH: t_A = 35 A (SLD 3.0), t_B = 55 A (SLD 5.0), roughness 3 A, '
        'total film thickness exactly 90 A. Demo: derived total_thickness, '
        'inequality constraints t_A < t_B and t_A + t_B <= 90 (BUMPS only).',
        q,
        r,
        sr,
        sample_model=orso_sample_model(
            stack='ambient | filmA | filmB | substrate',
            layer_definitions={
                'ambient': ('air', 0.0, 0.0),
                'filmA': ('MatA', 35.0, 3.0),
                'filmB': ('MatB', 55.0, 3.0),
                'substrate': ('Si', 0.0, 2.0),
            },
            material_slds={'air': 0.0, 'MatA': 3.0, 'MatB': 5.0, 'Si': 2.07},
        ),
    )

    # ------------------------------------------------------------------ 2
    # Ordering: a thin low-SLD layer on a thick high-SLD layer.
    # Truth: t_top = 20 A (SLD 2.5) above t_bottom = 60 A (SLD 4.2).
    top = Multilayer(Layer(Material(2.5, 0.0, 'TopMat'), thickness=20.0, roughness=3.0, name='Top'), name='Top layer')
    bottom = Multilayer(
        Layer(Material(4.2, 0.0, 'BottomMat'), thickness=60.0, roughness=3.0, name='Bottom'), name='Bottom layer'
    )
    model = Model(
        sample=Sample(
            Multilayer(Layer(Material(0.0, 0.0, 'Air'), thickness=0.0, roughness=0.0, name='Air'), name='Superphase'),
            top,
            bottom,
            Multilayer(Layer(Material(2.07, 0.0, 'Si'), thickness=0.0, roughness=2.0, name='Si'), name='Subphase'),
            populate_if_none=False,
        ),
        scale=1.0,
        background=BACKGROUND,
        resolution_function=PercentageFwhm(RESOLUTION_PERCENT),
    )
    r, sr = simulate(model, q, seed=2)
    write_ort(
        'swapped_layers.ort',
        'Layer ordering: thin capping layer on a thick layer',
        'air / thin TopMat / thick BottomMat / Si',
        'TRUTH: t_top = 20 A (SLD 2.5), t_bottom = 60 A (SLD 4.2), roughness 3 A. '
        'Demo: start the fit from swapped thicknesses (60 / 20) and use the '
        'inequality t_top < t_bottom to keep the physical assignment.',
        q,
        r,
        sr,
        sample_model=orso_sample_model(
            stack='ambient | top | bottom | substrate',
            layer_definitions={
                'ambient': ('air', 0.0, 0.0),
                'top': ('TopMat', 20.0, 3.0),
                'bottom': ('BottomMat', 60.0, 3.0),
                'substrate': ('Si', 0.0, 2.0),
            },
            material_slds={'air': 0.0, 'TopMat': 2.5, 'BottomMat': 4.2, 'Si': 2.07},
        ),
    )

    # ------------------------------------------------------------------ 3
    # Repeating multilayer with a fixed period.
    # Truth: [Ti 30 A / Ni 70 A] x 8, period exactly 100 A, conformal roughness 4 A.
    ti = Layer(Material(-1.95, 0.0, 'Ti'), thickness=30.0, roughness=4.0, name='Ti')
    ni = Layer(Material(9.41, 0.0, 'Ni'), thickness=70.0, roughness=4.0, name='Ni')
    stack = RepeatingMultilayer([ti, ni], repetitions=8, name='Ti/Ni stack')
    model = Model(
        sample=Sample(
            Multilayer(Layer(Material(0.0, 0.0, 'Air'), thickness=0.0, roughness=0.0, name='Air'), name='Superphase'),
            stack,
            Multilayer(Layer(Material(2.07, 0.0, 'Si'), thickness=0.0, roughness=4.0, name='Si'), name='Subphase'),
            populate_if_none=False,
        ),
        scale=1.0,
        background=BACKGROUND,
        resolution_function=PercentageFwhm(RESOLUTION_PERCENT),
    )
    r, sr = simulate(model, np.linspace(0.008, 0.35, 220), seed=3)
    write_ort(
        'ni_ti_multilayer.ort',
        'Ti/Ni repeating multilayer with a 100 A period',
        'air / [Ti 30 / Ni 70] x8 / Si',
        'TRUTH: period exactly 100 A (Ti 30 A, SLD -1.95; Ni 70 A, SLD 9.41), 8 repetitions, '
        'conformal roughness 4 A. Demo: physics recipes "Constant period" and '
        '"Conformal roughness" on the repeating multilayer; the Bragg peak position '
        'pins the period while the Ti/Ni split is fitted.',
        np.linspace(0.008, 0.35, 220),
        r,
        sr,
        sample_model=orso_sample_model(
            # The repetitions are resolved to 16 individual layers on import;
            # rebuild a RepeatingMultilayer by hand for the constant-period demo.
            stack='ambient | 8 ( layerTi | layerNi ) | substrate',
            layer_definitions={
                'ambient': ('air', 0.0, 0.0),
                'layerTi': ('Ti', 30.0, 4.0),
                'layerNi': ('Ni', 70.0, 4.0),
                'substrate': ('Si', 0.0, 4.0),
            },
            material_slds={'air': 0.0, 'Ti': -1.95, 'Ni': 9.41, 'Si': 2.07},
        ),
    )

    # ------------------------------------------------------------------ 4
    # DPPC monolayer at the air/D2O interface.
    # Truth: default DPPC surfactant layer, equal head/tail APM (48 A^2),
    # conformal roughness 3 A shared with the D2O subphase.
    surfactant = SurfactantLayer(name='DPPC')
    surfactant.tail_layer.area_per_molecule_parameter.value = 48.0
    surfactant.constrain_area_per_molecule = True
    surfactant.conformal_roughness = True
    d2o_layer = Layer(Material(6.36, 0.0, 'D2O'), thickness=0.0, roughness=3.0, name='D2O')
    model = Model(
        sample=Sample(
            Multilayer(Layer(Material(0.0, 0.0, 'Air'), thickness=0.0, roughness=0.0, name='Air'), name='Superphase'),
            surfactant,
            Multilayer(d2o_layer, name='Subphase'),
            populate_if_none=False,
        ),
        scale=1.0,
        background=5e-7,
        resolution_function=PercentageFwhm(RESOLUTION_PERCENT),
    )
    surfactant.layers[0].roughness.value = 3.0
    surfactant.constrain_solvent_roughness(d2o_layer.roughness)
    q_surf = np.linspace(0.01, 0.30, 160)
    r, sr = simulate(model, q_surf, seed=4)
    tail, head = surfactant.tail_layer, surfactant.head_layer
    write_ort(
        'dppc_monolayer.ort',
        'DPPC monolayer at the air/D2O interface',
        'air / DPPC tail / DPPC head / D2O',
        'TRUTH: default DPPC surfactant layer, area per molecule 48 A^2 shared by head '
        'and tail, conformal roughness 3 A extended to the D2O subphase. Demo: physics '
        'recipes "Equal head/tail area per molecule", "Conformal roughness" and '
        '"Solvent roughness follows the surfactant".',
        q_surf,
        r,
        sr,
        # Slab-equivalent of the surfactant (effective solvated SLDs); replace it
        # with a SurfactantLayer assembly for the physics-recipe demo.
        sample_model=orso_sample_model(
            stack='ambient | tails | heads | subphase',
            layer_definitions={
                'ambient': ('air', 0.0, 0.0),
                'tails': ('TailMat', float(tail.thickness.value), float(tail.roughness.value)),
                'heads': ('HeadMat', float(head.thickness.value), float(head.roughness.value)),
                'subphase': ('D2O', 0.0, float(d2o_layer.roughness.value)),
            },
            material_slds={
                'air': 0.0,
                'TailMat': float(getattr(tail.material.sld, 'value', tail.material.sld)),
                'HeadMat': float(getattr(head.material.sld, 'value', head.material.sld)),
                'D2O': 6.36,
            },
        ),
    )

    # ------------------------------------------------------------------ 5
    # Three contrasts of one d-DPPC monolayer, one dataset each in a single file:
    # d-DPPC on D2O (the reference), d-DPPC on air-contrast-matched water (ACMW;
    # the subphase and the head-group solvent are the same material, so both
    # change) and h-DPPC on D2O (tail formula C32H64). The structure is shared;
    # scale and background are each contrast's own.
    d2o = Material(6.36, 0.0, 'D2O')
    surfactant = SurfactantLayer(name='DPPC')
    surfactant.head_layer.solvent = d2o
    surfactant.tail_layer.thickness.value = 15.0
    surfactant.head_layer.thickness.value = 9.5
    surfactant.head_layer.solvent_fraction = 0.3
    surfactant.tail_layer.area_per_molecule_parameter.value = 52.0
    surfactant.constrain_area_per_molecule = True
    surfactant.conformal_roughness = True
    surfactant.layers[0].roughness.value = 3.5
    reference = Model(
        sample=Sample(
            Multilayer(Layer(Material(0.0, 0.0, 'Air'), thickness=0.0, roughness=0.0, name='Air'), name='Superphase'),
            surfactant,
            Multilayer(Layer(d2o, thickness=0.0, roughness=3.5, name='Water'), name='Subphase'),
            populate_if_none=False,
        ),
        name='d-DPPC / D2O',
        background=3e-7,
        resolution_function=PercentageFwhm(RESOLUTION_PERCENT),
    )
    on_acmw = derive_contrast(
        reference, name='d-DPPC / ACMW', substitutions=[ReplaceMaterial(d2o, Material(0.0, 0.0, 'ACMW'))]
    )
    on_acmw.background.value = 1e-6
    hydrogenous = derive_contrast(
        reference, name='h-DPPC / D2O', substitutions=[ReplaceFormula(surfactant.tail_layer, 'C32H64')]
    )
    hydrogenous.background.value = 6e-7
    hydrogenous.scale.value = 0.95
    truth = (
        'TRUTH (all contrasts): DPPC monolayer, area per molecule 52 A^2 shared by head and tail, '
        'tail 15.0 A, head 9.5 A with head solvent fraction 0.30, conformal roughness 3.5 A '
        '(the subphase too). Per contrast: '
        'd-DPPC/D2O scale 1.00, background 3e-7; '
        'd-DPPC/ACMW scale 1.00, background 1e-6; '
        'h-DPPC/D2O scale 0.95, background 6e-7. '
        'Demo: Add contrast (replace D2O by ACMW; replace the tail formula by C32H64), '
        'pair each dataset with its contrast and fit them jointly.'
    )
    datasets = []
    for seed, (label, model, tails, subphase) in enumerate(
        (
            ('1_dDPPC_D2O', reference, 'C32D64', 'D2O'),
            ('2_dDPPC_ACMW', on_acmw, 'C32D64', 'ACMW'),
            ('3_hDPPC_D2O', hydrogenous, 'C32H64', 'D2O'),
        ),
        start=5,
    ):
        r, sr = simulate(model, q_surf, seed=seed)
        datasets.append(
            ort_dataset(
                f'DPPC monolayer: {model.name}',
                f'air / DPPC ({tails} tails) / {subphase}',
                truth,
                q_surf,
                r,
                sr,
                data_set=label,
            )
        )
    save('dppc_contrasts.ort', datasets)

    # ------------------------------------------------------------------ 6
    # A dense (non-swelling) film on silicon under three waters, one dataset
    # each in a single file. Only the water changes, so the structure is plain
    # slabs: each dataset's header carries its own exact stack, and loading the
    # sample from the file builds the D2O one (the first dataset's).
    # Truth: Si | SiO2 15 A (SLD 3.47, roughness 3) | film 80 A (SLD 2.0,
    # roughness 5) | water (roughness 4).
    water = Material(6.36, 0.0, 'D2O')
    reference = Model(
        sample=Sample(
            Multilayer(Layer(Material(2.07, 0.0, 'Si'), thickness=0.0, roughness=0.0, name='Si'), name='Superphase'),
            Multilayer(
                [
                    Layer(Material(3.47, 0.0, 'SiO2'), thickness=15.0, roughness=3.0, name='SiO2'),
                    Layer(Material(2.0, 0.0, 'Film'), thickness=80.0, roughness=5.0, name='Film'),
                ],
                name='Loaded layer',
            ),
            Multilayer(Layer(water, thickness=0.0, roughness=4.0, name='Water'), name='Subphase'),
            populate_if_none=False,
        ),
        name='D2O',
        background=2e-7,
        resolution_function=PercentageFwhm(RESOLUTION_PERCENT),
    )
    waters = (('D2O', 6.36, 1.0, 2e-7), ('H2O', -0.56, 0.95, 5e-6), ('CMSi', 2.07, 1.0, 1e-6))
    truth = (
        'TRUTH (all contrasts): Si | SiO2 15 A (SLD 3.47, roughness 3 A) | film 80 A (SLD 2.0, '
        'roughness 5 A) | water (roughness 4 A). Per contrast: '
        + '; '.join(f'{name} (SLD {sld}) scale {scale:.2f}, background {bkg:.0e}' for name, sld, scale, bkg in waters)
        + '. Demo: load the sample from this file (the D2O stack), Add contrast replacing D2O by H2O '
        'and by CMSi, pair each dataset with its contrast and fit them jointly.'
    )
    datasets = []
    for seed, (name, sld, scale, bkg) in enumerate(waters, start=10):
        if name == 'D2O':
            model = reference
        else:
            model = derive_contrast(reference, name=name, substitutions=[ReplaceMaterial(water, Material(sld, 0.0, name))])
        model.scale.value = scale
        model.background.value = bkg
        r, sr = simulate(model, q, seed=seed)
        datasets.append(
            ort_dataset(
                f'Film on silicon in {name}',
                f'Si / SiO2 / film / {name}',
                truth,
                q,
                r,
                sr,
                # The layer keys name the materials on import; the material keys
                # must differ from them (lower case).
                sample_model=orso_sample_model(
                    stack=f'Si | SiO2 | Film | {name}',
                    layer_definitions={
                        'Si': ('si', 0.0, 0.0),
                        'SiO2': ('sio2', 15.0, 3.0),
                        'Film': ('film', 80.0, 5.0),
                        name: (name.lower(), 0.0, 4.0),
                    },
                    material_slds={'si': 2.07, 'sio2': 3.47, 'film': 2.0, name.lower(): sld},
                ),
                data_set=f'{seed - 9}_{name}',
            )
        )
    save('film_contrasts.ort', datasets)


if __name__ == '__main__':
    main()
