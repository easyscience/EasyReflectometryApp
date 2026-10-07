from EasyReflectometryApp.Backends.Py.logic.experiment_selection import ALL_CHANNELS
from EasyReflectometryApp.Backends.Py.logic.experiment_selection import ExperimentSelection


def test_defaults():
    selection = ExperimentSelection()

    assert selection.indices == []
    assert selection.is_multi is False
    assert selection.visible_channels == ALL_CHANNELS


def test_set_indices_drops_out_of_range_and_reports_change():
    selection = ExperimentSelection([0])

    assert selection.set_indices([1, 5, -1, 2], available_count=3) is True
    assert selection.indices == [1, 2]
    assert selection.is_multi is True
    assert selection.set_indices([1, 2], available_count=3) is False


def test_set_indices_falls_back_to_the_first_experiment():
    selection = ExperimentSelection([1])

    assert selection.set_indices([7], available_count=2) is True
    assert selection.indices == [0]


def test_set_indices_without_experiments_is_empty():
    selection = ExperimentSelection([0])

    assert selection.set_indices([0], available_count=0) is True
    assert selection.indices == []


def test_remove_index_shifts_later_experiments_down():
    selection = ExperimentSelection([0, 2, 3])

    # Experiment 2 removed: 3 experiments are left.
    assert selection.remove_index(2, available_count=3) is True
    assert selection.indices == [0, 2]


def test_remove_index_of_the_only_selected_selects_the_first():
    selection = ExperimentSelection([1])

    assert selection.remove_index(1, available_count=2) is True
    assert selection.indices == [0]


def test_prune_drops_experiments_that_are_gone():
    selection = ExperimentSelection([0, 3])

    assert selection.prune(available_count=2) is True
    assert selection.indices == [0]
    assert selection.prune(available_count=2) is False


def test_reset_selects_only_the_current_experiment():
    selection = ExperimentSelection([0, 1, 2])

    assert selection.reset(current_index=1, available_count=3) is True
    assert selection.indices == [1]


def test_indices_are_a_copy():
    selection = ExperimentSelection([0])

    selection.indices.append(5)

    assert selection.indices == [0]


def test_visible_channels_are_stored_frozen():
    selection = ExperimentSelection()

    selection.visible_channels = {'mm'}

    assert selection.visible_channels == frozenset({'mm'})
