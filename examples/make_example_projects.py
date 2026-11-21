"""Build the example projects listed in the Project page's Examples group.

Each example is an ordinary project file (``project.json``) built with the library from one of
the datasets in ``examples/datasets``, plus an ``index.json`` that gives the order, name and
one-line description the app lists them with. The models start from a deliberately rough guess
with sensible parameters free and bounded, so that an example can be fitted straight after
loading it.

Regenerate after a change of the project file format, or of an example below, with::

    python examples/make_example_projects.py

The output goes to ``EasyReflectometryApp/Examples``, which is shipped with the app.
"""

import json
import shutil
import warnings
from pathlib import Path
from typing import Callable

from easyreflectometry import Project
from easyreflectometry.contrasts import ReplaceFormula
from easyreflectometry.contrasts import ReplaceMaterial
from easyreflectometry.fitting import Minimizers
from easyreflectometry.inequality_constraints import InequalitySpec
from easyreflectometry.model import Model
from easyreflectometry.model import ModelCollection
from easyreflectometry.model import PercentageFwhm
from easyreflectometry.sample import Layer
from easyreflectometry.sample import LayerAreaPerMolecule
from easyreflectometry.sample import LayerMagnetism
from easyreflectometry.sample import Material
from easyreflectometry.sample import Multilayer
from easyreflectometry.sample import RepeatingMultilayer
from easyreflectometry.sample import Sample
from easyreflectometry.sample import SurfactantLayer
from easyscience import global_object

ROOT = Path(__file__).resolve().parents[1]
DATASETS = ROOT / 'examples' / 'datasets'
OUTPUT = ROOT / 'EasyReflectometryApp' / 'Examples'

#: The minimizer a new project gets in the app (see logic/minimizers.py).
APP_DEFAULT_MINIMIZER = Minimizers.Bumps_lm


# ----- helpers -----


def new_project(name: str, description: str) -> Project:
    global_object.registry.clear()
    project = Project()
    project._info['name'] = name
    project._info['short_description'] = description
    project.fit_settings.minimizer = APP_DEFAULT_MINIMIZER
    project.fit_settings.mode = 'minimize'
    return project


def fix_all(project: Project) -> None:
    """Fix every independent parameter, so that each example frees exactly what it fits."""
    for model in project.models:
        for parameter in model.get_all_parameters():
            if parameter.independent:
                parameter.fixed = True


def free(parameter, minimum: float, maximum: float) -> None:
    parameter.min = minimum
    parameter.max = maximum
    parameter.fixed = False


def slab(material: Material, thickness: float, roughness: float, name: str) -> Layer:
    return Layer(material=material, thickness=thickness, roughness=roughness, name=name)


def pair_experiments(project: Project, model_for_name: dict[str, int]) -> None:
    """Bind each loaded experiment to its model, by a fragment of the experiment's name."""
    for key, experiment in project.experiments.items():
        matches = [index for fragment, index in model_for_name.items() if fragment in experiment.name]
        if len(matches) != 1:
            raise RuntimeError(f'Cannot pair experiment {experiment.name!r} with a model')
        project.set_model_for_experiment(key, matches[0])


# ----- examples, simplest first -----


def polymer_film() -> Project:
    project = new_project(
        'Polymer film on silicon',
        'A polymer film on a silicon block measured against D2O at Platypus (ANSTO).',
    )
    si = Material(sld=2.07, isld=0, name='Si')
    sio2 = Material(sld=3.47, isld=0, name='SiO2')
    film = Material(sld=2.0, isld=0, name='Film')
    d2o = Material(sld=6.36, isld=0, name='D2O')
    sio2_layer = slab(sio2, 30, 3, 'SiO2')
    film_layer = slab(film, 250, 3, 'Film')
    subphase = slab(d2o, 0, 3, 'D2O')
    sample = Sample(
        Multilayer(slab(si, 0, 0, 'Si'), name='Superphase'),
        Multilayer([sio2_layer, film_layer], name='Oxide and film'),
        Multilayer(subphase, name='Subphase'),
        name='Polymer film',
    )
    model = Model(sample=sample, scale=1, background=1e-6, resolution_function=PercentageFwhm(2), name='Polymer film')
    project.models = ModelCollection([model])
    project.load_new_experiment(DATASETS / 'measured' / 'polymer_film_platypus.ort')

    fix_all(project)
    free(sio2_layer.thickness, 15, 50)
    free(sio2_layer.roughness, 1, 15)
    free(film_layer.thickness, 200, 300)
    free(film_layer.roughness, 1, 15)
    free(film.sld, 0.1, 3)
    free(subphase.roughness, 1, 15)
    free(model.scale, 0.5, 1.5)
    free(model.background, 1e-8, 1e-5)
    return project


