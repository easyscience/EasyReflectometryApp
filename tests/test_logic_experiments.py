from EasyReflectometryApp.Backends.Py.logic.experiments import Experiments
from tests.factories import make_experiment
from tests.factories import make_project


def test_available_orders_mapping_like_experiments_by_key():
    model_a = object()
    model_b = object()
    experiments = {
        5: make_experiment('Later', model=model_b),
        2: make_experiment('Earlier', model=model_a),
    }
    project = make_project(experiments=experiments, models=[model_a, model_b])
    logic = Experiments(project)

    assert logic.available() == ['Earlier', 'Later']
    assert logic.model_indices() == [0, 1]


def test_set_current_index_and_rename_current_experiment():
    experiments = [make_experiment('First'), make_experiment('Second')]
    project = make_project(experiments=experiments)
    logic = Experiments(project)

    assert logic.set_current_index(1) is True
    assert logic.current_index() == 1

    logic.set_experiment_name('Renamed')

    assert experiments[1].name == 'Renamed'
    assert logic.set_current_index(1) is False


def test_model_index_on_current_experiment_returns_index_or_minus_one():
    model_a = object()
    model_b = object()
    experiments = [make_experiment('First', model=model_b)]
    project = make_project(experiments=experiments, models=[model_a, model_b])
    logic = Experiments(project)

    assert logic.model_index_on_experiment() == 1

    experiments[0].model = None

    assert logic.model_index_on_experiment() == -1


def test_set_model_on_experiment_binds_only_that_row():
    model_a = object()
    model_b = object()
    experiments = {0: make_experiment('First', model=model_a), 1: make_experiment('Second', model=model_a)}
    project = make_project(experiments=experiments, models=[model_a, model_b])
    logic = Experiments(project)

    assert logic.set_model_on_experiment(1, 1)

    assert experiments[1].model is model_b
    assert experiments[0].model is model_a  # only the row asked for
    assert logic.model_indices() == [0, 1]
    assert not logic.set_model_on_experiment(1, 1)


def test_remove_experiment_updates_current_index_for_mapping_storage():
    experiments = {
        10: make_experiment('First'),
        20: make_experiment('Second'),
        30: make_experiment('Third'),
    }
    third = experiments[30]
    project = make_project(experiments=experiments)
    project._current_experiment_index = 2
    logic = Experiments(project)

    logic.remove_experiment(1)

    # Re-keyed by position: positions, selection indices and the library's lookups
    # (which use the position as the key) stay the same thing.
    assert list(project._experiments.keys()) == [0, 1]
    assert logic.available() == ['First', 'Third']
    assert project._current_experiment_index == 1
    assert project._experiments[1] is third


def test_remove_first_experiment_keeps_the_others_addressable_by_position():
    experiments = {i: make_experiment(f'E{i}') for i in range(3)}
    first, second, third = (experiments[i] for i in range(3))
    project = make_project(experiments=experiments)
    logic = Experiments(project)

    logic.remove_experiment(0)

    assert logic.available() == ['E1', 'E2']
    assert project._experiments[0] is second
    assert project._experiments[1] is third
    assert first not in project._experiments.values()


def test_remove_last_remaining_experiment_resets_index_to_zero():
    experiments = {0: make_experiment('Only')}
    project = make_project(experiments=experiments)
    project._current_experiment_index = 0
    logic = Experiments(project)

    logic.remove_experiment(0)

    assert project._experiments == {}
    assert project._current_experiment_index == 0
