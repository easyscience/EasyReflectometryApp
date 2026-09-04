"""Qt-level tests for the density-material slots on the Sample backend.

These exercise the real reflectometry library because the sld_coupled
toggle lives in the parameter dependency graph.
"""

import pytest
from easyreflectometry import Project
from easyreflectometry.sample import MaterialDensity
from easyscience import global_object

from EasyReflectometryApp.Backends.Py.sample import Sample


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.map._clear()
    yield
    global_object.map._clear()


@pytest.fixture
def backend_with_density_material(qcore_application):
    project = Project()
    backend = Sample(project)  # installs the default model
    project._materials.add_material(MaterialDensity(chemical_structure='Si', density=2.33, name='SiDensity'))
    return project, backend, len(project._materials) - 1


def _spy(signal):
    calls = []
    signal.connect(lambda *args: calls.append(args))
    return calls


def test_set_material_sld_coupled_slot_toggles_and_emits(backend_with_density_material):
    project, backend, index = backend_with_density_material
    emitted = {
        'materials': _spy(backend.materialsTableChanged),
        'plot': _spy(backend.externalRefreshPlot),
        'sample': _spy(backend.externalSampleChanged),
        'models': _spy(backend.modelsTableChanged),
    }

    backend.setMaterialSldCoupledAtIndex(index, False)
    assert project._materials[index].sld_coupled is False
    assert {name: len(calls) for name, calls in emitted.items()} == {
        'materials': 1,
        'plot': 1,
        'sample': 1,
        'models': 1,
    }

    # A no-op toggle must not emit again.
    backend.setMaterialSldCoupledAtIndex(index, False)
    assert all(len(calls) == 1 for calls in emitted.values())


def test_density_and_formula_slots_update_material(backend_with_density_material):
    project, backend, index = backend_with_density_material
    material = project._materials[index]
    original_sld = material.sld.value

    backend.setMaterialDensityAtIndex(index, '4.66')
    assert material.density.value == pytest.approx(4.66)
    assert material.sld.value == pytest.approx(2 * original_sld)

    backend.setMaterialFormulaAtIndex(index, 'SiO2')
    assert material.chemical_structure == 'SiO2'

    # Invalid input is rejected without touching the material.
    backend.setMaterialFormulaAtIndex(index, '###')
    assert material.chemical_structure == 'SiO2'

    row = backend.materials[index]
    assert row['kind'] == 'density'
    assert row['formula'] == 'SiO2'
    assert row['sld_coupled'] is True


def test_sld_slot_refused_while_coupled(backend_with_density_material):
    project, backend, index = backend_with_density_material
    material = project._materials[index]
    coupled_sld = material.sld.value
    materials_calls = _spy(backend.materialsTableChanged)

    backend.setMaterialSldAtIndex(index, 9.9)
    assert material.sld.value == pytest.approx(coupled_sld)
    assert len(materials_calls) == 0

    backend.setMaterialSldCoupledAtIndex(index, False)
    backend.setMaterialSldAtIndex(index, 9.9)
    assert material.sld.value == 9.9


def test_decouple_clears_free_on_density_knobs(backend_with_density_material):
    """A knob ticked 'Fit' while coupled must not keep entering the fit once
    its row goes inactive — the GUI overlay (kind: 'inactive') is display
    only, `Parameter.free` is what the minimizer actually reads."""
    project, backend, index = backend_with_density_material
    material = project._materials[index]
    material.density.free = True
    material.molecular_weight.free = True

    backend.setMaterialSldCoupledAtIndex(index, False)

    assert material.density.free is False
    assert material.molecular_weight.free is False
    assert material.scattering_length_real.free is False
    assert material.scattering_length_imag.free is False
    # None of the cleared knobs are independent+free, whatever model they
    # end up wired into — the predicate `count_free_parameters` itself uses.
    assert not any(
        parameter.independent and parameter.free
        for parameter in (
            material.density,
            material.molecular_weight,
            material.scattering_length_real,
            material.scattering_length_imag,
        )
    )
