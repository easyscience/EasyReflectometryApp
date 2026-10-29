import logging
from typing import Optional
from typing import Union

from easyreflectometry import Project as ProjectLib
from easyreflectometry.sample import LayerAreaPerMolecule
from easyreflectometry.sample import LayerCollection
from easyreflectometry.sample import LayerMagnetism
from easyreflectometry.sample import Material
from easyreflectometry.sample import Sample
from easyreflectometry.sample.elements.layers.layer_magnetism import DEFAULTS as MAGNETISM_DEFAULTS

from .structure import guide_field_reference
from .structure import magnetic_vector_for_layer

logger = logging.getLogger(__name__)

# Shown in the magnetism fields of a layer that is not magnetic (yet): the
# values attaching magnetism would start from. Taken from the library so the
# preview cannot drift away from what `LayerMagnetism()` actually creates.
_DEFAULT_RHO_M = MAGNETISM_DEFAULTS['rho_m']['value']
_DEFAULT_THETA_M = MAGNETISM_DEFAULTS['theta_m']['value']


class Layers:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib

    def _has_valid_layer_index(self, index: int) -> bool:
        return 0 <= index < len(self._layers)

    def _has_valid_material_index(self, index: int) -> bool:
        return 0 <= index < len(self._project_lib._materials)

    @property
    def _sample(self) -> Sample:
        return self._project_lib._models[self._project_lib.current_model_index].sample

    @property
    def _layers(self) -> LayerCollection:
        return self._sample[self._project_lib.current_assembly_index].layers

    @property
    def index(self) -> int:
        return self._project_lib.current_layer_index

    @index.setter
    def index(self, new_value: Union[int, str]) -> None:
        self._project_lib.current_layer_index = int(new_value)

    @property
    def name_at_current_index(self) -> str:
        return self._layers[self.index].name

    @property
    def layers(self) -> list[dict[str, str]]:
        return _from_layers_collection_to_list_of_dicts(self._layers)

    @property
    def layers_names(self) -> list[str]:
        return [element['label'] for element in self.layers]

    def remove_at_index(self, index: int) -> None:
        self._layers.remove_at(index)
        # A removed coupled layer can leave its material's moment, or the
        # model's field, acting on nothing; the project fixes those.
        self._project_lib._sync_parameter_states()

    def add_new(self) -> None:
        if 'Si' not in [material.name for material in self._project_lib._materials]:
            self._project_lib._materials.add_material(Material(name='Si', sld=2.07, isld=0.0))
        index_si = [material.name for material in self._project_lib._materials].index('Si')
        self._layers.add_layer()
        self._layers[-1].material = self._project_lib._materials[index_si]
        # Set layer name based on material name
        self._layers[-1].name = self._project_lib._materials[index_si].name + ' Layer'

    def duplicate_selected(self) -> None:
        self._layers.duplicate_layer(self.index)

    def move_selected_up(self) -> None:
        if self.index > 0:
            self._layers.move_up(self.index)
            self.index = self.index - 1

    def move_selected_down(self) -> None:
        if self.index < len(self._layers) - 1:
            self._layers.move_down(self.index)
            self.index = self.index + 1

    def set_name_at_current_index(self, new_value: str) -> bool:
        if self._layers[self.index].name != new_value:
            self._layers[self.index].name = new_value
            return True
        return False

    def set_name_at_index(self, index: int, new_value: str) -> bool:
        if not self._has_valid_layer_index(index):
            return False
        if self._layers[index].name != new_value:
            self._layers[index].name = new_value
            return True
        return False

    def set_thickness_at_current_index(self, new_value: float) -> bool:
        if self._layers[self.index].thickness.value != new_value:
            self._layers[self.index].thickness.value = new_value
            return True
        return False

    def set_thickness_at_index(self, index: int, new_value: float) -> bool:
        if not self._has_valid_layer_index(index):
            return False
        if self._layers[index].thickness.value != new_value:
            self._layers[index].thickness.value = new_value
            return True
        return False

    def set_roughness_at_current_index(self, new_value: float) -> bool:
        if self._layers[self.index].roughness.value != new_value:
            self._layers[self.index].roughness.value = new_value
            return True
        return False

    def set_roughness_at_index(self, index: int, new_value: float) -> bool:
        if not self._has_valid_layer_index(index):
            return False
        if self._layers[index].roughness.value != new_value:
            self._layers[index].roughness.value = new_value
            return True
        return False

    def set_material_at_current_index(self, new_value: int) -> bool:
        if self._layers[self.index].material != self._project_lib._materials[new_value]:
            self._layers[self.index].material = self._project_lib._materials[new_value]
            # Update layer name based on material name
            self._layers[self.index].name = self._project_lib._materials[new_value].name + ' Layer'
            # A new material can end the layer's rho_m coupling.
            self._project_lib._sync_parameter_states()
            return True
        return False

    def set_material_at_index(self, index: int, new_value: int) -> bool:
        if not self._has_valid_layer_index(index) or not self._has_valid_material_index(new_value):
            return False
        if self._layers[index].material != self._project_lib._materials[new_value]:
            self._layers[index].material = self._project_lib._materials[new_value]
            self._layers[index].name = self._project_lib._materials[new_value].name + ' Layer'
            # A new material can end the layer's rho_m coupling.
            self._project_lib._sync_parameter_states()
            return True
        return False

    def set_solvent_at_current_index(self, new_value: int) -> bool:
        if self._layers[self.index].solvent != self._project_lib._materials[new_value]:
            self._layers[self.index].solvent = self._project_lib._materials[new_value]
            return True
        return False

    def set_solvent_at_index(self, index: int, new_value: int) -> bool:
        if not self._has_valid_layer_index(index) or not self._has_valid_material_index(new_value):
            return False
        if self._layers[index].solvent != self._project_lib._materials[new_value]:
            self._layers[index].solvent = self._project_lib._materials[new_value]
            return True
        return False

    def set_apm_at_current_index(self, new_value: float) -> bool:
        if self._layers[self.index].area_per_molecule != new_value:
            self._layers[self.index].area_per_molecule = new_value
            return True
        return False

    def set_apm_at_index(self, index: int, new_value: float) -> bool:
        if not self._has_valid_layer_index(index):
            return False
        if self._layers[index].area_per_molecule != new_value:
            self._layers[index].area_per_molecule = new_value
            return True
        return False

    def set_solvation_at_current_index(self, new_value: float) -> bool:
        if self._layers[self.index].solvent_fraction != new_value:
            self._layers[self.index].solvent_fraction = new_value
            return True
        return False

    def set_solvation_at_index(self, index: int, new_value: float) -> bool:
        if not self._has_valid_layer_index(index):
            return False
        if self._layers[index].solvent_fraction != new_value:
            self._layers[index].solvent_fraction = new_value
            return True
        return False

    def set_formula(self, new_value: str) -> bool:
        if self._layers[self.index].molecular_formula != new_value:
            self._layers[self.index].molecular_formula = new_value
            return True
        return False

    def set_formula_at_index(self, index: int, new_value: str) -> bool:
        if not self._has_valid_layer_index(index):
            return False
        if self._layers[index].molecular_formula != new_value:
            self._layers[index].molecular_formula = new_value
            return True
        return False

    # # #
    # Magnetism
    # # #

    @property
    def magnetism_supported(self) -> bool:
        """Whether the active calculator can model magnetic layers (refl1d only)."""
        return bool(self._project_lib.calculator_supports_magnetism)

    @property
    def magnetism(self) -> list[dict[str, str]]:
        """One row per layer of the current assembly, describing its magnetism.

        ``magnetic`` is 'True'/'False'; ``rho_m``/``theta_m`` carry the defaults
        of a fresh :class:`LayerMagnetism` for non-magnetic layers so the fields
        show what attaching magnetism would start from. ``phi`` is the direction
        the moment points, in degrees from the guide field - what the compass
        draws - and ``editable`` whether that direction can be set by dragging
        it (a constrained ``theta_m`` follows its expression, not the pointer).
        Both are empty for a non-magnetic layer, which has no direction.
        ``material_magnetic`` says whether the layer's material carries a
        moment (a ``MaterialMagnetic``), and ``rho_m_coupled`` whether the
        layer takes ``rho_m`` from it.
        """
        rows = []
        for layer in self._layers:
            magnetism = getattr(layer, 'magnetism', None)
            rows.append(
                {
                    'label': layer.name,
                    'magnetic': str(magnetism is not None),
                    'rho_m': str(magnetism.rho_m.value if magnetism is not None else _DEFAULT_RHO_M),
                    'theta_m': str(magnetism.theta_m.value if magnetism is not None else _DEFAULT_THETA_M),
                    'phi': '' if magnetism is None else str(magnetic_vector_for_layer(magnetism)['phi']),
                    'editable': '' if magnetism is None else str(magnetism.theta_m.independent),
                    'material_magnetic': str(getattr(layer.material, 'rho_m', None) is not None),
                    'rho_m_coupled': str(layer.rho_m_coupled),
                }
            )
        return rows

    def set_magnetic_at_index(self, index: int, new_value: bool) -> bool:
        """Attach or remove :class:`LayerMagnetism` on one layer.

        Attaching turns calculator magnetism on; removing the last magnetic
        layer turns it off again (both handled by the library).
        """
        if not self._has_valid_layer_index(index):
            return False
        layer = self._layers[index]
        is_magnetic = getattr(layer, 'magnetism', None) is not None
        if bool(new_value) == is_magnetic:
            return False
        if new_value and not self.magnetism_supported:
            engines = ', '.join(self._project_lib.calculators_supporting_magnetism) or 'none of the available engines'
            raise NotImplementedError(
                f'The {self._project_lib.calculator} calculation engine cannot model magnetic layers; '
                f'magnetism needs {engines}.'
            )
        layer.magnetism = LayerMagnetism() if new_value else None
        if new_value:
            self._ensure_calculator_magnetism()
        # Bring fresh parameters under the project's limit/enablement policy,
        # exactly as a newly created layer would be; the model's field
        # parameters follow whether the model is magnetic.
        self._project_lib._sync_parameter_states()
        return True

    def set_rho_m_coupled_at_index(self, index: int, coupled: bool) -> bool:
        """Take the layer's ``rho_m`` from its magnetic material, or stop doing so."""
        if not self._has_valid_layer_index(index):
            return False
        layer = self._layers[index]
        if layer.magnetism is None or layer.rho_m_coupled == bool(coupled):
            return False
        try:
            layer.rho_m_coupled = bool(coupled)
        except ValueError:
            logger.warning('Layer %r has no magnetic material to take rho_m from', layer.name)
            return False
        self._project_lib._sync_parameter_states()
        return True

    def _current_model(self):
        """The current model, or None when there is none to show."""
        models = self._project_lib._models
        index = self._project_lib.current_model_index
        if models is None or index is None or not 0 <= index < len(models):
            return None
        return models[index]

    @property
    def field(self) -> dict:
        """The current model's guide field angle (degrees) and applied field
        (tesla), with where its reference arrow points (:func:`guide_field_reference`),
        and ``model_magnetic``: whether the field acts on the model at all.
        The defaults when there is no current model."""
        model = self._current_model()
        if model is None:
            return {**DEFAULT_FIELD}
        guide_field_angle = float(model.guide_field_angle.value)
        return {
            'guide_field_angle': guide_field_angle,
            'applied_field': float(model.applied_field.value),
            'model_magnetic': bool(model.has_magnetism),
            **guide_field_reference(guide_field_angle),
        }

    def set_field(self, name: str, new_value: float) -> bool:
        """Set ``guide_field_angle`` or ``applied_field`` of the current model."""
        model = self._current_model()
        if model is None:
            return False
        return _set_parameter_value(getattr(model, name), new_value)

    def _ensure_calculator_magnetism(self) -> None:
        """Make sure attaching magnetism actually reached the calculator.

        `Layer.magnetism` can only switch magnetism on through its own
        interface, which is None for a layer that was never bound (a sample
        assigned wholesale rather than edited in place). The calculator would
        then still be unpolarized and every spin channel would fail to
        calculate, so re-propagate the model's interface over the sample tree.
        """
        model = self._project_lib._models[self._project_lib.current_model_index]
        interface = getattr(model, 'interface', None)
        if interface is None or interface().include_magnetism:
            return
        logger.debug('Re-propagating the calculator interface to bind new magnetism')
        model.interface = interface

    def set_rho_m_at_index(self, index: int, new_value: float) -> bool:
        return self._set_magnetism_value_at_index(index, 'rho_m', new_value)

    def set_theta_m_at_index(self, index: int, new_value: float) -> bool:
        return self._set_magnetism_value_at_index(index, 'theta_m', new_value)

    def _set_magnetism_value_at_index(self, index: int, attribute: str, new_value: float) -> bool:
        """Set one magnetic parameter, ignoring edits to a non-magnetic layer."""
        magnetism = self.magnetism_at_index(index)
        if magnetism is None:
            return False
        return _set_parameter_value(getattr(magnetism, attribute), new_value)

    def magnetism_at_index(self, index: int) -> Optional[LayerMagnetism]:
        """The layer's magnetism, or None when the layer is not magnetic/valid."""
        if not self._has_valid_layer_index(index):
            return None
        return getattr(self._layers[index], 'magnetism', None)


