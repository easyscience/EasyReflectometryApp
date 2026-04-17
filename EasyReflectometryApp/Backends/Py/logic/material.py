from typing import Union

from easyreflectometry import Project as ProjectLib
from easyreflectometry.sample import MaterialCollection


class Material:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib

    @property
    def _materials(self) -> MaterialCollection:
        return self._project_lib._materials

    @property
    def index(self) -> int:
        return self._project_lib.current_material_index

    @index.setter
    def index(self, new_value: Union[int, str]) -> None:
        self._project_lib.current_material_index = int(new_value)

    @property
    def name_at_current_index(self) -> str:
        return self._materials[self.index].name

    @property
    def materials(self) -> list[dict[str, str]]:
        return _from_materials_collection_to_list_of_dicts(self._materials)

    @property
    def material_names(self) -> list[str]:
        return [element['label'] for element in self.materials]

    def remove_at_index(self, value: str) -> None:
        self._materials.pop(int(value))

    def add_new(self) -> None:
        self._materials.add_material()

    def duplicate_selected(self) -> None:
        self._materials.duplicate_material(self.index)

    def move_selected_up(self) -> None:
        if self.index > 0:
            self._materials.move_up(self.index)
            self.index = self.index - 1

    def move_selected_down(self) -> None:
        if self.index < len(self._materials) - 1:
            self._materials.move_down(self.index)
            self.index = self.index + 1

    def set_name_at_current_index(self, new_value: str) -> bool:
        if self._materials[self.index].name != new_value:
            self._materials[self.index].name = new_value
            return True
        return False

    def set_name_at_index(self, index: int, new_value: str) -> bool:
        if not (0 <= index < len(self._materials)):
            return False
        if self._materials[index].name != new_value:
            self._materials[index].name = new_value
            return True
        return False

    def set_sld_at_current_index(self, new_value: float) -> bool:
        if self._materials[self.index].sld.value != new_value:
            self._materials[self.index].sld.value = new_value
            return True
        return False

    def set_sld_at_index(self, index: int, new_value: float) -> bool:
        if not (0 <= index < len(self._materials)):
            return False
        if self._materials[index].sld.value != new_value:
            self._materials[index].sld.value = new_value
            return True
        return False

    def set_isld_at_current_index(self, new_value: float) -> bool:
        if self._materials[self.index].isld.value != new_value:
            self._materials[self.index].isld.value = new_value
            return True
        return False

    def set_isld_at_index(self, index: int, new_value: float) -> bool:
        if not (0 <= index < len(self._materials)):
            return False
        if self._materials[index].isld.value != new_value:
            self._materials[index].isld.value = new_value
            return True
        return False


def _from_materials_collection_to_list_of_dicts(materials_collection: MaterialCollection) -> list[dict[str, str]]:
    materials_list = []
    for material in materials_collection:
        materials_list.append({'label': material.name, 'sld': str(material.sld.value), 'isld': str(material.isld.value)})
    return materials_list
