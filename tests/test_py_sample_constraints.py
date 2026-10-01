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
from EasyReflectometryApp.Backends.Py import sample as sample_module
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

    def test_enable_toggle_out_of_range_is_a_no_op(self, project_and_backend):
        _, backend = project_and_backend
        idx = _dependent_index(backend, 'Film A thickness')
        alias_b = _alias(backend, 'Film B thickness')
        backend.addConstraint(idx, '<', f'{alias_b} * 2')
        backend.setInequalityConstraintEnabled(5, False)
        backend.setInequalityConstraintEnabled(-1, False)
        assert backend.inequalityConstraintsCount == 1


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
        fitting.on_fit_progress({'iteration': 5, 'chi2': 1e12, 'infeasible': True})
        fitting.clear_fit_progress()
        assert fitting.fit_infeasible is False
        assert fitting.fit_progress_message == ''


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

    def test_constant_period_clamp_survives_reload_and_restores(self, project_and_backend):
        project, backend = project_and_backend
        film_b = project.models[0].sample[2]
        assert backend.applyPhysicsConstraint(2, 'constant_period')['success']
        assert film_b.layers[0].thickness.max == pytest.approx(60.0)

        project_dict = json.loads(json.dumps(project.as_dict()))
        global_object.map._clear()
        reloaded = Project()
        reloaded_backend = Sample(reloaded)
        reloaded.from_dict(project_dict)

        # The clamp survives the round-trip, and removing the recipe afterwards
        # still hands back the original (pre-clamp) bound.
        reloaded_first = reloaded.models[0].sample[2].layers[0].thickness
        assert reloaded_first.max == pytest.approx(60.0)
        assert reloaded_backend.removePhysicsConstraint(2, 'constant_period')['success']
        assert reloaded_first.max == float('inf')

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


def _save_and_reload(project, backend):
    """What the app does on save and load: hooks around the library's own (de)serialization."""
    backend.store_constraint_metadata()
    project_dict = json.loads(json.dumps(project.as_dict(include_materials_not_in_model=True)))
    global_object.map._clear()
    reloaded_project = Project()
    reloaded_backend = Sample(reloaded_project)
    reloaded_project.from_dict(project_dict)
    reloaded_backend.reload_constraint_states()
    return reloaded_project, reloaded_backend, project_dict


def _equality_rows(backend):
    return sorted(
        (row['type'], row['dependentName'], row['relation'], row['expression'])
        for row in backend.constraintsList
        if row['type'] in ('dynamic', 'static', 'lower_bound', 'upper_bound') and row['dependentName'].startswith('Model')
    )


def _row_index(backend, dependent_text):
    return next(
        i
        for i, row in enumerate(backend.constraintsList)
        if all(part in row['dependentName'] for part in dependent_text.split())
    )


