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
    assert logic.model_on_experiment(0) is model_a


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


def test_set_model_on_experiment_updates_current_experiment_model():
    model_a = object()
    model_b = object()
    experiments = [make_experiment('First', model=model_a)]
    project = make_project(experiments=experiments, models=[model_a, model_b])
    logic = Experiments(project)

    logic.set_model_on_experiment(1)

    assert experiments[0].model is model_b


def test_remove_experiment_updates_current_index_for_mapping_storage():
    experiments = {
        10: make_experiment('First'),
        20: make_experiment('Second'),
        30: make_experiment('Third'),
    }
    project = make_project(experiments=experiments)
    project._current_experiment_index = 2
    logic = Experiments(project)

    logic.remove_experiment(1)

    assert list(project._experiments.keys()) == [10, 30]
    assert project._current_experiment_index == 1


def test_remove_last_remaining_experiment_resets_index_to_zero():
    experiments = [make_experiment('Only')]
    project = make_project(experiments=experiments)
    project._current_experiment_index = 0
    logic = Experiments(project)

    logic.remove_experiment(0)

    assert project._experiments == []
    assert project._current_experiment_index == 0