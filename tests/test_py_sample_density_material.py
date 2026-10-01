"""Qt-level tests for the density-material slots on the Sample backend.

These exercise the real reflectometry library because the sld_coupled
toggle lives in the parameter dependency graph.
"""

import json

import pytest
from easyreflectometry import Project
from easyreflectometry.constraints import USER_CONSTRAINT_FLAG
from easyreflectometry.constraints import constrain
from easyreflectometry.sample import Layer
from easyreflectometry.sample import MaterialDensity
from easyreflectometry.sample import Multilayer
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
    material.scattering_length_real.free = True

    backend.setMaterialSldCoupledAtIndex(index, False)

    assert material.density.free is False
    assert material.scattering_length_real.free is False
    assert material.scattering_length_imag.free is False
    # None of the cleared knobs are independent+free, whatever model they
    # end up wired into — the predicate `count_free_parameters` itself uses.
    assert not any(
        parameter.independent and parameter.free
        for parameter in (
            material.density,
            material.scattering_length_real,
            material.scattering_length_imag,
        )
    )


def test_molecular_weight_is_a_descriptor_not_a_parameter(backend_with_density_material):
    """mw is a constant of the formula: as a DescriptorNumber it never enters
    project.parameters, so it cannot be freed into the fit (it is fully
    degenerate with density) and needs no app-side gating."""
    project, backend, index = backend_with_density_material
    material = project._materials[index]

    assert not hasattr(material.molecular_weight, 'free')
    assert material.molecular_weight not in project.parameters
    # The formula setter still refreshes it through the descriptor.
    backend.setMaterialFormulaAtIndex(index, 'B')
    assert material.molecular_weight.value == pytest.approx(10.81)



def test_recoupling_drops_the_user_constraint_mark(backend_with_density_material):
    """Re-coupling replaces a user constraint on isld with the density tie. The library must not
    then save that tie as the user's constraint (for a material outside the models, that save
    would even fail, as the density parameters cannot be addressed)."""
    project, backend, index = backend_with_density_material
    material = project._materials[index]
    backend.setMaterialSldCoupledAtIndex(index, False)
    constrain(material.isld, 'a', a=project._materials[0].isld)
    assert material.sld_coupled is False  # derived from sld alone
    assert getattr(material.isld, USER_CONSTRAINT_FLAG, False)

    backend.setMaterialSldCoupledAtIndex(index, True)

    assert material.isld.independent is False  # follows the density again
    assert not hasattr(material.isld, USER_CONSTRAINT_FLAG)
    assert 'parameter_constraints' not in project.as_dict(include_materials_not_in_model=True)


def test_project_with_a_decoupled_density_material_reloads_with_its_constraint(qcore_application):
    """A density material inside a model must load (it used to fail on 'sld_coupled'), keep its
    decoupled manual SLD, and keep a user constraint that depends on it."""
    project = Project()
    backend = Sample(project)
    model = project.models[0]
    material = MaterialDensity(chemical_structure='Ni', density=8.9, name='m1')
    model.add_assemblies(Multilayer(Layer(material, thickness=50.0, roughness=4.0, name='m1'), name='Ni film'))
    material.sld_coupled = False
    material.sld.value = 9.4
    substrate_isld = model.sample[0].layers[0].material.isld
    constrain(substrate_isld, 'm1_sld', m1_sld=material.sld)
    backend.store_constraint_metadata()
    project_dict = json.loads(json.dumps(project.as_dict()))

    global_object.map._clear()
    reloaded = Project()
    reloaded_backend = Sample(reloaded)
    reloaded.from_dict(project_dict)
    reloaded_backend.reload_constraint_states()

    reloaded_model = reloaded.models[0]
    reloaded_material = reloaded_model.sample[-1].layers[0].material
    assert isinstance(reloaded_material, MaterialDensity)
    assert reloaded_material.sld_coupled is False
    assert reloaded_material.sld.value == pytest.approx(9.4)
    reloaded_isld = reloaded_model.sample[0].layers[0].material.isld
    assert reloaded_isld.independent is False
    reloaded_material.sld.value = 8.0
    assert reloaded_isld.value == pytest.approx(8.0)
