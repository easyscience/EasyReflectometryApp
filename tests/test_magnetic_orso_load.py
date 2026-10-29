"""Magnetic samples through the app's real backend: ORSO load (plan A6), the
refusal under an engine without magnetism, import warnings, and the Magnetism
table and field controls following material and layer edits."""

import numpy as np
import pytest
from easyscience import global_object
from orsopy.fileio import Column
from orsopy.fileio import ErrorColumn
from orsopy.fileio import Orso
from orsopy.fileio import OrsoDataset
from orsopy.fileio import model_language
from orsopy.fileio import save_orso
from orsopy.fileio.base import ComplexValue
from orsopy.fileio.base import Value

COLUMNS = [
    Column(name='Qz', unit='1/angstrom', physical_quantity='wavevector transfer'),
    Column(name='R', physical_quantity='reflectivity'),
    ErrorColumn(error_of='R', error_type='uncertainty', value_is='sigma'),
    ErrorColumn(error_of='Qz', error_type='resolution', value_is='sigma'),
]
FE_RHO_M = 5.042


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.map._clear()
    yield
    global_object.map._clear()


def _write_film(path, **film_material) -> str:
    """An 'air | film | Si' .ort file whose film has the given model-language material."""
    layers = {
        'air': model_language.Layer(thickness=0.0, material=model_language.Material(sld=ComplexValue(real=0.0))),
        'film': model_language.Layer(thickness=Value(10.0, 'nm'), material=model_language.Material(**film_material)),
        'Si': model_language.Layer(thickness=0.0, material=model_language.Material(sld=ComplexValue(real=2.07e-6))),
    }
    info = Orso.empty()
    info.data_set = 0
    info.data_source.sample.name = 'magnetic film'
    info.data_source.sample.model = model_language.SampleModel(stack='air | film | Si', layers=layers)
    info.columns = list(COLUMNS)
    q = np.linspace(0.01, 0.3, 5)
    r = np.exp(-q * 10.0)
    save_orso([OrsoDataset(info=info, data=np.column_stack([q, r, r * 0.05, q * 0.02]))], str(path))
    return path.resolve().as_uri()


IRON = {'formula': 'Fe', 'mass_density': Value(7.874, 'g/cm^3'), 'magnetic_moment': 2.2}


@pytest.fixture
def backend(qcore_application):
    from EasyReflectometryApp.Backends.Py.py_backend import PyBackend

    backend = PyBackend()
    backend._project_lib.calculator = 'refl1d'
    return backend


def _signals(signal) -> list:
    received = []
    signal.connect(lambda *args: received.append(args))
    return received


def _film_row(backend) -> dict:
    project = backend._project_lib
    project.current_assembly_index = 1
    return backend._sample._layers_logic.magnetism[0]


class TestLoad:
    def test_a_moment_gives_a_magnetic_material_and_a_coupled_layer(self, backend, tmp_path):
        warnings_received = _signals(backend._project.sampleLoadWarning)

        backend._project.sampleLoad(_write_film(tmp_path / 'iron.ort', **IRON), False)

        film = backend._project_lib.models[0].sample[1].layers[0]
        material_row = next(row for row in backend._sample._material_logic.materials if row['label'] == film.material.name)
        assert material_row['magnetic'] is True
        assert float(material_row['magnetic_moment']) == pytest.approx(2.2)
        row = _film_row(backend)
        assert (row['magnetic'], row['material_magnetic'], row['rho_m_coupled']) == (True, True, True)
        assert float(row['rho_m']) == pytest.approx(FE_RHO_M, abs=1e-3)
        assert warnings_received == []

    def test_import_warnings_reach_the_user_after_a_successful_load(self, backend, tmp_path):
        warnings_received = _signals(backend._project.sampleLoadWarning)
        url = _write_film(
            tmp_path / 'no_density.ort', sld=ComplexValue(real=7.0e-6), magnetic_moment=2.2, relative_density=0.5
        )

        backend._project.sampleLoad(url, False)

        assert backend._project_lib.models[0].sample[1].layers[0].magnetism is None
        assert len(warnings_received) == 1
        (message,) = warnings_received[0]
        assert 'Magnetic moment of "film" not imported' in message
        assert 'relative_density of "film" is not applied' in message

    @pytest.mark.parametrize('append', [True, False])
    def test_an_engine_without_magnetism_refuses_and_keeps_the_project(self, backend, tmp_path, append):
        project = backend._project_lib
        project.calculator = 'refnx'
        models = list(project.models)
        materials = list(project._materials)
        errors = _signals(backend._project.projectLoadError)

        backend._project.sampleLoad(_write_film(tmp_path / 'iron.ort', **IRON), append)

        assert list(project.models) == models
        assert list(project._materials) == materials
        assert len(errors) == 1 and 'switch to refl1d' in errors[0][0]


class TestMagnetismTableFollowsMaterialEdits:
    @pytest.fixture
    def loaded(self, backend, tmp_path):
        backend._project.sampleLoad(_write_film(tmp_path / 'iron.ort', **IRON), False)
        film = backend._project_lib.models[0].sample[1].layers[0]
        index = list(backend._project_lib._materials).index(film.material)
        return backend, film, index

    def test_density_edit(self, loaded):
        backend, film, index = loaded
        received = _signals(backend._sample.magnetismChanged)

        backend._sample.setMaterialDensityAtIndex(index, str(7.874 / 2))

        assert received
        assert float(_film_row(backend)['rho_m']) == pytest.approx(FE_RHO_M / 2, abs=1e-3)

    def test_formula_edit(self, loaded):
        backend, film, index = loaded
        received = _signals(backend._sample.magnetismChanged)

        backend._sample.setMaterialFormulaAtIndex(index, 'Fe2')

        assert received
        assert float(_film_row(backend)['rho_m']) == pytest.approx(FE_RHO_M / 2, abs=1e-3)

    def test_moment_edit_notifies_once(self, loaded):
        backend, film, index = loaded
        received = _signals(backend._sample.magnetismChanged)

        backend._sample.setMaterialMagneticMomentAtIndex(index, '1.1')

        assert len(received) == 1
        assert float(_film_row(backend)['rho_m']) == pytest.approx(FE_RHO_M / 2, abs=1e-3)

    def test_a_non_magnetic_material_edit_does_not_notify(self, backend):
        from easyreflectometry.sample import MaterialDensity

        backend._project_lib._materials.add_material(MaterialDensity(name='Si-like'))
        index = len(backend._project_lib._materials) - 1
        received = _signals(backend._sample.magnetismChanged)

        backend._sample.setMaterialDensityAtIndex(index, '2.0')

        assert received == []


class TestFieldControls:
    def test_shown_only_for_a_magnetic_model(self, backend, tmp_path):
        backend._project.sampleLoad(_write_film(tmp_path / 'iron.ort', **IRON), False)
        assert backend._sample.magneticField['model_magnetic'] is True

        backend._project_lib.current_assembly_index = 1
        backend._sample.setLayerMagneticAtIndex(0, False)

        assert backend._sample.magneticField['model_magnetic'] is False
