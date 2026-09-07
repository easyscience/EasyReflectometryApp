import logging
from typing import Union

from easyreflectometry import Project as ProjectLib
from easyreflectometry.sample import MaterialCollection

logger = logging.getLogger(__name__)


def _is_density_material(material) -> bool:
    """Density materials (``MaterialDensity``) expose the ``sld_coupled``
    toggle; duck-typed so test fakes and future material types work."""
    return hasattr(material, 'sld_coupled')


def _parameter_is_writable(parameter) -> bool:
    """A coupled density material derives sld/isld from density — writing to
    the dependent parameter would raise, so the setters refuse instead.
    Checked per-parameter (not just `sld`): the lib guards sld and isld
    individually since they can disagree mid-toggle."""
    return getattr(parameter, 'independent', True)


# A density material's fittable input knobs; cleared (free = False) when the
# material's sld/isld are decoupled from them so an already-ticked knob
# doesn't keep entering the fit after its row goes inactive in the GUI.
# molecular_weight is deliberately absent: it is a DescriptorNumber (a
# formula constant, never fittable) and has no `free` flag.
_DENSITY_KNOB_NAMES = ('density', 'scattering_length_real', 'scattering_length_imag')


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
        material = self._materials[self.index]
        if not _parameter_is_writable(material.sld):
            return False
        if material.sld.value != new_value:
            material.sld.value = new_value
            return True
        return False

    def set_sld_at_index(self, index: int, new_value: float) -> bool:
        if not (0 <= index < len(self._materials)):
            return False
        material = self._materials[index]
        if not _parameter_is_writable(material.sld):
            return False
        if material.sld.value != new_value:
            material.sld.value = new_value
            return True
        return False

    def set_isld_at_current_index(self, new_value: float) -> bool:
        material = self._materials[self.index]
        if not _parameter_is_writable(material.isld):
            return False
        if material.isld.value != new_value:
            material.isld.value = new_value
            return True
        return False

    def set_isld_at_index(self, index: int, new_value: float) -> bool:
        if not (0 <= index < len(self._materials)):
            return False
        material = self._materials[index]
        if not _parameter_is_writable(material.isld):
            return False
        if material.isld.value != new_value:
            material.isld.value = new_value
            return True
        return False

    def set_sld_coupled_at_index(self, index: int, coupled: bool) -> bool:
        if not (0 <= index < len(self._materials)):
            return False
        material = self._materials[index]
        if not _is_density_material(material):
            return False
        if bool(material.sld_coupled) == bool(coupled):
            return False
        material.sld_coupled = bool(coupled)
        if not coupled:
            # The GUI greys these rows out (kind: 'inactive') but that is
            # display-only — the fitter reads Parameter.free, so a knob
            # ticked before decoupling would otherwise keep entering the
            # minimizer after it stops affecting the reflectivity.
            for knob_name in _DENSITY_KNOB_NAMES:
                knob = getattr(material, knob_name, None)
                if knob is not None:
                    knob.free = False
        return True

    def set_formula_at_index(self, index: int, formula: str) -> bool:
        if not (0 <= index < len(self._materials)):
            return False
        material = self._materials[index]
        if not _is_density_material(material):
            return False
        formula = formula.strip()
        if not formula or material.chemical_structure == formula:
            return False
        try:
            material.chemical_structure = formula
        except Exception:
            logger.warning('Rejected invalid chemical formula %r', formula)
            return False
        return True

    def set_density_at_index(self, index: int, new_value: float) -> bool:
        if not (0 <= index < len(self._materials)):
            return False
        material = self._materials[index]
        if not _is_density_material(material):
            return False
        try:
            value = float(new_value)
        except (TypeError, ValueError):
            return False
        if material.density.value == value:
            return False
        try:
            material.density.value = value
        except Exception:
            logger.warning('Rejected out-of-bounds density %r', value)
            return False
        return True


def _from_materials_collection_to_list_of_dicts(materials_collection: MaterialCollection) -> list[dict[str, str]]:
    materials_list = []
    for material in materials_collection:
        is_density = _is_density_material(material)
        materials_list.append(
            {
                'label': material.name,
                'sld': str(material.sld.value),
                'isld': str(material.isld.value),
                'kind': 'density' if is_density else 'sld',
                'formula': material.chemical_structure if is_density else '',
                'density': str(material.density.value) if is_density else '',
                'sld_coupled': bool(material.sld_coupled) if is_density else True,
            }
        )
    return materials_list
