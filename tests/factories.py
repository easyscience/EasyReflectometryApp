from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace


class ValueHolder:
    def __init__(self, value):
        self.value = value


class FlaggedValueHolder(ValueHolder):
    def __init__(self, value, enabled=True):
        super().__init__(value)
        self.enabled = enabled


class FakeMaterial:
    def __init__(self, name, sld=0.0, isld=0.0):
        self.name = name
        self.sld = ValueHolder(sld)
        self.isld = ValueHolder(isld)


class FakeLayer:
    def __init__(
        self,
        name='Layer',
        material=None,
        thickness=10.0,
        roughness=2.0,
        solvent=None,
        area_per_molecule=0.1,
        solvent_fraction=0.2,
        molecular_formula='formula',
    ):
        self.name = name
        self.material = material or FakeMaterial('Air')
        self.solvent = solvent or FakeMaterial('D2O')
        self._thickness = FlaggedValueHolder(thickness)
        self._roughness = FlaggedValueHolder(roughness)
        self.area_per_molecule = area_per_molecule
        self.solvent_fraction = solvent_fraction
        self.molecular_formula = molecular_formula

    @property
    def thickness(self):
        return self._thickness

    @thickness.setter
    def thickness(self, value):
        if isinstance(value, FlaggedValueHolder):
            self._thickness = value
        else:
            self._thickness.value = value

    @property
    def roughness(self):
        return self._roughness

    @roughness.setter
    def roughness(self, value):
        if isinstance(value, FlaggedValueHolder):
            self._roughness = value
        else:
            self._roughness.value = value


class FakeLayerAreaPerMolecule(FakeLayer):
    pass


class FakeLayerCollection(list):
    def __init__(self, layers=()):
        super().__init__(layers)
        self.data = self

    def add_layer(self):
        self.append(FakeLayer(name=f'Layer {len(self) + 1}'))

    def duplicate_layer(self, index):
        source = self[index]
        duplicate = type(source)(
            name=source.name,
            material=source.material,
            thickness=source.thickness.value,
            roughness=source.roughness.value,
            solvent=getattr(source, 'solvent', None),
            area_per_molecule=getattr(source, 'area_per_molecule', 0.1),
            solvent_fraction=getattr(source, 'solvent_fraction', 0.2),
            molecular_formula=getattr(source, 'molecular_formula', 'formula'),
        )
        self.insert(index + 1, duplicate)

    def remove(self, index):
        self.pop(index)

    def move_up(self, index):
        self[index - 1], self[index] = self[index], self[index - 1]

    def move_down(self, index):
        self[index], self[index + 1] = self[index + 1], self[index]


class FakeAssembly:
    def __init__(self, name='Assembly', assembly_type='Multi-layer', layers=None):
        self.name = name
        self.type = assembly_type
        self.layers = FakeLayerCollection(layers or [FakeLayer()])


class FakeMultilayer(FakeAssembly):
    def __init__(self, name='Assembly', layers=None):
        super().__init__(name=name, assembly_type='Multi-layer', layers=layers)


class FakeRepeatingMultilayer(FakeAssembly):
    def __init__(self, repetitions=1, name='Repeating Multi-layer', layers=None):
        super().__init__(name=name, assembly_type='Repeating Multi-layer', layers=layers)
        self.repetitions = ValueHolder(repetitions)


class FakeSurfactantLayer(FakeAssembly):
    def __init__(self, name='Surfactant Layer', layers=None):
        super().__init__(name=name, assembly_type='Surfactant Layer', layers=layers or [FakeLayer(), FakeLayer()])
        self.constrain_area_per_molecule = 'False'
        self.conformal_roughness = 'False'


class FakeSample(list):
    def __init__(self, assemblies=()):
        super().__init__(assemblies)
        self.data = self

    def add_assembly(self):
        self.append(FakeMultilayer(name=f'Assembly {len(self) + 1}'))

    def duplicate_assembly(self, index):
        source = self[index]
        if isinstance(source, FakeRepeatingMultilayer):
            duplicate = FakeRepeatingMultilayer(repetitions=source.repetitions.value, name=source.name, layers=list(source.layers))
        elif isinstance(source, FakeSurfactantLayer):
            duplicate = FakeSurfactantLayer(name=source.name, layers=list(source.layers))
        else:
            duplicate = FakeMultilayer(name=source.name, layers=list(source.layers))
        self.insert(index + 1, duplicate)

    def remove_assembly(self, index):
        self.pop(index)

    def move_up(self, index):
        self[index - 1], self[index] = self[index], self[index - 1]

    def move_down(self, index):
        self[index], self[index + 1] = self[index + 1], self[index]