class TestEqualityConstraintPersistence:
    """GUI-made constraints must survive save/load (issue #311, item 5)."""

    def _add_all(self, backend):
        film_a_thickness = _dependent_index(backend, 'Film A thickness')
        assert backend.addConstraint(film_a_thickness, '=', 'model_film_b_thickness * 2')['success']
        assert backend.addConstraint(_dependent_index(backend, 'Film A roughness'), '=', '5')['success']
        assert backend.addConstraint(_dependent_index(backend, 'Film B thickness'), '>', '10')['success']
        assert backend.addConstraint(_dependent_index(backend, 'Film B roughness'), '<', '8')['success']

    def test_every_kind_of_row_survives_reload(self, project_and_backend):
        project, backend = project_and_backend
        self._add_all(backend)
        before = _equality_rows(backend)
        assert len(before) == 4

        _, reloaded_backend, _ = _save_and_reload(project, backend)

        assert _equality_rows(reloaded_backend) == before
        # Every row came back from the saved state, not just from inference.
        assert len(reloaded_backend._constraint_states) == 4

    def test_dynamic_constraint_is_live_after_reload(self, project_and_backend):
        project, backend = project_and_backend
        self._add_all(backend)

        reloaded, _, project_dict = _save_and_reload(project, backend)

        # Saved by the library itself, addressed by structural path.
        targets = [record['target'] for record in project_dict['parameter_constraints']]
        assert targets == ['models/0/sample/1/layers/0/thickness']
        film_a_thickness = reloaded.models[0].sample[1].layers[0].thickness
        film_b_thickness = reloaded.models[0].sample[2].layers[1].thickness
        assert film_a_thickness.independent is False
        film_b_thickness.value = 25.0
        assert film_a_thickness.value == pytest.approx(50.0)

    def test_static_constraint_reloads_pinned(self, project_and_backend):
        project, backend = project_and_backend
        self._add_all(backend)

        reloaded, reloaded_backend, _ = _save_and_reload(project, backend)

        roughness = reloaded.models[0].sample[1].layers[0].roughness
        assert roughness.value == pytest.approx(5.0)
        assert roughness.free is False
        assert roughness.independent is False
        # Pinned, so it is not offered as the dependent of a new constraint.
        assert not any('Film A roughness' in name for name in reloaded_backend.dependentParameterNames)

    def test_bounds_reload_with_their_values(self, project_and_backend):
        project, backend = project_and_backend
        self._add_all(backend)

        reloaded, _, _ = _save_and_reload(project, backend)

        film_b = reloaded.models[0].sample[2].layers[1]
        assert film_b.thickness.min == pytest.approx(10.0)
        assert film_b.roughness.max == pytest.approx(8.0)

    def test_remove_after_reload_restores_pre_constraint_state(self, project_and_backend):
        project, backend = project_and_backend
        self._add_all(backend)

        reloaded, reloaded_backend, _ = _save_and_reload(project, backend)
        film_a = reloaded.models[0].sample[1].layers[0]
        film_b = reloaded.models[0].sample[2].layers[1]

        reloaded_backend.removeConstraintByIndex(_row_index(reloaded_backend, 'Film A thickness'))
        assert film_a.thickness.independent is True
        assert film_a.thickness.value == pytest.approx(40.0)

        reloaded_backend.removeConstraintByIndex(_row_index(reloaded_backend, 'Film A roughness'))
        assert film_a.roughness.independent is True
        assert film_a.roughness.value == pytest.approx(3.0)

        reloaded_backend.removeConstraintByIndex(_row_index(reloaded_backend, 'Film B thickness'))
        assert film_b.thickness.min == pytest.approx(0.0)

        assert _equality_rows(reloaded_backend) == [('upper_bound', 'Model Film B roughness', '<', '8')]

    def test_removed_constraint_is_not_resurrected(self, project_and_backend):
        project, backend = project_and_backend
        self._add_all(backend)
        backend.removeConstraintByIndex(_row_index(backend, 'Film A thickness'))

        reloaded, reloaded_backend, project_dict = _save_and_reload(project, backend)

        assert 'parameter_constraints' not in project_dict
        assert reloaded.models[0].sample[1].layers[0].thickness.independent is True
        assert all('Film A thickness' not in row['dependentName'] for row in reloaded_backend.constraintsList)

    def test_dynamic_row_is_described_without_app_metadata(self, project_and_backend):
        # E.g. a file written by the library alone: the row is inferred from the parameter, with
        # dependencies named after the parameters rather than the saved aliases.
        project, backend = project_and_backend
        film_a_thickness = _dependent_index(backend, 'Film A thickness')
        assert backend.addConstraint(film_a_thickness, '=', 'model_film_b_thickness * 2')['success']
        backend._constraint_states.clear()

        _, reloaded_backend, _ = _save_and_reload(project, backend)

        assert _equality_rows(reloaded_backend) == [('dynamic', 'Model Film A thickness', '=', 'Model Film B thickness * 2')]

    def test_linked_models_survive_reload(self, project_and_backend):
        project, backend = project_and_backend
        project.models.duplicate_model(0)
        backend.constrainModelsParameters([0, 1])
        linked = [
            row
            for row in backend.constraintsList
            if row['type'] == 'dynamic' and row['uniqueName'] in backend._constraint_states
        ]
        assert linked

        reloaded, reloaded_backend, _ = _save_and_reload(project, backend)

        reloaded_linked = [
            row
            for row in reloaded_backend.constraintsList
            if row['type'] == 'dynamic' and row['uniqueName'] in reloaded_backend._constraint_states
        ]
        assert sorted((row['dependentName'], row['expression']) for row in reloaded_linked) == sorted(
            (row['dependentName'], row['expression']) for row in linked
        )
        reloaded.models[0].sample[1].layers[0].thickness.value = 33.0
        assert reloaded.models[1].sample[1].layers[0].thickness.value == pytest.approx(33.0)

    def test_constraint_on_a_disabled_parameter_survives_reload(self, project_and_backend):
        # Moving a film to the superphase disables its thickness; the constraint is still there.
        project, backend = project_and_backend
        assert backend.addConstraint(_dependent_index(backend, 'Film A thickness'), '=', '20')['success']
        backend.setCurrentAssemblyIndex(1)
        backend.moveSelectedAssemblyUp()
        thickness = project.models[0].sample[0].layers[0].thickness
        assert thickness.enabled is False

        reloaded, reloaded_backend, project_dict = _save_and_reload(project, backend)

        assert [record['path'] for record in project_dict['info']['app_constraints']] == [
            'models/0/sample/0/layers/0/thickness'
        ]
        reloaded_backend.setCurrentAssemblyIndex(0)
        reloaded_backend.moveSelectedAssemblyDown()
        reloaded_thickness = reloaded.models[0].sample[1].layers[0].thickness
        assert reloaded_thickness.enabled is True
        assert reloaded_thickness.independent is False
        reloaded_backend.removeConstraintByIndex(_row_index(reloaded_backend, 'Film A thickness'))
        assert reloaded_thickness.independent is True
        assert reloaded_thickness.value == pytest.approx(40.0)

    def test_replaced_tie_with_the_same_expression_is_not_mistaken_for_the_saved_one(self, project_and_backend):
        # Model link 'a' = M1's layer, then a recipe re-ties the same parameter as 'a' = a layer
        # of its own assembly. The link's display text and undo state must not survive.
        project, backend = project_and_backend
        project.models.duplicate_model(0)
        backend.constrainModelsParameters([0, 1])
        target = project.models[1].sample[2].layers[1].thickness
        assert target.unique_name in backend._constraint_states
        backend.setCurrentModelIndex(1)
        assert backend.applyPhysicsConstraint(2, 'conformal_thickness')['success']
        assert target.dependency_expression == 'a'
        assert target.dependency_map['a'] is project.models[1].sample[2].layers[0].thickness

        target_path = project.parameter_path(target)
        reloaded, reloaded_backend, project_dict = _save_and_reload(project, backend)

        assert target_path not in [record['path'] for record in project_dict['info'].get('app_constraints', [])]
        reloaded_target = reloaded.resolve_parameter_path(target_path)
        assert reloaded_target.unique_name not in reloaded_backend._constraint_states

    @pytest.mark.parametrize(
        ('dependent_value', 'source_relation', 'source_bound'),
        [(100.0, '<', '35'), (5.0, '>', '20')],
        ids=['above-inherited-max', 'below-inherited-min'],
    )
    def test_remove_restores_a_value_outside_the_inherited_bounds(
        self, project_and_backend, dependent_value, source_relation, source_bound
    ):
        project, backend = project_and_backend
        film_a_thickness = project.models[0].sample[1].layers[0].thickness
        film_a_thickness.value = dependent_value
        source_index = _dependent_index(backend, 'Film B thickness')
        assert backend.addConstraint(source_index, source_relation, source_bound)['success']
        assert backend.addConstraint(_dependent_index(backend, 'Film A thickness'), '=', 'model_film_b_thickness')['success']

        reloaded, reloaded_backend, _ = _save_and_reload(project, backend)
        reloaded_backend.removeConstraintByIndex(_row_index(reloaded_backend, 'Film A thickness'))

        reloaded_thickness = reloaded.models[0].sample[1].layers[0].thickness
        assert reloaded_thickness.value == pytest.approx(dependent_value)
        assert reloaded_thickness.min == pytest.approx(0.0)
        assert reloaded_thickness.max == float('inf')

    def test_expression_collapsing_the_bounds_is_rejected(self, project_and_backend):
        # The library cannot load a parameter whose min equals its max, so such a constraint
        # would make the project unloadable. It is refused and the parameter left as it was.
        project, backend = project_and_backend
        thickness = project.models[0].sample[1].layers[0].thickness

        result = backend.addConstraint(_dependent_index(backend, 'Film A thickness'), '=', 'model_film_b_thickness * 0')

        assert not result['success']
        assert 'single value' in result['message']
        assert thickness.independent is True
        assert (thickness.value, thickness.min, thickness.max) == (40.0, 0.0, float('inf'))
        assert 'parameter_constraints' not in project.as_dict()

    def test_equality_with_another_unit_is_rejected(self, project_and_backend):
        # A thickness tied to an SLD would take the SLD's unit: the model's total thickness then
        # fails, and so does the next load of the project.
        project, backend = project_and_backend
        thickness = project.models[0].sample[1].layers[0].thickness
        idx = _dependent_index(backend, 'Film A thickness')

        validation = backend.validateConstraintExpression(idx, '=', 'a_sld')
        result = backend.addConstraint(idx, '=', 'a_sld')

        assert not validation['valid'] and 'Incompatible units' in validation['message']
        assert not result['success']
        assert (thickness.independent, str(thickness.unit), thickness.value) == (True, 'Å', 40.0)

    def test_failed_add_leaves_the_parameter_as_it_was(self, project_and_backend, monkeypatch):
        project, backend = project_and_backend
        thickness = project.models[0].sample[1].layers[0].thickness
        real_constrain = sample_module.constrain

        def constrain_then_fail(parameter, expression, **dependencies):
            real_constrain(parameter, expression, **dependencies)
            raise RuntimeError('failed after changing the parameter')

        monkeypatch.setattr(sample_module, 'constrain', constrain_then_fail)
        result = backend.addConstraint(_dependent_index(backend, 'Film A thickness'), '=', 'model_film_b_thickness * 2')

        assert not result['success']
        assert thickness.independent is True
        assert (thickness.value, thickness.min, thickness.max) == (40.0, 0.0, float('inf'))
        assert 'parameter_constraints' not in project.as_dict()

    def test_stale_bound_row_is_not_saved(self, project_and_backend):
        project, backend = project_and_backend
        assert backend.addConstraint(_dependent_index(backend, 'Film B thickness'), '>', '10')['success']
        project.models[0].sample[2].layers[1].thickness.min = 2.0  # edited in the parameter table

        _, reloaded_backend, project_dict = _save_and_reload(project, backend)

        assert 'app_constraints' not in project_dict['info']
        assert _equality_rows(reloaded_backend) == []

    def test_reload_drops_the_rows_of_the_previous_project(self, project_and_backend):
        project, backend = project_and_backend
        assert backend.addConstraint(_dependent_index(backend, 'Film B thickness'), '>', '10')['success']

        project.reset()
        project.default_model()
        backend.reload_constraint_states()

        assert backend._constraint_states == {}

    def test_saved_project_file_loads(self, project_and_backend, tmp_path):
        # Through a real file: the unbounded maxima in the saved undo state must load back.
        project, backend = project_and_backend
        self._add_all(backend)
        before = _equality_rows(backend)
        project.set_path_project_parent(tmp_path)
        project.create()
        backend.store_constraint_metadata()
        project.save_as_json()

        global_object.map._clear()
        reloaded = Project()
        reloaded_backend = Sample(reloaded)
        reloaded.load_from_json(project.path_json)
        reloaded_backend.reload_constraint_states()

        assert _equality_rows(reloaded_backend) == before