def _dspc(
    tail_formula: str,
    head_formula: str,
    solvent: Material,
    air: Material,
    name: str,
    tail_thickness: float = 20,
    head_thickness: float = 12,
) -> SurfactantLayer:
    tail = LayerAreaPerMolecule(
        molecular_formula=tail_formula,
        thickness=tail_thickness,
        solvent=air,
        solvent_fraction=0.0,
        area_per_molecule=45,
        roughness=3,
        name='DSPC tail',
    )
    head = LayerAreaPerMolecule(
        molecular_formula=head_formula,
        thickness=head_thickness,
        solvent=solvent,
        solvent_fraction=0.5,
        area_per_molecule=45,
        roughness=3,
        name='DSPC head',
    )
    surfactant = SurfactantLayer(tail_layer=tail, head_layer=head, name=name)
    surfactant.constrain_area_per_molecule = True
    surfactant.conformal_roughness = True
    return surfactant


#: The SURF data are not normalised to a critical edge: the scale refines to about 0.2.
SURF_SCALE = 0.2


def dspc_monolayer() -> Project:
    project = new_project(
        'DSPC monolayer on water',
        'A tail-deuterated DSPC monolayer at the air/D2O interface measured at SURF (ISIS).',
    )
    air = Material(sld=0, isld=0, name='Air')
    d2o = Material(sld=6.36, isld=0, name='D2O')
    # The layer thicknesses are those of the DSPC chemistry, as in the library's monolayer
    # tutorial: one contrast cannot tell head thickness from head hydration.
    dspc = _dspc('C34D70', 'C10H18NO8P', d2o, air, 'd70-DSPC', tail_thickness=17.6, head_thickness=12.9)
    subphase = slab(d2o, 0, 3, 'D2O')
    dspc.constrain_solvent_roughness(subphase.roughness)
    sample = Sample(Multilayer(slab(air, 0, 0, 'Air'), name='Superphase'), dspc, Multilayer(subphase, name='Subphase'))
    model = Model(
        sample=sample, scale=SURF_SCALE, background=5e-7, resolution_function=PercentageFwhm(5), name='d70-DSPC in D2O'
    )
    project.models = ModelCollection([model])
    project.load_new_experiment(DATASETS / 'measured' / 'dspc_d70_d2o_surf.ort')

    fix_all(project)
    free(dspc.tail_layer.area_per_molecule_parameter, 30, 60)
    free(dspc.head_layer.solvent_fraction_parameter, 0.4, 0.7)
    free(model.scale, 0.05, 1.5)
    free(model.background, 4e-7, 1e-6)
    return project


def dspc_contrasts() -> Project:
    project = new_project(
        'DSPC monolayer, three contrasts',
        'Head-, tail- and fully-deuterated DSPC on D2O and air-contrast-matched water, '
        'fitted jointly; measured at SURF (ISIS).',
    )
    air = Material(sld=0, isld=0, name='Air')
    d2o = Material(sld=6.36, isld=0, name='D2O')
    acmw = Material(sld=0, isld=0, name='ACMW')
    dspc = _dspc('C34H70', 'C10D18NO8P', d2o, air, 'd13-DSPC')
    subphase = slab(d2o, 0, 3, 'Water')
    dspc.constrain_solvent_roughness(subphase.roughness)
    sample = Sample(Multilayer(slab(air, 0, 0, 'Air'), name='Superphase'), dspc, Multilayer(subphase, name='Subphase'))
    reference = Model(
        sample=sample, scale=SURF_SCALE, background=5e-7, resolution_function=PercentageFwhm(5), name='d13-DSPC in D2O'
    )
    project.models = ModelCollection([reference])
    tail, head = dspc.tail_layer, dspc.head_layer
    deuterated_tail = ReplaceFormula(target=tail, formula='C34D70')
    project.add_contrast(0, 'd70-DSPC in D2O', [deuterated_tail, ReplaceFormula(target=head, formula='C10H18NO8P')])
    project.add_contrast(0, 'd83-DSPC in ACMW', [deuterated_tail, ReplaceMaterial(old=d2o, new=acmw)])
    project.current_model_index = 0
    project.load_all_experiments_from_file(DATASETS / 'measured' / 'dspc_contrasts_surf.ort')
    pair_experiments(project, {'Head-deuterated': 0, 'Tail-deuterated': 1, 'Fully-deuterated': 2})

    fix_all(project)
    # The contrasts follow the reference's structure; each has its own scale and background.
    # Bounds as in the library's multiple-contrast tutorial.
    free(dspc.tail_layer.thickness, 18, 24)
    free(dspc.head_layer.thickness, 8, 12)
    free(dspc.tail_layer.area_per_molecule_parameter, 40, 50)
    free(dspc.head_layer.solvent_fraction_parameter, 0.2, 0.6)
    for model in project.models:
        free(model.scale, 0.05, 1.5)
        free(model.background, 1e-8, 1e-5)
    return project


