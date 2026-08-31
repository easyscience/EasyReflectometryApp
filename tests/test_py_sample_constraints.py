"""Backend tests for inequality constraints, derived parameters and physics recipes.

These exercise the real reflectometry library (not the fakes in
``tests/factories.py``) because the features under test live in the
parameter graph and the project's structural paths.
"""

import json

import pytest
from easyreflectometry import Project
from easyreflectometry.sample import Layer
from easyreflectometry.sample import Material
from easyreflectometry.sample import Multilayer
from easyreflectometry.sample import SurfactantLayer
from easyscience import global_object

from EasyReflectometryApp.Backends.Py.logic.fitting import Fitting
from EasyReflectometryApp.Backends.Py.logic.minimizers import Minimizers
from EasyReflectometryApp.Backends.Py.sample import Sample


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.map._clear()
    yield
    global_object.map._clear()


@pytest.fixture
def project_and_backend(qcore_application):
    project = Project()
    backend = Sample(project)  # installs the default model
    model = project.models[0]
    film_a = Multilayer(Layer(Material(3.0, 0.0, 'A'), thickness=40.0, roughness=3.0, name='A'), name='Film A')
    film_b = Multilayer(
        [
            Layer(Material(5.0, 0.0, 'B1'), thickness=30.0, roughness=3.0, name='B1'),
            Layer(Material(4.0, 0.0, 'B2'), thickness=30.0, roughness=3.0, name='B2'),
        ],
        name='Film B',
    )
    substrate = model.sample[-1]
    model.remove_assembly(len(model.sample) - 1)
    model.remove_assembly(len(model.sample) - 1)
    model.add_assemblies(film_a, film_b, SurfactantLayer(name='Surf'), substrate)
    return project, backend


def _dependent_index(backend, text):
    names = backend.dependentParameterNames
    return next(i for i, name in enumerate(names) if all(part in name for part in text.split()))


def _alias(backend, text, kind=None):
    for entry in backend.constraintParametersMetadata:
        if all(part in entry['displayName'] for part in text.split()) and (kind is None or entry['kind'] == kind):
            return entry['alias']
    raise AssertionError(f'no alias for {text}')


class TestDerivedParameterMetadata:
    def test_total_thickness_is_listed_read_only_with_alias(self, project_and_backend):
        project, backend = project_and_backend
        entries = [p for p in backend._parameters_logic.all_parameters() if p['kind'] == 'derived']
        assert len(entries) == 1
        entry = entries[0]
        assert entry['readOnly'] is True
        assert entry['independent'] is False
        assert entry['fit'] is False
        assert entry['value'] == pytest.approx(project.models[0].total_thickness.value)
        assert 'total_thickness' in entry['alias']
        assert [m for m in backend.constraintParametersMetadata if m['kind'] == 'derived']

    def test_derived_parameter_is_not_a_constraint_row(self, project_and_backend):
        _, backend = project_and_backend
        assert all('total_thickness' not in row['dependentName'] for row in backend.constraintsList)


