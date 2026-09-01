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
    def _assembly_type(self) -> str:
        """Determine if current assembly is superphase, subphase, or regular."""
        current_index = self._project_lib.current_assembly_index
        total_assemblies = len(self._sample)
        if current_index == 0:
            return 'superphase'
        elif current_index == total_assemblies - 1:
            return 'subphase'
        else:
            return 'regular'

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
        return _from_layers_collection_to_list_of_dicts(self._layers, self._assembly_type)

    @property
    def layers_names(self) -> list[str]:
        return [element['label'] for element in self.layers]

    def remove_at_index(self, value: str) -> None:
        self._layers.remove_at(int(value))

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
            return True
        return False

    def set_material_at_index(self, index: int, new_value: int) -> bool:
        if not self._has_valid_layer_index(index) or not self._has_valid_material_index(new_value):
            return False
        if self._layers[index].material != self._project_lib._materials[new_value]:
            self._layers[index].material = self._project_lib._materials[new_value]
            self._layers[index].name = self._project_lib._materials[new_value].name + ' Layer'
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
        show what attaching magnetism would start from.
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
            # Bring the fresh parameters under the project's limit/enablement
            # policy, exactly as a newly created layer would be.
            self._project_lib._sync_parameter_states()
        return True

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
        try:
            value = float(new_value)
        except (TypeError, ValueError):
            return False
        parameter = getattr(magnetism, attribute)
        if parameter.value == value:
            return False
        try:
            parameter.value = value
        except (ValueError, TypeError):
            logger.exception('Failed to set %s to %s', attribute, value)
            return False
        return True

    def magnetism_at_index(self, index: int) -> Optional[LayerMagnetism]:
        """The layer's magnetism, or None when the layer is not magnetic/valid."""
        if not self._has_valid_layer_index(index):
            return None
        return getattr(self._layers[index], 'magnetism', None)


def _from_layers_collection_to_list_of_dicts(
    layers_collection: LayerCollection, assembly_type: str = 'regular'
) -> list[dict[str, str]]:
    """Convert layers collection to list of dicts.

    :param layers_collection: The collection of layers.
    :param assembly_type: Type of assembly - 'superphase', 'subphase', or 'regular'.
        - superphase: Neither thickness nor roughness should be editable
        - subphase: Only roughness should be editable
        - regular: Both thickness and roughness should be editable
    """
    # Determine enabled states based on assembly type
    if assembly_type == 'superphase':
        thickness_enabled = 'False'
        roughness_enabled = 'False'
    elif assembly_type == 'subphase':
        thickness_enabled = 'False'
        roughness_enabled = 'True'
    else:  # regular
        thickness_enabled = 'True'
        roughness_enabled = 'True'

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
                'thickness_enabled': thickness_enabled,
                'roughness_enabled': roughness_enabled,
            }
        )
        if isinstance(layer, LayerAreaPerMolecule):
            layers_list[-1]['formula'] = layer.molecular_formula
            layers_list[-1]['apm'] = str(layer.area_per_molecule)
            layers_list[-1]['solvent'] = layer.solvent.name
            layers_list[-1]['solvation'] = str(layer.solvent_fraction)

    return layers_list