def ni_ti_multilayer() -> Project:
    project = new_project(
        'Ni/Ti multilayer',
        'Simulated: eight Ti/Ni bilayers on silicon, a repeating multilayer with a Bragg peak.',
    )
    air = Material(sld=0, isld=0, name='Air')
    ti = slab(Material(sld=-1.95, isld=0, name='Ti'), 35, 4, 'Ti')
    ni = slab(Material(sld=9.41, isld=0, name='Ni'), 65, 4, 'Ni')
    subphase = slab(Material(sld=2.07, isld=0, name='Si'), 0, 4, 'Si')
    stack = RepeatingMultilayer([ti, ni], repetitions=8, name='Ti/Ni stack')
    sample = Sample(Multilayer(slab(air, 0, 0, 'Air'), name='Superphase'), stack, Multilayer(subphase, name='Subphase'))
    model = Model(sample=sample, scale=1, background=1e-7, resolution_function=PercentageFwhm(5), name='Ti/Ni x 8')
    project.models = ModelCollection([model])
    project.load_new_experiment(DATASETS / 'ni_ti_multilayer.ort')

    fix_all(project)
    free(ti.thickness, 20, 45)
    free(ni.thickness, 55, 80)
    free(ti.roughness, 1, 8)
    free(ni.roughness, 1, 8)
    free(subphase.roughness, 1, 8)
    return project


def film_contrasts() -> Project:
    project = new_project(
        'Film in three water contrasts',
        'Simulated: a dense film on silicon measured under D2O, H2O and silicon-matched water, fitted jointly.',
    )
    si = Material(sld=2.07, isld=0, name='Si')
    sio2 = Material(sld=3.47, isld=0, name='SiO2')
    film = Material(sld=1.0, isld=0, name='Film')
    d2o = Material(sld=6.36, isld=0, name='D2O')
    h2o = Material(sld=-0.56, isld=0, name='H2O')
    cmsi = Material(sld=2.07, isld=0, name='CMSi')
    oxide = slab(sio2, 25, 3, 'SiO2')
    film_layer = slab(film, 70, 3, 'Film')
    subphase = slab(d2o, 0, 4, 'Water')
    sample = Sample(
        Multilayer(slab(si, 0, 0, 'Si'), name='Superphase'),
        Multilayer([oxide, film_layer], name='Oxide and film'),
        Multilayer(subphase, name='Subphase'),
    )
    reference = Model(sample=sample, scale=1, background=2e-7, resolution_function=PercentageFwhm(5), name='Film in D2O')
    project.models = ModelCollection([reference])
    project.add_contrast(0, 'Film in H2O', [ReplaceMaterial(old=d2o, new=h2o)])
    project.add_contrast(0, 'Film in CMSi', [ReplaceMaterial(old=d2o, new=cmsi)])
    project.current_model_index = 0
    project.load_all_experiments_from_file(DATASETS / 'film_contrasts.ort')
    pair_experiments(project, {'D2O': 0, 'H2O': 1, 'CMSi': 2})

    fix_all(project)
    free(oxide.thickness, 5, 40)
    free(film_layer.thickness, 50, 120)
    free(film.sld, -0.5, 4)
    free(film_layer.roughness, 1, 10)
    # Backgrounds stay fixed at their known values: freeing all three lets the fit wander into
    # a local minimum (see examples/datasets/README.md, dataset 5).
    for model, background in zip(project.models, (2e-7, 5e-6, 1e-6)):
        model.background.value = background
        free(model.scale, 0.5, 1.5)
    return project