class FakeResolutionFunction:
    def __init__(self, constant):
        self.constant = constant


class FakeModel:
    def __init__(
        self,
        name='Model',
        unique_name='model-1',
        color='#000000',
        scale=1.0,
        background=0.0,
        resolution_function=None,
        sample=None,
        user_data=None,
    ):
        self.name = name
        self.unique_name = unique_name
        self.color = color
        self.scale = ValueHolder(scale)
        self.background = ValueHolder(background)
        self.resolution_function = resolution_function
        self.sample = sample or FakeSample()
        self.user_data = user_data or {}
        self.add_assemblies_called = 0
        self.interface = None

    def add_assemblies(self):
        self.add_assemblies_called += 1
        self.sample = FakeSample(
            [
                FakeMultilayer(name='Assembly 1', layers=[FakeLayer(name='Layer 1')]),
                FakeMultilayer(name='Assembly 2', layers=[FakeLayer(name='Layer 2')]),
                FakeMultilayer(name='Assembly 3', layers=[FakeLayer(name='Layer 3')]),
            ]
        )


class FakeModelCollection(list):
    def add_model(self):
        self.append(make_model(name=f'Model {len(self) + 1}', unique_name=f'model-{len(self) + 1}'))

    def duplicate_model(self, index):
        source = self[index]
        duplicate = make_model(
            name=source.name,
            unique_name=f'{source.unique_name}-copy',
            color=source.color,
            scale=source.scale.value,
            background=source.background.value,
            resolution_function=source.resolution_function,
            sample=source.sample,
            user_data=dict(source.user_data),
        )
        self.insert(index + 1, duplicate)

    def move_up(self, index):
        self[index - 1], self[index] = self[index], self[index - 1]

    def move_down(self, index):
        self[index], self[index + 1] = self[index + 1], self[index]


class FakeMaterialCollection(list):
    def add_material(self, material=None):
        self.append(material or FakeMaterial(f'Material {len(self) + 1}'))

    def duplicate_material(self, index):
        source = self[index]
        self.insert(index + 1, FakeMaterial(source.name, source.sld.value, source.isld.value))

    def move_up(self, index):
        self[index - 1], self[index] = self[index], self[index - 1]

    def move_down(self, index):
        self[index], self[index + 1] = self[index + 1], self[index]


class FakeCalculatorController:
    def __init__(self, available_interfaces):
        self.available_interfaces = list(available_interfaces)
        self.switched_to = None

    def switch(self, value):
        self.switched_to = value


class FakeExperiment:
    def __init__(self, name, model=None, x=None, y=None, ye=None):
        self.name = name
        self.model = model
        self.x = [] if x is None else x
        self.y = [] if y is None else y
        self.ye = [] if ye is None else ye


class FakeMinimizerValue:
    def __init__(self, name):
        self.name = name


class FakeParameter:
    def __init__(
        self,
        name,
        unique_name,
        value=0.0,
        variance=0.0,
        minimum=0.0,
        maximum=100.0,
        unit='',
        free=False,
        independent=True,
        enabled=True,
        dependency_expression='',
        dependency_map=None,
    ):
        self.name = name
        self.unique_name = unique_name
        self.value = value
        self.variance = variance
        self.min = minimum
        self.max = maximum
        self.unit = unit
        self.free = free
        self.independent = independent
        self.enabled = enabled
        self.dependency_expression = dependency_expression
        self.dependency_map = dependency_map or {}

    def make_dependent_on(self, dependency_expression, dependency_map):
        self.independent = False
        self.dependency_expression = dependency_expression
        self.dependency_map = dependency_map


class FakeFitResult:
    def __init__(self, success=True, chi2=1.0, n_pars=1, x=None, reduced_chi=0.5, minimizer_engine='stub'):
        self.success = success
        self.chi2 = chi2
        self.n_pars = n_pars
        self.x = [] if x is None else x
        self.reduced_chi = reduced_chi
        self.minimizer_engine = minimizer_engine


