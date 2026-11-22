"""The materials palette never holds a mixture, whichever easyreflectometry is installed.

With a library older than the palette fix these exercise ``lib_compat``'s patch; with a fixed
library they pin that the library and the patch agree. Either way they use the real library
objects (the DSPC examples have surfactant layers), not fakes.
"""

import pytest
from easyreflectometry import Project as ProjectLib
from easyreflectometry.sample import LayerAreaPerMolecule
from easyreflectometry.sample import MaterialMixture
from easyscience import global_object

from EasyReflectometryApp.Backends.Py import lib_compat
from EasyReflectometryApp.Backends.Py.logic.project import EXAMPLES_DIR


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.registry.clear()
    yield
    global_object.registry.clear()


def _load(example: str) -> ProjectLib:
    project = ProjectLib()
    project.load_from_json(EXAMPLES_DIR / example / 'project.json')
    return project


def _mixtures(project: ProjectLib) -> list:
    return [material for material in project._materials if isinstance(material, MaterialMixture)]


def _solvents(project: ProjectLib) -> list:
    return [
        layer.solvent
        for model in project.models
        for assembly in model.sample
        for layer in assembly.layers
        if isinstance(layer, LayerAreaPerMolecule)
    ]


def test_the_palette_fix_is_in_place():
    from easyreflectometry.project import Project

    assert lib_compat.lib_has_palette_fix() or Project._get_materials_in_models is lib_compat._get_materials_in_models
    assert lib_compat.install() is False  # already installed at import, or not needed


@pytest.mark.parametrize('example', ['DspcMonolayer', 'DspcContrasts'])
def test_add_contrast_of_a_surfactant_model_keeps_mixtures_out_of_the_palette(example):
    project = _load(example)

    project.add_contrast(0, 'extra')

    assert _mixtures(project) == []
    assert all(any(solvent is material for material in project._materials) for solvent in _solvents(project))


def test_a_surfactant_solvent_counts_as_in_use():
    project = _load('DspcMonolayer')
    in_use = project._get_materials_in_models()

    assert _solvents(project)
    assert all(any(solvent is material for material in in_use) for solvent in _solvents(project))
    assert not any(isinstance(material, MaterialMixture) for material in in_use)


def test_a_file_saved_with_a_mixture_in_the_palette_loads_without_it():
    project = _load('DspcMonolayer')
    mixture = next(
        layer.material
        for assembly in project.models[0].sample
        for layer in assembly.layers
        if isinstance(layer, LayerAreaPerMolecule)
    )
    project._materials.append(mixture)  # the palette as easyreflectometry 2.0.0 left it
    project_dict = project.as_dict()
    global_object.registry.clear()

    reloaded = ProjectLib()
    reloaded.from_dict(project_dict)

    assert _mixtures(reloaded) == []
    assert all(any(solvent is material for material in reloaded._materials) for solvent in _solvents(reloaded))


@pytest.mark.skipif(not lib_compat.lib_has_palette_fix(), reason='compares the patch with the fixed library')
def test_the_patch_matches_the_fixed_library():
    project = _load('DspcContrasts')

    assert [id(m) for m in lib_compat._get_materials_in_models(project)] == [id(m) for m in project._get_materials_in_models()]
    model = project.models[0]
    assert [id(m) for m in lib_compat._get_materials_from_model(project, model)] == [
        id(m) for m in project._get_materials_from_model(model)
    ]