class TestInequalityConstraints:
    def test_validation_reports_type_and_feasibility(self, project_and_backend):
        project, backend = project_and_backend
        idx = _dependent_index(backend, 'Film A thickness')
        alias_b = _alias(backend, 'Film B thickness')
        result = backend.validateConstraintExpression(idx, '<', f'{alias_b} * 2')
        assert result['valid'] and result['type'] == 'inequality' and result['warning'] == ''

        violated = backend.validateConstraintExpression(idx, '>', f'{alias_b} * 2')
        assert violated['valid'] and 'violate' in violated['warning']

    def test_mixed_literals_fall_back_to_numeric_for_inequalities(self, project_and_backend):
        # '90 - t_B' cannot be evaluated with units, but is a perfectly good
        # inequality expression (literals read in the dependent's unit).
        _, backend = project_and_backend
        idx = _dependent_index(backend, 'Film A thickness')
        alias_b = _alias(backend, 'Film B thickness')
        result = backend.validateConstraintExpression(idx, '<', f'90 - {alias_b}')
        assert result['valid'] and result['type'] == 'inequality'
        assert backend.addConstraint(idx, '<', f'90 - {alias_b}')['success']
        # equality constraints keep the strict unit-carrying behaviour
        equality = backend.validateConstraintExpression(idx, '=', f'90 - {alias_b}')
        assert not equality['valid']

    def test_unit_mismatch_is_rejected(self, project_and_backend):
        _, backend = project_and_backend
        idx = _dependent_index(backend, 'Film A thickness')
        alias_sld = _alias(backend, 'B1 sld')
        result = backend.validateConstraintExpression(idx, '<', alias_sld)
        assert not result['valid'] and 'Incompatible units' in result['message']

    def test_self_reference_is_rejected(self, project_and_backend):
        _, backend = project_and_backend
        idx = _dependent_index(backend, 'Film A thickness')
        alias_a = _alias(backend, 'Film A thickness')
        result = backend.validateConstraintExpression(idx, '<', f'{alias_a} * 2')
        assert not result['valid']

    def test_add_list_remove_and_persist(self, project_and_backend):
        project, backend = project_and_backend
        idx = _dependent_index(backend, 'Film A thickness')
        alias_b = _alias(backend, 'Film B thickness')
        alias_total = _alias(backend, 'total_thickness', kind='derived')

        assert backend.addConstraint(idx, '<', f'{alias_b} * 2')['success']
        assert backend.addConstraint(idx, '<', f'{alias_total} / 2')['success']
        assert backend.inequalityConstraintsCount == 2
        rows = [row for row in backend.constraintsList if row['type'] == 'inequality']
        assert [row['relation'] for row in rows] == ['≤', '≤']
        assert rows[0]['dependentName'].endswith('Film A thickness')
        assert 'Film B thickness * 2' in rows[0]['expression']
        assert all(row['satisfied'] for row in rows)
        # The parameter itself is untouched: it stays independent (no dependency is created).
        t_a = project.models[0].sample[1].layers[0].thickness
        assert t_a.independent

        project_dict = json.loads(json.dumps(project.as_dict()))
        global_object.map._clear()
        reloaded_project = Project()
        reloaded_backend = Sample(reloaded_project)
        reloaded_project.from_dict(project_dict)
        rows = [row for row in reloaded_backend.constraintsList if row['type'] == 'inequality']
        assert len(rows) == 2 and 'Film B thickness * 2' in rows[0]['expression']

        reloaded_backend.removeConstraintByIndex(reloaded_backend.constraintsList.index(rows[0]))
        assert reloaded_backend.inequalityConstraintsCount == 1

    def test_enable_toggle_and_violation_listing(self, project_and_backend):
        project, backend = project_and_backend
        idx = _dependent_index(backend, 'Film A thickness')
        alias_b = _alias(backend, 'Film B thickness')
        backend.addConstraint(idx, '>', f'{alias_b} * 2')  # 40 >= 60 is violated
        assert backend.violatedInequalityConstraints
        backend.setInequalityConstraintEnabled(0, False)
        assert backend.inequalityConstraintsCount == 0
        assert backend.violatedInequalityConstraints == []