class FakeProject:
    @property
    def calculator(self):
        return self._calculator_name

    @calculator.setter
    def calculator(self, value):
        self._calculator_name = value
        self._calculator.switched_to = value

    @property
    def _current_model_index(self):
        return self.current_model_index

    @_current_model_index.setter
    def _current_model_index(self, value):
        self.current_model_index = value

    def __init__(
        self,
        materials=None,
        experiments=None,
        models=None,
        calculator_interfaces=None,
        calculator_name='refnx',
        minimizer_name='LeastSquares',
    ):
        self._materials = materials or FakeMaterialCollection()
        self.current_material_index = 0
        self._experiments = experiments or {}
        self.experiments = self._experiments
        self._current_experiment_index = 0
        self._models = models or FakeModelCollection()
        self.models = self._models
        self.current_model_index = 0
        self.current_assembly_index = 0
        self.current_layer_index = 0
        self._calculator = FakeCalculatorController(calculator_interfaces or ['refnx', 'refl1d'])
        self._calculator_name = calculator_name
        self.minimizer = FakeMinimizerValue(minimizer_name)
        self._fitter = None
        self.fitter = None
        self._info = {'name': 'Demo Project', 'short_description': 'Demo Description', 'modified': '2026-03-19'}
        self.created = False
        self.path = Path('C:/tmp/demo-project')
        self.q_min = 0.01
        self.q_max = 0.5
        self.q_resolution = 200
        self.parameters = []
        self.calls = []

    def default_model(self):
        self.calls.append(('default_model',))

    def reset(self):
        self.calls.append(('reset',))

    def create(self):
        self.created = True
        self.calls.append(('create',))

    def save_as_json(self, overwrite=False):
        self.calls.append(('save_as_json', overwrite))

    def load_from_json(self, path):
        self.calls.append(('load_from_json', path))

    def load_experiment_for_model_at_index(self, path, index):
        self.calls.append(('load_experiment_for_model_at_index', path, index))

    def load_new_experiment(self, path):
        self.calls.append(('load_new_experiment', path))

    def count_datasets_in_file(self, path):
        self.calls.append(('count_datasets_in_file', path))
        return 3

    def load_all_experiments_from_file(self, path):
        self.calls.append(('load_all_experiments_from_file', path))
        return 2

    def set_sample_from_orso(self, sample):
        self.calls.append(('set_sample_from_orso', sample))

    def add_sample_from_orso(self, sample):
        self.calls.append(('add_sample_from_orso', sample))
        self.models.append(sample)

    def replace_models_from_orso(self, sample):
        self.calls.append(('replace_models_from_orso', sample))
        self.models[:] = [sample]

    def experimental_data_for_model_at_index(self, index):
        self.calls.append(('experimental_data_for_model_at_index', index))
        if index >= len(self.models):
            raise IndexError(index)
        return object()

    def set_path_project_parent(self, path):
        self.calls.append(('set_path_project_parent', path))

    def sample_data_for_model_at_index(self, index):
        self.calls.append(('sample_data_for_model_at_index', index))
        return SimpleNamespace(x=[], y=[])

    def sld_data_for_model_at_index(self, index):
        self.calls.append(('sld_data_for_model_at_index', index))
        return SimpleNamespace(x=[], y=[])

    def get_index_air(self):
        return [material.name for material in self._materials].index('Air')

    def get_index_si(self):
        return [material.name for material in self._materials].index('Si')

    def get_index_sio2(self):
        return [material.name for material in self._materials].index('SiO2')

    def get_index_d2o(self):
        return [material.name for material in self._materials].index('D2O')


@dataclass
class FakeWorkerFitter:
    method_result: object = None
    error: Exception | None = None

    def __post_init__(self):
        self.calls = []

    def fit(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error is not None:
            raise self.error
        return self.method_result


def make_material(name, sld=0.0, isld=0.0):
    return FakeMaterial(name, sld=sld, isld=isld)


def make_material_collection(*materials):
    return FakeMaterialCollection(materials)


def make_experiment(name, model=None, x=None, y=None, ye=None):
    return FakeExperiment(name=name, model=model, x=x, y=y, ye=ye)


def make_layer(**kwargs):
    return FakeLayer(**kwargs)


def make_layer_collection(*layers):
    return FakeLayerCollection(layers)


def make_assembly(name='Assembly', assembly_type='Multi-layer', layers=None):
    if assembly_type == 'Repeating Multi-layer':
        return FakeRepeatingMultilayer(name=name, layers=layers)
    if assembly_type == 'Surfactant Layer':
        return FakeSurfactantLayer(name=name, layers=layers)
    return FakeMultilayer(name=name, layers=layers)


def make_sample(*assemblies):
    return FakeSample(assemblies)


def make_model(**kwargs):
    return FakeModel(**kwargs)


def make_model_collection(*models):
    return FakeModelCollection(models)


def make_parameter(**kwargs):
    return FakeParameter(**kwargs)


def make_fit_result(**kwargs):
    return FakeFitResult(**kwargs)


def make_project(**kwargs):
    return FakeProject(**kwargs)


def make_worker_fitter(method_result=None, error=None):
    return FakeWorkerFitter(method_result=method_result, error=error)


def make_multi_fitter_stub(tolerance=1e-6, max_evaluations=5000):
    return SimpleNamespace(tolerance=tolerance, max_evaluations=max_evaluations)
