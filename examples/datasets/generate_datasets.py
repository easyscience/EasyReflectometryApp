# SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
"""Generate the demo datasets for the constraints functionality.

Each ``.ort`` file in this directory is simulated from a *known* structure
(documented in the file header and in ``README.md``) with reproducible 4 %
noise, so every constraint demo has a ground truth to compare against:

- ``two_layer_film.ort``        inequality budget + derived total thickness
- ``swapped_layers.ort``        layer-ordering inequality (t_top < t_bottom)
- ``ni_ti_multilayer.ort``      constant-period recipe on a repeating multilayer
- ``dppc_monolayer.ort``        surfactant recipes (equal APM, conformal / solvent roughness)

Re-run from the repository root to regenerate::

    python examples/datasets/generate_datasets.py
"""

import datetime
from pathlib import Path

import numpy as np
from orsopy import fileio
from orsopy.fileio import model_language

from easyreflectometry.calculators import CalculatorFactory
from easyreflectometry.model import Model
from easyreflectometry.model import PercentageFwhm
from easyreflectometry.sample import Layer
from easyreflectometry.sample import Material
from easyreflectometry.sample import Multilayer
from easyreflectometry.sample import RepeatingMultilayer
from easyreflectometry.sample import Sample
from easyreflectometry.sample import SurfactantLayer

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
        name: model_language.Material(sld=fileio.Value(sld * 1e-6, '1/angstrom^2'))
        for name, sld in material_slds.items()
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


def write_ort(filename: str, title: str, sample_name: str, description: str, q, r, sr, sample_model=None) -> Path:
    """Write one ORSO file with the ground truth recorded in the header."""
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
        data_set=0,
    )
    # Gaussian sigma of the dQ/Q resolution (FWHM -> sigma).
    sq = (RESOLUTION_PERCENT / 100.0) * q / 2.355
    dataset = fileio.OrsoDataset(header, np.array([q, r, sr, sq]).T)
    path = OUTPUT_DIR / filename
    fileio.save_orso([dataset], str(path))
    print(f'wrote {path.name}: {len(q)} points')
    return path


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
        q, r, sr,
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
        q, r, sr,
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
        np.linspace(0.008, 0.35, 220), r, sr,
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
        q_surf, r, sr,
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


if __name__ == '__main__':
    main()
