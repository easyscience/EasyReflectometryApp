"""Keep mixtures out of the materials palette with easyreflectometry releases that lack the fix.

The palette holds the materials a user picks for a layer, and the Material editor reads
``material.sld.value`` from each. Releases up to 2.0.0 put every layer's material in it,
including a surfactant layer's ``MaterialSolvated`` (a ``MaterialMixture``, whose SLD is
computed from its constituents). One of those breaks the Material editor: QML shows only
``BackendWrapper.qml: Error: <NULL>``. It happens after Add contrast or loading a model with
a surfactant layer, and on loading a project file saved in that state. The in-use check run
before a material is removed also looks at the mixture, so it misses the surfactant's solvent.

The library fixes this in ``easyreflectometry.project`` (``_palette_materials``): a mixture
is replaced by its constituents, and an area-per-molecule layer adds only its solvent. Until
the app requires a release with that fix, :func:`install` adds the same behaviour to
``Project``. With a fixed library it changes nothing.

Remove this module (and its call in ``Backends/Py/__init__.py``) once the app requires
easyreflectometry 2.0.1 or newer: https://github.com/easyscience/EasyReflectometryApp/issues/387
"""

import functools

import easyreflectometry.project as _lib_project
from easyreflectometry import Project
from easyreflectometry.sample import LayerAreaPerMolecule
from easyreflectometry.sample import MaterialCollection
from easyreflectometry.sample import MaterialMixture

_installed = False


def lib_has_palette_fix() -> bool:
    """Whether the installed easyreflectometry keeps mixtures out of the palette itself."""
    return hasattr(_lib_project, '_palette_materials')


def palette_materials(layer) -> list:
    """The materials of `layer` that belong in the materials palette.

    A mixture is never a palette entry; its constituents are. An area-per-molecule layer
    builds its material from its own chemical formula; only its solvent is picked.
    """
    if isinstance(layer, LayerAreaPerMolecule):
        return [layer.solvent]
    return _constituents(layer.material)


def _constituents(material) -> list:
    if isinstance(material, MaterialMixture):
        return _constituents(material.material_a) + _constituents(material.material_b)
    return [material]


def _get_materials_from_model(self, model) -> MaterialCollection:
    """The palette materials of a single model's sample (see :func:`palette_materials`)."""
    materials_in_model = MaterialCollection(populate_if_none=False)
    for assembly in model.sample:
        for layer in assembly.layers:
            for material in palette_materials(layer):
                if material not in materials_in_model:
                    materials_in_model.append(material)
    return materials_in_model


def _get_materials_in_models(self) -> MaterialCollection:
    """The palette materials the project's models use (see :func:`palette_materials`)."""
    materials_in_model = MaterialCollection(populate_if_none=False)
    seen: set[int] = set()
    for model in self._models:
        for assembly in model.sample:
            for layer in assembly.layers:
                for material in palette_materials(layer):
                    if id(material) not in seen:  # one material in two layers, once
                        seen.add(id(material))
                        materials_in_model.append(material)
    return materials_in_model


def _wrap_from_dict(from_dict):
    @functools.wraps(from_dict)
    def wrapper(self, project_dict: dict):
        result = from_dict(self, project_dict)
        # A file saved with the palette in the broken state holds mixtures; their
        # constituents take their place, appended after the file's own entries.
        if any(isinstance(material, MaterialMixture) for material in self._materials):
            kept = [material for material in self._materials if not isinstance(material, MaterialMixture)]
            self._replace_collection(kept, self._materials)
            self._extend_palette_from_models()
        return result

    return wrapper


def install() -> bool:
    """Add the palette fix to ``Project`` unless the library has it. Returns whether it patched.

    Call it before the first ``Project`` is used; calling it again does nothing.
    """
    global _installed
    if _installed or lib_has_palette_fix():
        return False
    Project._get_materials_from_model = _get_materials_from_model
    Project._get_materials_in_models = _get_materials_in_models
    Project.from_dict = _wrap_from_dict(Project.from_dict)
    _installed = True
    return True
