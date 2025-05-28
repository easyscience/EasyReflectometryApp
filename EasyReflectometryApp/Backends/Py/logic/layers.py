from typing import Union

from easyreflectometry import Project as ProjectLib
from easyreflectometry.sample import LayerAreaPerMolecule
from easyreflectometry.sample import LayerCollection
from easyreflectometry.sample import Material


class Layers:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib

    @property
    def _layers(self) -> LayerCollection:
        return (
            self._project_lib._models[self._project_lib.current_model_index]
            .sample[self._project_lib.current_assembly_index]
            .layers
        )

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

    def remove_at_index(self, value: str) -> None:
        self._layers.remove(int(value))

    def add_new(self) -> None:
        if 'Si' not in [material.name for material in self._project_lib._materials]:
            self._project_lib._materials.add_material(Material(name='Si', sld=2.07, isld=0.0))
        index_si = [material.name for material in self._project_lib._materials].index('Si')
        self._layers.add_layer()
        self._layers[-1].material = self._project_lib._materials[index_si]

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

    def set_thickness_at_current_index(self, new_value: float) -> bool:
        if self._layers[self.index].thickness.value != new_value:
            self._layers[self.index].thickness.value = new_value
            return True
        return False

    def set_roughness_at_current_index(self, new_value: float) -> bool:
        if self._layers[self.index].roughness.value != new_value:
            self._layers[self.index].roughness.value = new_value
            return True
        return False

    def set_material_at_current_index(self, new_value: int) -> bool:
        if self._layers[self.index].material != self._project_lib._materials[new_value]:
            self._layers[self.index].material = self._project_lib._materials[new_value]
            return True
        return False

    def set_solvent_at_current_index(self, new_value: int) -> bool:
        if self._layers[self.index].solvent != self._project_lib._materials[new_value]:
            self._layers[self.index].solvent = self._project_lib._materials[new_value]
            return True
        return False

    def set_apm_at_current_index(self, new_value: float) -> bool:
        if self._layers[self.index].area_per_molecule != new_value:
            self._layers[self.index].area_per_molecule = new_value
            return True
        return False

    def set_solvation_at_current_index(self, new_value: float) -> bool:
        if self._layers[self.index].solvent_fraction != new_value:
            self._layers[self.index].solvent_fraction = new_value
            return True
        return False

    def set_formula(self, new_value: str) -> bool:
        if self._layers[self.index].molecular_formula != new_value:
            self._layers[self.index].molecular_formula = new_value
            return True
        return False


def _from_layers_collection_to_list_of_dicts(layers_collection: LayerCollection) -> list[dict[str, str]]:
    layers_list = []
    for layer in layers_collection:
        layers_list.append(
            {
                'label': layer.name,
                'roughness': str(layer.roughness.value),
                'roughness_enabled': str(layer.roughness.enabled),
                'thickness': str(layer.thickness.value),
                'thickness_enabled': str(layer.thickness.enabled),
                'material': layer.material.name,
                'formula': 'formula',
                'apm': '0.1',
                'solvent': 'solvent',
                'solvation': '0.2',
                'apm_enabled': 'True',
            }
        )
        if isinstance(layer, LayerAreaPerMolecule):
            layers_list[-1]['formula'] = layer.molecular_formula
            layers_list[-1]['apm'] = str(layer.area_per_molecule)
            layers_list[-1]['solvent'] = layer.solvent.name
            layers_list[-1]['solvation'] = str(layer.solvent_fraction)

    return layers_list