# What `Layers.field` reports without a current model: refl1d's defaults.
DEFAULT_FIELD = {'guide_field_angle': 270.0, 'applied_field': 0.0, 'model_magnetic': False, 'in_plane': True, 'phi': 0.0}


def _set_parameter_value(parameter, new_value) -> bool:
    """Set a parameter from an edit; False for no change, bad input or a
    dependent parameter (a coupled rho_m follows its material)."""
    if not parameter.independent:
        return False
    try:
        value = float(new_value)
    except (TypeError, ValueError):
        return False
    if parameter.value == value:
        return False
    try:
        parameter.value = value
    except (ValueError, TypeError):
        logger.exception('Failed to set %s to %s', parameter.name, value)
        return False
    return True


def _from_layers_collection_to_list_of_dicts(layers_collection: LayerCollection) -> list[dict[str, str]]:
    """Convert layers collection to list of dicts.

    Editability of thickness and roughness mirrors each parameter's ``enabled``
    flag, which ``Project._update_enablement_of_fixed_layers_for_model`` keeps
    in step with the superphase (first layer of the first assembly) and the
    subphase (last layer of the last assembly). Reading the flag rather than
    re-deriving it from the assembly position keeps the table and the
    parameters in agreement (issue #329).

    :param layers_collection: The collection of layers.
    """
    layers_list = []
    for layer in layers_collection:
        layers_list.append(
            {
                'label': layer.name,
                'roughness': str(layer.roughness.value),
                'thickness': str(layer.thickness.value),
                'material': layer.material.name,
                'formula': 'formula',
                'apm': '0.1',
                'solvent': 'solvent',
                'solvation': '0.2',
                'apm_enabled': 'True',
                # `enabled` is set on a parameter only once enablement has run
                # over it; until then it counts as enabled, as in the library.
                'thickness_enabled': str(bool(getattr(layer.thickness, 'enabled', True))),
                'roughness_enabled': str(bool(getattr(layer.roughness, 'enabled', True))),
            }
        )
        if isinstance(layer, LayerAreaPerMolecule):
            layers_list[-1]['formula'] = layer.molecular_formula
            layers_list[-1]['apm'] = str(layer.area_per_molecule)
            layers_list[-1]['solvent'] = layer.solvent.name
            layers_list[-1]['solvation'] = str(layer.solvent_fraction)

    return layers_list
