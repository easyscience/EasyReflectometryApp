from collections import Counter
from typing import Union

from easyreflectometry import Project as ProjectLib
from easyreflectometry.contrasts import ReplaceFormula
from easyreflectometry.contrasts import ReplaceMaterial
from easyreflectometry.contrasts import substitution_candidates
from easyreflectometry.model import Model
from easyreflectometry.model import ModelCollection
from easyreflectometry.model.resolution_functions import PercentageFwhm
from easyreflectometry.project import ModelRemoval

from .experiments import ordered_experiment_items
from .helpers import get_original_name
from .helpers import is_independent
from .helpers import set_value_widening_bounds


def _set_model_parameter(parameter, new_value: float) -> bool:
    """Set a model's scale or background; False for no change or a dependent or pinned
    parameter (both are constrainable, so the user can pin one on the Sample page)."""
    if not is_independent(parameter) or parameter.value == new_value:
        return False
    set_value_widening_bounds(parameter, new_value)
    return True


def _formula_of(target) -> str:
    return getattr(target, 'molecular_formula', None) or getattr(target, 'chemical_structure', '')


class Models:
    def __init__(self, project_lib: ProjectLib):
        self._project_lib = project_lib
        self._contrast_candidates: tuple = (None, [])

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
    def current_experiment_model_index(self) -> int | None:
        """The model of the selected experiment, or None without one (or when it has no model).

        Scale, background and resolution belong to the model, so the Experiment page shows
        those of the model the selected experiment is fitted with: with several contrasts,
        each experiment has its own.
        """
        items = ordered_experiment_items(self._project_lib)
        position = self._project_lib.current_experiment_index
        if not items or position is None or not 0 <= position < len(items):
            return None
        return self._project_lib.model_index_for_experiment(items[position][0])

    def scaling_at(self, index: int) -> float:
        return self._models[index].scale.value

    def background_at(self, index: int) -> float:
        return self._models[index].background.value

    def resolution_at(self, index: int) -> str:
        """The percentage resolution, or '-' for a measured (pointwise) one."""
        if isinstance(self._models[index].resolution_function, PercentageFwhm):
            return str(self._models[index].resolution_function.constant)
        return '-'

    @property
    def scaling_at_current_index(self) -> float:
        return self.scaling_at(self.index)

    @property
    def background_at_current_index(self) -> float:
        return self.background_at(self.index)

    @property
    def resolution_at_current_index(self) -> str:
        return self.resolution_at(self.index)

    @property
    def models(self) -> list[dict[str, str]]:
        return _from_models_collection_to_list_of_dicts(self._models)

    @property
    def models_names(self) -> list[str]:
        return [element['label'] for element in self.models]

    def set_name_at_current_index(self, new_value: str) -> bool:
        return _rename(self._models[self.index], new_value)

    def set_name_at_index(self, index: int, new_value: str) -> bool:
        if not (0 <= index < len(self._models)):
            return False
        return _rename(self._models[index], new_value)

    def set_scaling_at(self, index: int, new_value: float) -> bool:
        return _set_model_parameter(self._models[index].scale, new_value)

    def set_background_at(self, index: int, new_value: float) -> bool:
        return _set_model_parameter(self._models[index].background, new_value)

    def set_resolution_at(self, index: int, new_value: str) -> bool:
        resolution = self._models[index].resolution_function
        if isinstance(resolution, PercentageFwhm) and resolution.constant != float(new_value):
            resolution.constant = float(new_value)
            return True
        return False

    def set_scaling_at_current_index(self, new_value: float) -> bool:
        return self.set_scaling_at(self.index, new_value)

    def set_background_at_current_index(self, new_value: float) -> bool:
        return self.set_background_at(self.index, new_value)

    def set_resolution_at_current_index(self, new_value: str) -> bool:
        return self.set_resolution_at(self.index, new_value)

    def contrast_candidates(self, index: int) -> list[dict]:
        """What a contrast of the model at `index` can change: rows of ``label``, ``kind``
        (``'material'``: replace it by another material; ``'formula'``: give it another
        chemical formula) and, for a formula, the current one."""
        materials, formulas = substitution_candidates(self._project_lib.models[index])
        self._contrast_candidates = (self._project_lib.models[index], materials + formulas)
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
        Returns the new model's index.

        Raises ValueError when the model changed since the candidates were listed: a row
        would then name another object."""
        model, candidates = self._contrast_candidates
        materials, formulas = substitution_candidates(self._project_lib.models[index])
        current = materials + formulas
        if model is not self._project_lib.models[index] or [id(c) for c in current] != [id(c) for c in candidates]:
            raise ValueError('The model changed since the dialog opened; open it again.')
        substitutions = []
        for choice in choices:
            candidate = candidates[int(choice['candidate'])]
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

    def remove_at_index(self, index: int, rebind_to: int = -1) -> ModelRemoval:
        """Remove the model; its experiments are removed, or bound to `rebind_to` when that is
        a model index (counted before the removal). Returns the library's account of it: with
        the experiments removed, ``remap`` keys the remaining ones."""
        experiments = None
        if self._project_lib.experiments_for_model(index):
            experiments = rebind_to if rebind_to >= 0 else 'remove'
        return self._project_lib.remove_model_at_index(index, experiments=experiments)

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
        self._adopt_new_model(self._models[-1])
        # Update index to point to the new model
        self.index = len(self._models) - 1

    def duplicate_selected_model(self) -> None:
        self._models.duplicate_model(self.index)
        self._adopt_new_model(self._models[-1])
        # Update index to point to the duplicated model
        self.index = len(self._models) - 1

    def _adopt_new_model(self, model: Model) -> None:
        """Make a model added through the collection a full member of the project.

        The collection's `add_model`/`duplicate_model` know nothing of the project, so the
        project-level setup its own entry points (models setter, `add_contrast`, sample loads)
        perform has to be applied here:

        - the calculator: without an interface the project's lazily built fitter fails, and
          `Project.as_dict` (hence every save) touches it, so saving with such a model selected
          failed with an internal error instead of writing the file;
        - parameter states: the project disables (and fixes) the guide field angle and applied
          field of a model with no magnetic layer. Skipped, a new non-magnetic model's field
          parameters carried no `enabled` flag at all, read as enabled, and so appeared in the
          Analysis table as fittable polarisation parameters in an unpolarised project.
        """
        model.interface = self._project_lib._calculator
        self._project_lib._sync_parameter_states()

    # The library keeps the moved model the current one.
    def move_selected_up(self) -> None:
        if self.index > 0:
            self._project_lib.move_model(self.index, self.index - 1)

    def move_selected_down(self) -> None:
        if self.index < len(self._models) - 1:
            self._project_lib.move_model(self.index, self.index + 1)


def _rename(model, new_value: str) -> bool:
    """Give `model` the name the user typed. Returns whether its shown name changed.

    A model loaded from an ORSO file carries the file's sample name in
    ``user_data['original_name']``, which is shown instead of ``model.name``. The name
    the user types replaces it; otherwise the rename would not show, and the model
    table, which commits every keystroke, would put the file's name back at once.
    """
    if get_original_name(model) == new_value and model.name == new_value:
        return False
    model.name = new_value
    if isinstance(getattr(model, 'user_data', None), dict):
        model.user_data.pop('original_name', None)
    return True


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
