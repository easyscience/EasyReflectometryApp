from collections import Counter
from typing import Union

from easyreflectometry import Project as ProjectLib
from easyreflectometry.contrasts import ReplaceFormula
from easyreflectometry.contrasts import ReplaceMaterial
from easyreflectometry.contrasts import substitution_candidates
from easyreflectometry.model import Model
from easyreflectometry.model import ModelCollection
from easyreflectometry.model.resolution_functions import PercentageFwhm

from .helpers import get_original_name


def _formula_of(target) -> str:
    return getattr(target, 'molecular_formula', None) or getattr(target, 'chemical_structure', '')


class Models:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._contrast_candidates: list = []

    @property
    def _models(self) -> ModelCollection:
        return self._project_lib._models

    @property
    def index(self) -> int:
        return self._project_lib.current_model_index

    @index.setter
    def index(self, new_value: Union[int, str]) -> None:
        self._project_lib.current_model_index = int(new_value)

    @property
    def name_at_current_index(self) -> str:
        return get_original_name(self._models[self.index])

    @property
    def scaling_at_current_index(self) -> float:
        return self._models[self.index].scale.value

    @property
    def background_at_current_index(self) -> float:
        return self._models[self.index].background.value

    @property
    def resolution_at_current_index(self) -> str:
        if isinstance(self._models[self.index].resolution_function, PercentageFwhm):
            return str(self._models[self.index].resolution_function.constant)
        else:
            return '-'

    @property
    def models(self) -> list[dict[str, str]]:
        return _from_models_collection_to_list_of_dicts(self._models)

    @property
    def models_names(self) -> list[str]:
        return [element['label'] for element in self.models]

    def set_name_at_current_index(self, new_value: str) -> bool:
        if self._models[self.index].name != new_value:
            self._models[self.index].name = new_value
            return True
        return False

    def set_name_at_index(self, index: int, new_value: str) -> bool:
        if not (0 <= index < len(self._models)):
            return False
        if self._models[index].name != new_value:
            self._models[index].name = new_value
            return True
        return False

    def set_scaling_at_current_index(self, new_value: str) -> bool:
        if self._models[self.index].scale.value != float(new_value):
            self._models[self.index].scale.value = float(new_value)
            return True
        return False

    def set_background_at_current_index(self, new_value: str) -> bool:
        if self._models[self.index].background.value != float(new_value):
            self._models[self.index].background.value = float(new_value)
            return True
        return False

    def set_resolution_at_current_index(self, new_value: str) -> bool:
        if isinstance(self._models[self.index].resolution_function, PercentageFwhm):
            if self._models[self.index].resolution_function.constant != float(new_value):
                self._models[self.index].resolution_function.constant = float(new_value)
                return True
        return False

    def contrast_candidates(self, index: int) -> list[dict]:
        """What a contrast of the model at `index` can change: rows of ``label``, ``kind``
        (``'material'``: replace it by another material; ``'formula'``: give it another
        chemical formula) and, for a formula, the current one."""
        materials, formulas = substitution_candidates(self._project_lib.models[index])
        self._contrast_candidates = materials + formulas
        rows = [{'label': material.name, 'kind': 'material'} for material in materials]
        rows += [{'label': target.name, 'kind': 'formula', 'formula': _formula_of(target)} for target in formulas]
        # Two distinct objects may share a name (each surfactant layer has its own D2O).
        counts = Counter(row['label'] for row in rows)
        seen = Counter()
        for row in rows:
            if counts[row['label']] > 1:
                seen[row['label']] += 1
                row['label'] = f"{row['label']} #{seen[row['label']]}"
        return rows

    def add_contrast(self, index: int, name: str, choices: list[dict]) -> int:
        """Add a contrast of the model at `index`; `choices` refer to the rows of the last
        :meth:`contrast_candidates`, each with a palette ``material`` index or a ``formula``.
        Returns the new model's index."""
        substitutions = []
        for choice in choices:
            candidate = self._contrast_candidates[int(choice['candidate'])]
            if 'material' in choice:
                material = self._project_lib._materials[int(choice['material'])]
                if material is not candidate:
                    substitutions.append(ReplaceMaterial(candidate, material))
            elif str(choice['formula']).strip() not in ('', _formula_of(candidate)):
                substitutions.append(ReplaceFormula(candidate, str(choice['formula'])))
        return self._project_lib.add_contrast(index, name, substitutions)

    def experiments_using(self, index: int) -> list[str]:
        """Names of the experiments bound to the model at `index`."""
        experiments = self._project_lib.experiments
        return [experiments[key].name for key in self._project_lib.experiments_for_model(index)]

    def remove_at_index(self, index: int, rebind_to: int = -1) -> list[int]:
        """Remove the model; its experiments are removed, or bound to `rebind_to` when that is
        a model index. Returns the keys of the experiments removed with it."""
        experiments = None
        if self._project_lib.experiments_for_model(index):
            experiments = rebind_to if rebind_to >= 0 else 'remove'
        removal = self._project_lib.remove_model_at_index(index, experiments=experiments)
        return removal.experiments if experiments == 'remove' else []

    def default_model_content(self, model: Model) -> None:
        """Set the default content for a model."""
        model.add_assemblies()
        # Superphase (Air layer)
        air_material = self._project_lib._materials[self._project_lib.get_index_air()]
        model.sample.data[0].layers.data[0].material = air_material
        model.sample.data[0].layers.data[0].thickness = 0.0
        model.sample.data[0].layers.data[0].roughness = 0.0
        model.sample.data[0].layers.data[0].name = air_material.name + ' Layer'
        model.sample.data[0].name = 'Superphase'

        # Middle layer (SiO2)
        sio2_material = self._project_lib._materials[self._project_lib.get_index_sio2()]
        model.sample.data[1].layers.data[0].material = sio2_material
        model.sample.data[1].layers.data[0].thickness = 100.0
        model.sample.data[1].layers.data[0].roughness = 3.0
        model.sample.data[1].layers.data[0].name = sio2_material.name + ' Layer'
        model.sample.data[1].name = 'SiO2'

        # Subphase (Si substrate)
        si_material = self._project_lib._materials[self._project_lib.get_index_si()]
        model.sample.data[2].layers.data[0].material = si_material
        model.sample.data[2].name = 'Substrate'
        model.sample.data[2].layers.data[0].name = si_material.name + ' Layer'
        model.sample.data[2].layers.data[0].thickness = 0.0
        model.sample.data[2].layers.data[0].roughness = 1.2

    def add_new(self) -> None:
        self._models.add_model()
        self.default_model_content(self._models[-1])
        self._attach_calculator(self._models[-1])
        # Update index to point to the new model
        self.index = len(self._models) - 1

    def duplicate_selected_model(self) -> None:
        self._models.duplicate_model(self.index)
        self._attach_calculator(self._models[-1])
        # Update index to point to the duplicated model
        self.index = len(self._models) - 1

    def _attach_calculator(self, model: Model) -> None:
        """Bind a model added through the collection to the project's calculator.

        The collection's `add_model`/`duplicate_model` do not know the project's calculator, so
        a model added through them has no interface. The project's fitter is built lazily for
        the current model, and `Project.as_dict` (hence every save) touches it, so saving with
        such a model selected failed with an internal error instead of writing the file.
        """
        model.interface = self._project_lib._calculator

    def move_selected_up(self) -> None:
        if self.index > 0:
            self._project_lib.move_model(self.index, self.index - 1)
            self.index = self.index - 1

    def move_selected_down(self) -> None:
        if self.index < len(self._models) - 1:
            self._project_lib.move_model(self.index, self.index + 1)
            self.index = self.index + 1


def _from_models_collection_to_list_of_dicts(models_collection: ModelCollection) -> list[dict[str, str]]:
    models_list = []
    for model in models_collection:
        models_list.append(
            {
                'label': get_original_name(model),
                'color': str(model.color),
            }
        )
    return models_list