def two_layer_film_constraints() -> Project:
    project = new_project(
        'Two-layer film with a thickness budget',
        'Simulated: two films on silicon whose total thickness is known to be 90 A, '
        'kept by inequality constraints during the fit.',
    )
    air = Material(sld=0, isld=0, name='Air')
    film_a = slab(Material(sld=3.0, isld=0, name='MatA'), 30, 3, 'Film A')
    film_b = slab(Material(sld=5.0, isld=0, name='MatB'), 50, 3, 'Film B')
    subphase = slab(Material(sld=2.07, isld=0, name='Si'), 0, 2, 'Si')
    sample = Sample(
        Multilayer(slab(air, 0, 0, 'Air'), name='Superphase'),
        Multilayer(film_a, name='Film A'),
        Multilayer(film_b, name='Film B'),
        Multilayer(subphase, name='Subphase'),
    )
    model = Model(sample=sample, scale=1, background=1e-7, resolution_function=PercentageFwhm(5), name='Two-layer film')
    project.models = ModelCollection([model])
    project.load_new_experiment(DATASETS / 'two_layer_film.ort')

    fix_all(project)
    free(film_a.thickness, 10, 80)
    free(film_b.thickness, 10, 80)
    a_path = project.parameter_path(film_a.thickness)
    b_path = project.parameter_path(film_b.thickness)
    project.add_inequality_constraint(
        InequalitySpec('a', '<=', 'b', lhs_paths={'a': a_path}, rhs_paths={'b': b_path}, name='Film A is the thinner')
    )
    project.add_inequality_constraint(
        InequalitySpec('a + b', '<=', '90', lhs_paths={'a': a_path, 'b': b_path}, name='Total thickness at most 90 A')
    )
    # BUMPS honours inequality constraints; the app's default Bumps_lm only weakly.
    project.fit_settings.minimizer = Minimizers.Bumps_simplex
    return project


def fe_on_si_polarized() -> Project:
    project = new_project(
        'Magnetic iron film, polarized',
        'Simulated: an Fe film on silicon with a canted moment, all four spin channels fitted at once (Refl1D).',
    )
    vacuum = Material(sld=0, isld=0, name='Vacuum')
    iron = Material(sld=8.02, isld=0, name='Fe')
    silicon = Material(sld=2.07, isld=0, name='Si')
    film = Layer(
        material=iron,
        thickness=180,
        roughness=5,
        magnetism=LayerMagnetism(rho_m=3.0, theta_m=60.0, name='Fe moment'),
        name='Fe film',
    )
    sample = Sample(
        Multilayer(slab(vacuum, 0, 0, 'Vacuum'), name='Superphase'),
        Multilayer(film, name='Fe film'),
        Multilayer(slab(silicon, 0, 3, 'Si'), name='Subphase'),
    )
    model = Model(sample=sample, scale=1, background=1e-7, resolution_function=PercentageFwhm(5), name='Fe on Si')
    # Magnetism needs Refl1D; switched before the model is added, so the model is bound to it.
    project.calculator = 'refl1d'
    project.models = ModelCollection([model])
    directory = DATASETS / 'polarized'
    suffixes = {'pp': 'uu', 'pm': 'ud', 'mp': 'du', 'mm': 'dd'}
    project.load_polarized_experiment(
        {channel: directory / f'fe_on_si_{suffix}.dat' for channel, suffix in suffixes.items()}, model_index=0
    )

    fix_all(project)
    free(film.thickness, 150, 250)
    free(film.magnetism.rho_m, 0, 8)
    free(film.magnetism.theta_m, 0, 90)
    return project


#: (directory name, builder, the short line listed under the name), in the order the app lists
#: them. The line fits the sidebar; the project's own description says more.
EXAMPLES: list[tuple[str, Callable[[], Project], str]] = [
    ('PolymerFilm', polymer_film, 'neutrons, solid/liquid, slab model, Platypus@ANSTO'),
    ('DspcMonolayer', dspc_monolayer, 'neutrons, air/liquid, surfactant layer, SURF@ISIS'),
    ('NiTiMultilayer', ni_ti_multilayer, 'neutrons, repeating multilayer, simulated'),
    ('FilmContrasts', film_contrasts, 'neutrons, three contrasts fitted jointly, simulated'),
    ('DspcContrasts', dspc_contrasts, 'neutrons, three contrasts fitted jointly, SURF@ISIS'),
    ('TwoLayerFilmConstraints', two_layer_film_constraints, 'neutrons, inequality constraints, simulated'),
    ('FePolarized', fe_on_si_polarized, 'polarized neutrons, magnetic film, simulated'),
]


def main() -> None:
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    OUTPUT.mkdir(parents=True)
    index = []
    for directory, build, summary in EXAMPLES:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', DeprecationWarning)
            project = build()
        # Projects are written as <parent>/<name>/project.json; the directory is the name here.
        project_dict = project.as_dict()
        target = OUTPUT / directory / 'project.json'
        target.parent.mkdir()
        target.write_text(json.dumps(project_dict, indent=4), encoding='utf-8')
        index.append(
            {
                'path': f'{directory}/project.json',
                'name': project._info['name'],
                'description': summary,
            }
        )
        print(f'{target.relative_to(ROOT)}: {len(project.models)} model(s), {len(project.experiments)} experiment(s)')
    (OUTPUT / 'index.json').write_text(json.dumps(index, indent=4) + '\n', encoding='utf-8')
    global_object.registry.clear()


if __name__ == '__main__':
    main()