class TestFitScreening:
    def _with_inequality(self, project_and_backend, relation='<'):
        project, backend = project_and_backend
        idx = _dependent_index(backend, 'Film A thickness')
        alias_b = _alias(backend, 'Film B thickness')
        assert backend.addConstraint(idx, relation, f'{alias_b} * 2')['success']
        return project, Minimizers(project), Fitting(project)

    def _select(self, minimizers, name):
        names = minimizers.minimizers_available()
        minimizers.set_minimizer_current_index(names.index(name))

    def test_non_bumps_engine_is_refused(self, project_and_backend):
        project, minimizers, fitting = self._with_inequality(project_and_backend)
        self._select(minimizers, 'LMFit_leastsq')
        assert minimizers.supports_inequalities() is False
        assert 'BUMPS' in fitting.inequality_constraints_error(minimizers)
        assert fitting.inequality_constraints_warning(minimizers)

    def test_bumps_and_bayesian_are_accepted(self, project_and_backend):
        project, minimizers, fitting = self._with_inequality(project_and_backend)
        self._select(minimizers, 'Bumps_simplex')
        assert minimizers.supports_inequalities() and fitting.inequality_constraints_error(minimizers) is None
        assert fitting.inequality_constraints_warning(minimizers) == ''
        minimizers.set_minimizer_current_index(0)  # Bayesian sentinel
        assert minimizers.is_bayesian_selected() and minimizers.supports_inequalities()
        assert fitting.inequality_constraints_error(minimizers) is None
        assert callable(fitting.snapshot_constraints_factory())

    def test_bumps_lm_only_warns(self, project_and_backend):
        project, minimizers, fitting = self._with_inequality(project_and_backend)
        self._select(minimizers, 'Bumps_lm')
        assert minimizers.enforces_inequalities_weakly()
        assert fitting.inequality_constraints_error(minimizers) is None
        assert 'Bumps_lm' in fitting.inequality_constraints_warning(minimizers)

    def test_infeasible_start_point_is_refused(self, project_and_backend):
        project, minimizers, fitting = self._with_inequality(project_and_backend, relation='>')
        self._select(minimizers, 'Bumps_simplex')
        assert 'violate' in fitting.inequality_constraints_error(minimizers)

    def test_no_constraints_means_no_factory(self, project_and_backend):
        project, backend = project_and_backend
        fitting = Fitting(project)
        minimizers = Minimizers(project)
        assert fitting.inequality_constraints_error(minimizers) is None
        assert fitting.snapshot_constraints_factory() is None

    def test_progress_payload_infeasible_flag(self, project_and_backend):
        project, _ = project_and_backend
        fitting = Fitting(project)
        fitting.on_fit_progress({'iteration': 3, 'chi2': 1e12, 'infeasible': True})
        assert fitting.fit_infeasible is True
        assert 'outside' in fitting.fit_progress_message
        fitting.on_fit_progress({'iteration': 4, 'chi2': 2.0, 'infeasible': False})
        assert fitting.fit_infeasible is False


