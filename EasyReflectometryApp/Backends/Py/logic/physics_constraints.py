# SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
# SPDX-License-Identifier: BSD-3-Clause
# © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

"""Physics-constraint recipes: one-click groups of parameter dependencies.

The library already knows how to tie parameters according to physics —
conformal roughness/thickness across an assembly, equal head/tail area per
molecule, bilayer head coupling, solvent roughness following a surfactant —
and, with derived parameters, a constant multilayer period. This module turns
those into a declarative list of *recipes* per assembly of the current model,
so the GUI can render toggles without knowing any library API, and reports
which underlying parameters each active recipe owns so the constraints list
can show one row per recipe instead of N cryptic ties.

Every recipe is detected from the parameter graph (not from remembered
state), so recipes applied in a script or restored from a project file show
as active too.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any
from typing import Callable
from typing import Optional

from easyreflectometry import Project as ProjectLib
from easyreflectometry.constraints import clamp_sum_partners
from easyreflectometry.constraints import constrain_to_sum
from easyreflectometry.constraints import is_constrained_to_sum
from easyreflectometry.constraints import restore_sum_partners
from easyreflectometry.constraints import unconstrain
from easyreflectometry.sample import BaseAssembly
from easyreflectometry.sample import Bilayer
from easyreflectometry.sample import GradientLayer
from easyreflectometry.sample import MaterialMixture
from easyreflectometry.sample import MaterialSolvated
from easyreflectometry.sample import Multilayer
from easyreflectometry.sample import RepeatingMultilayer
from easyreflectometry.sample import SurfactantLayer
from easyreflectometry.sample.assemblies.base_assembly import follows_equal
from easyscience.variable import Parameter

logger = logging.getLogger(__name__)


def _follows(follower: Parameter, leader: Parameter) -> bool:
    """Exact ``follower = leader`` tie (the conformal / equal-parameter idiom)."""
    return follows_equal(follower, leader)


def _layers(assembly: BaseAssembly) -> list:
    return list(assembly.layers)


@dataclass
class Recipe:
    id: str
    title: str
    description: str
    applies_to: Callable[[BaseAssembly], bool]
    available: Callable[[BaseAssembly, Any], tuple[bool, str]]
    active: Callable[[BaseAssembly, Any], bool]
    owned: Callable[[BaseAssembly, Any], list[Parameter]]
    apply: Optional[Callable[[BaseAssembly, Any], None]]
    remove: Optional[Callable[[BaseAssembly, Any], None]]
    toggleable: bool = True
    requires: tuple[str, ...] = ()


# --------------------------------------------------------------------------- conformal roughness


def _conformal_roughness_available(assembly, ctx):
    if isinstance(assembly, GradientLayer):
        return True, 'Always on for a gradient layer.'
    if len(_layers(assembly)) < 2:
        return False, 'Needs an assembly with at least two layers.'
    return True, ''


def _conformal_roughness_owned(assembly, ctx):
    layers = _layers(assembly)
    if len(layers) < 2:
        return []
    leader = layers[0].roughness
    return [layer.roughness for layer in layers[1:] if _follows(layer.roughness, leader)]


def _conformal_roughness_active(assembly, ctx):
    layers = _layers(assembly)
    if len(layers) < 2:
        return False
    if isinstance(assembly, GradientLayer):
        return True
    return bool(assembly.conformal_roughness)


def _set_conformal_roughness(status):
    def _set(assembly, ctx):
        # Every assembly persists this itself: SurfactantLayer/Bilayer always
        # did, Multilayer/RepeatingMultilayer serialize the flag since the
        # `improved_constraints` lib branch.
        assembly.conformal_roughness = status

    return _set


# --------------------------------------------------------------------------- conformal thickness


def _conformal_thickness_available(assembly, ctx):
    if isinstance(assembly, GradientLayer):
        return True, 'Always on for a gradient layer.'
    if len(_layers(assembly)) < 2:
        return False, 'Needs an assembly with at least two layers.'
    return True, ''


def _conformal_thickness_owned(assembly, ctx):
    layers = _layers(assembly)
    if len(layers) < 2:
        return []
    leader = layers[0].thickness
    return [layer.thickness for layer in layers[1:] if _follows(layer.thickness, leader)]


def _conformal_thickness_active(assembly, ctx):
    if isinstance(assembly, GradientLayer):
        return True
    return bool(assembly.conformal_thickness)


def _set_conformal_thickness(status):
    def _set(assembly, ctx):
        assembly.conformal_thickness = status  # persisted by the assembly itself

    return _set


# --------------------------------------------------------------------------- surfactant APM


def _apm_owned(assembly, ctx):
    head = assembly.head_layer.area_per_molecule_parameter
    return [head] if _follows(head, assembly.tail_layer.area_per_molecule_parameter) else []


# --------------------------------------------------------------------------- bilayer heads


def _heads_owned(assembly, ctx):
    owned = []
    front, back = assembly.front_head_layer, assembly.back_head_layer
    for name in ('thickness', 'area_per_molecule_parameter'):
        follower = getattr(back, name, None)
        leader = getattr(front, name, None)
        if follower is not None and leader is not None and _follows(follower, leader):
            owned.append(follower)
    return owned


# --------------------------------------------------------------------------- solvent roughness


def _solvent_parameter(assembly, ctx) -> Optional[Parameter]:
    """Roughness of the layer right after the surfactant (its solvent side)."""
    sample = ctx['sample']
    for index, candidate in enumerate(sample):
        if candidate is assembly:
            if index + 1 < len(sample) and len(_layers(sample[index + 1])):
                return _layers(sample[index + 1])[0].roughness
            return None
    return None


def _solvent_roughness_available(assembly, ctx):
    if not assembly.conformal_roughness:
        return False, 'Requires conformal roughness on the surfactant layer.'
    if _solvent_parameter(assembly, ctx) is None:
        return False, 'There is no layer below the surfactant to act as solvent.'
    return True, ''


def _solvent_roughness_owned(assembly, ctx):
    solvent = _solvent_parameter(assembly, ctx)
    if solvent is not None and _follows(solvent, assembly.tail_layer.roughness):
        return [solvent]
    return []


def _solvent_roughness_apply(assembly, ctx):
    solvent = _solvent_parameter(assembly, ctx)
    if solvent is None:
        raise ValueError('There is no layer below the surfactant to act as solvent.')
    assembly.constrain_solvent_roughness(solvent)


def _solvent_roughness_remove(assembly, ctx):
    solvent = _solvent_parameter(assembly, ctx)
    if solvent is not None:
        unconstrain(solvent)


# --------------------------------------------------------------------------- constant period


def _period_available(assembly, ctx):
    if len(_layers(assembly)) < 2:
        return False, 'Needs at least two layers whose thicknesses form a period.'
    if assembly.conformal_thickness:
        return False, 'Not compatible with conformal thickness.'
    return True, ''


def _period_owned(assembly, ctx):
    layers = _layers(assembly)
    if len(layers) < 2:
        return []
    last = layers[-1].thickness
    thicknesses = [layer.thickness for layer in layers]
    return [last] if is_constrained_to_sum(last, thicknesses) else []


def _period_apply(assembly, ctx):
    layers = _layers(assembly)
    thicknesses = [layer.thickness for layer in layers]
    constrain_to_sum(thicknesses[-1], thicknesses)  # the last layer absorbs the remainder
    # On its own the constraint lets a fit push the free layers past the
    # period and drive the remainder to a negative thickness; the lib caps
    # the free maxima (and, with the project, persists the originals).
    clamp_sum_partners(thicknesses[:-1], float(thicknesses[-1].value))


def _period_remove(assembly, ctx):
    layers = _layers(assembly)
    unconstrain(layers[-1].thickness)
    restore_sum_partners([layer.thickness for layer in layers[:-1]])


# --------------------------------------------------------------------------- mixtures (informational)


def _mixture_layers(assembly, ctx):
    return [layer for layer in _layers(assembly) if isinstance(layer.material, (MaterialMixture, MaterialSolvated))]


def _mixture_available(assembly, ctx):
    if _mixture_layers(assembly, ctx):
        return True, ''
    return False, 'No layer of this assembly uses a material mixture or solvated material.'


RECIPES: list[Recipe] = [
    Recipe(
        id='conformal_roughness',
        title='Conformal roughness',
        description='Every interface of the assembly shares the roughness of its first layer.',
        applies_to=lambda a: isinstance(a, (Multilayer, RepeatingMultilayer, GradientLayer, SurfactantLayer, Bilayer)),
        available=_conformal_roughness_available,
        active=_conformal_roughness_active,
        owned=_conformal_roughness_owned,
        apply=_set_conformal_roughness(True),
        remove=_set_conformal_roughness(False),
    ),
    Recipe(
        id='conformal_thickness',
        title='Conformal thickness',
        description='Every layer of the assembly shares the thickness of its first layer.',
        applies_to=lambda a: isinstance(a, (Multilayer, RepeatingMultilayer, GradientLayer))
        and not isinstance(a, (SurfactantLayer, Bilayer)),
        available=_conformal_thickness_available,
        active=_conformal_thickness_active,
        owned=_conformal_thickness_owned,
        apply=_set_conformal_thickness(True),
        remove=_set_conformal_thickness(False),
    ),
    Recipe(
        id='equal_apm',
        title='Equal head/tail area per molecule',
        description='The head layer takes the area per molecule of the tail layer.',
        applies_to=lambda a: isinstance(a, SurfactantLayer),
        available=lambda a, c: (True, ''),
        active=lambda a, c: bool(a.constrain_area_per_molecule),
        owned=_apm_owned,
        apply=lambda a, c: setattr(a, 'constrain_area_per_molecule', True),
        remove=lambda a, c: setattr(a, 'constrain_area_per_molecule', False),
    ),
    Recipe(
        id='bilayer_heads',
        title='Symmetric head groups',
        description='The back head layer follows the front head layer thickness and area per molecule.',
        applies_to=lambda a: isinstance(a, Bilayer),
        available=lambda a, c: (True, ''),
        active=lambda a, c: bool(a.constrain_heads),
        owned=_heads_owned,
        apply=lambda a, c: setattr(a, 'constrain_heads', True),
        remove=lambda a, c: setattr(a, 'constrain_heads', False),
    ),
    Recipe(
        id='solvent_roughness',
        title='Solvent roughness follows the surfactant',
        description='The roughness of the first layer of the assembly below the surfactant follows the tail roughness.',
        applies_to=lambda a: isinstance(a, SurfactantLayer),
        available=_solvent_roughness_available,
        active=lambda a, c: bool(_solvent_roughness_owned(a, c)),
        owned=_solvent_roughness_owned,
        apply=_solvent_roughness_apply,
        remove=_solvent_roughness_remove,
        requires=('conformal_roughness',),
    ),
    Recipe(
        id='constant_period',
        title='Constant period Λ',
        description='The summed thickness of the layers stays constant: the last layer absorbs '
        'whatever the others change by.',
        applies_to=lambda a: isinstance(a, (Multilayer, RepeatingMultilayer))
        and not isinstance(a, (SurfactantLayer, Bilayer, GradientLayer)),
        available=_period_available,
        active=lambda a, c: bool(_period_owned(a, c)),
        owned=_period_owned,
        apply=_period_apply,
        remove=_period_remove,
    ),
    Recipe(
        id='mixture_fractions',
        title='Mixture fractions sum to 1',
        description='Material mixtures and solvated materials keep their fractions normalised internally.',
        applies_to=lambda a: True,
        available=_mixture_available,
        active=lambda a, c: bool(_mixture_layers(a, c)),
        owned=lambda a, c: [],
        apply=None,
        remove=None,
        toggleable=False,
    ),
]

RECIPES_BY_ID = {recipe.id: recipe for recipe in RECIPES}


class PhysicsConstraints:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib

    # ----- helpers -----

    @property
    def _sample(self):
        models = self._project_lib.models
        if not len(models):
            return None
        return models[self._project_lib.current_model_index].sample

    def _context(self):
        return {'sample': self._sample}

    def _assembly(self, index: int) -> BaseAssembly:
        sample = self._sample
        if sample is None or not 0 <= index < len(sample):
            raise IndexError(f'No assembly at index {index}.')
        return sample[index]

    # ----- API -----

    def recipes(self) -> list[dict[str, Any]]:
        """Declarative recipe list for every assembly of the current model."""
        sample = self._sample
        if sample is None:
            return []
        ctx = self._context()
        rows = []
        for assembly_index, assembly in enumerate(sample):
            for recipe in RECIPES:
                if not recipe.applies_to(assembly):
                    continue
                try:
                    available, reason = recipe.available(assembly, ctx)
                    # Report the graph truth even for unavailable recipes: a tie
                    # left behind by a script must not be hidden as "inactive".
                    active = bool(recipe.active(assembly, ctx))
                except Exception as error:  # noqa: BLE001 - a broken model must not hide the panel
                    logger.debug('Recipe %s unavailable for %s: %s', recipe.id, assembly.name, error)
                    available, reason, active = False, str(error), False
                toggleable = recipe.toggleable and not isinstance(assembly, GradientLayer)
                rows.append(
                    {
                        'id': recipe.id,
                        'assemblyIndex': assembly_index,
                        'assemblyName': assembly.name,
                        'assemblyType': assembly.type,
                        'title': recipe.title,
                        'description': recipe.description,
                        'available': bool(available),
                        'active': bool(active),
                        'toggleable': bool(toggleable and available),
                        'reason': reason,
                        'requires': list(recipe.requires),
                    }
                )
        return rows

    def apply(self, assembly_index: int, recipe_id: str) -> bool:
        recipe = RECIPES_BY_ID[recipe_id]
        assembly = self._assembly(assembly_index)
        ctx = self._context()
        if recipe.apply is None:
            return False
        available, reason = recipe.available(assembly, ctx)
        if not available:
            raise ValueError(reason or f"'{recipe.title}' is not available for {assembly.name}.")
        if recipe.active(assembly, ctx):
            return False
        recipe.apply(assembly, ctx)
        return True

    def remove(self, assembly_index: int, recipe_id: str) -> bool:
        recipe = RECIPES_BY_ID[recipe_id]
        assembly = self._assembly(assembly_index)
        ctx = self._context()
        if recipe.remove is None or isinstance(assembly, GradientLayer):
            return False
        if not recipe.active(assembly, ctx):
            return False
        # Dependents first: e.g. solvent roughness needs conformal roughness.
        for other in RECIPES:
            if recipe.id in other.requires and other.applies_to(assembly) and other.active(assembly, ctx):
                other.remove(assembly, ctx)
        recipe.remove(assembly, ctx)
        return True

    def owned_parameters(self) -> dict[str, dict[str, Any]]:
        """``unique_name -> group info`` for every parameter an active recipe owns in the current model."""
        sample = self._sample
        if sample is None:
            return {}
        ctx = self._context()
        owned: dict[str, dict[str, Any]] = {}
        for assembly_index, assembly in enumerate(sample):
            for recipe in RECIPES:
                if not recipe.applies_to(assembly):
                    continue
                try:
                    parameters = recipe.owned(assembly, ctx)
                except Exception:  # noqa: BLE001
                    continue
                for parameter in parameters:
                    owned.setdefault(
                        parameter.unique_name,
                        {
                            'recipeId': recipe.id,
                            'title': recipe.title,
                            'assemblyIndex': assembly_index,
                            'assemblyName': assembly.name,
                            'count': len(parameters),
                        },
                    )
        return owned