class TestPhysicsRecipes:
    def test_recipe_availability_matrix(self, project_and_backend):
        _, backend = project_and_backend
        recipes = backend.physicsConstraintRecipes
        by_key = {(r['assemblyName'], r['id']): r for r in recipes}
        assert by_key[('Film A', 'conformal_roughness')]['available'] is False
        assert 'two layers' in by_key[('Film A', 'conformal_roughness')]['reason']
        assert by_key[('Film B', 'conformal_roughness')]['toggleable'] is True
        assert by_key[('Film B', 'constant_period')]['available'] is True
        assert by_key[('Surf', 'equal_apm')]['available'] is True
        assert by_key[('Surf', 'solvent_roughness')]['available'] is False  # needs conformal roughness first
        assert by_key[('Surf', 'mixture_fractions')]['toggleable'] is False
        assert by_key[('Surf', 'mixture_fractions')]['active'] is True
        assert ('Surf', 'conformal_thickness') not in by_key

    def test_apply_remove_and_grouped_rows(self, project_and_backend):
        project, backend = project_and_backend
        film_b = project.models[0].sample[2]
        assert backend.applyPhysicsConstraint(2, 'conformal_roughness')['success']
        assert backend.applyPhysicsConstraint(2, 'constant_period')['success']
        assert film_b.layers[1].roughness.independent is False
        assert film_b.layers[1].thickness.independent is False

        rows = [row for row in backend.constraintsList if row['type'] == 'recipe']
        assert sorted(row['expression'] for row in rows) == ['Conformal roughness', 'Constant period Λ']
        assert all(row['dependentName'] == 'Film B' for row in rows)
        # No raw per-parameter rows leak for owned parameters
        assert not any(row['type'] == 'dynamic' and 'Film B' in row['dependentName'] for row in backend.constraintsList)
        recipes = {(r['assemblyName'], r['id']): r for r in backend.physicsConstraintRecipes}
        assert recipes[('Film B', 'conformal_roughness')]['active'] is True
        assert recipes[('Film B', 'constant_period')]['active'] is True
        assert recipes[('Film B', 'conformal_thickness')]['active'] is False

        # Period: the last layer absorbs the change of the first
        total = film_b.layers[0].thickness.value + film_b.layers[1].thickness.value
        film_b.layers[0].thickness.value = 45.0
        assert film_b.layers[0].thickness.value + film_b.layers[1].thickness.value == pytest.approx(total)

        # Removing the grouped row removes the recipe
        period_row = next(row for row in backend.constraintsList if row.get('recipeId') == 'constant_period')
        backend.removeConstraintByIndex(backend.constraintsList.index(period_row))
        assert film_b.layers[1].thickness.independent is True
        assert backend.removePhysicsConstraint(2, 'conformal_roughness')['success']
        assert film_b.layers[1].roughness.independent is True

    def test_constant_period_clamps_the_free_layers(self, project_and_backend):
        project, backend = project_and_backend
        film_b = project.models[0].sample[2]
        first, second = film_b.layers[0].thickness, film_b.layers[1].thickness
        assert backend.applyPhysicsConstraint(2, 'constant_period')['success']

        # The period is the whole budget, so the free layer cannot exceed it and
        # the tied layer can never be driven to a negative thickness.
        assert first.max == pytest.approx(60.0)
        first.value = 1.0e6
        assert first.value == pytest.approx(60.0)
        assert second.value == pytest.approx(0.0)
        assert second.min >= 0.0
        assert project.models[0].total_thickness.min >= 0.0

        # Removing the recipe hands the original bound back
        assert backend.removePhysicsConstraint(2, 'constant_period')['success']
        assert first.max == float('inf')

    def test_solvent_roughness_requires_and_follows_conformal(self, project_and_backend):
        project, backend = project_and_backend
        surf = project.models[0].sample[3]
        substrate_roughness = project.models[0].sample[4].layers[0].roughness
        assert not backend.applyPhysicsConstraint(3, 'solvent_roughness')['success']
        assert backend.applyPhysicsConstraint(3, 'conformal_roughness')['success']
        assert backend.applyPhysicsConstraint(3, 'solvent_roughness')['success']
        assert substrate_roughness.independent is False
        surf.tail_layer.roughness.value = 7.0
        assert substrate_roughness.value == pytest.approx(7.0)
        # Removing conformal roughness also drops the dependent solvent recipe
        assert backend.removePhysicsConstraint(3, 'conformal_roughness')['success']
        assert substrate_roughness.independent is True

    def test_recipes_survive_reload(self, project_and_backend):
        project, backend = project_and_backend
        backend.applyPhysicsConstraint(2, 'conformal_roughness')
        backend.applyPhysicsConstraint(2, 'constant_period')
        backend.applyPhysicsConstraint(3, 'equal_apm')
        project_dict = json.loads(json.dumps(project.as_dict()))

        global_object.map._clear()
        reloaded = Project()
        reloaded_backend = Sample(reloaded)
        reloaded.from_dict(project_dict)

        rows = sorted((row['dependentName'], row['expression']) for row in reloaded_backend.constraintsList if row['type'] == 'recipe')
        assert rows == [
            ('Film B', 'Conformal roughness'),
            ('Film B', 'Constant period Λ'),
            ('Surf', 'Equal head/tail area per molecule'),
        ]
        film_b = reloaded.models[0].sample[2]
        total = film_b.layers[0].thickness.value + film_b.layers[1].thickness.value
        film_b.layers[0].thickness.value = 20.0
        assert film_b.layers[0].thickness.value + film_b.layers[1].thickness.value == pytest.approx(total)
