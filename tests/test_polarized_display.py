"""Tests for polarized-experiment support in the plotting backend and logic wrappers."""

from types import SimpleNamespace

import numpy as np
import pytest
from EasyReflectometryApp.Backends.Py.logic.experiments import experiment_channel_values
from EasyReflectometryApp.Backends.Py.logic.experiments import flatten_polarized
from EasyReflectometryApp.Backends.Py.logic.project import Project as ProjectLogic
from EasyReflectometryApp.Backends.Py.plotting_1d import Plotting1d


class FakeChannel(str):
    """Channel key behaving like PolarizationChannel (has .value)."""

    @property
    def value(self):
        return str(self)


class FakeDataset:
    def __init__(self, x, y, ye=None):
        self.x = np.asarray(x)
        self.y = np.asarray(y)
        self.ye = np.asarray(ye if ye is not None else np.zeros_like(self.x))

    def data_points(self):
        return list(zip(self.x, self.y, self.ye))


class FakePolarizedExperiment:
    def __init__(self, channels):
        self._channels = {FakeChannel(name): dataset for name, dataset in channels.items()}
        self.name = 'polarized'

    @property
    def available_channels(self):
        return list(self._channels.keys())

    @property
    def channels(self):
        return self._channels

    def __getitem__(self, channel):
        for key, dataset in self._channels.items():
            if str(key) == str(channel):
                return dataset
        raise KeyError(channel)


def _polarized_experiment():
    return FakePolarizedExperiment(
        {
            'pp': FakeDataset([0.1, 0.2], [1e-2, 1e-3], [1e-8, 1e-9]),
            'mm': FakeDataset([0.1, 0.3], [2e-2, 2e-3], [1e-8, 1e-9]),
        }
    )


class FakeProjectLib:
    def __init__(self, experiment):
        self._experiments = {0: experiment}
        self.current_experiment_index = 0
        self._current_model_index = 0
        self.q_min = 0.0
        self.q_max = 1.0
        self.models = [SimpleNamespace()]

    def experimental_data_for_model_at_index(self, index, channel=None):
        experiment = self._experiments[index]
        if channel is None:
            return experiment
        return experiment[channel]

    def experiment_is_polarized_at_index(self, index=0):
        # Part of the per-channel library API the plotting backend requires.
        return hasattr(self._experiments.get(index), 'available_channels')


class TestFlattenPolarized:
    def test_unpolarized_passthrough(self):
        dataset = FakeDataset([0.1], [1.0])
        assert flatten_polarized(dataset) is dataset
        assert experiment_channel_values(dataset) == []

    def test_first_visible_channel_wins(self):
        experiment = _polarized_experiment()
        assert flatten_polarized(experiment, {'mm'}) is experiment['mm']
        assert flatten_polarized(experiment, {'pp', 'mm'}) is experiment['pp']
        # No visible channel measured: fall back to the first measured one.
        assert flatten_polarized(experiment, {'pm'}) is experiment['pp']
        assert experiment_channel_values(experiment) == ['pp', 'mm']


class TestPlottingChannels:
    def _plotting(self, qcore_application):
        return Plotting1d(project_lib=FakeProjectLib(_polarized_experiment()), parent=None)

    def test_get_experiment_channels_rows(self, qcore_application):
        plotting = self._plotting(qcore_application)
        rows = plotting.getExperimentChannels(0)
        assert [row['channel'] for row in rows] == ['pp', 'mm']
        assert all(row['visible'] for row in rows)
        assert rows[0]['label'] == '↑↑' and rows[1]['label'] == '↓↓'
        assert rows[0]['color'] != rows[1]['color']

    def test_current_experiment_is_polarized(self, qcore_application):
        plotting = self._plotting(qcore_application)
        assert plotting.currentExperimentIsPolarized is True
        assert [row['channel'] for row in plotting.experimentChannelList] == ['pp', 'mm']

    def test_set_channel_visible_updates_and_keeps_one(self, qcore_application):
        plotting = self._plotting(qcore_application)
        emitted = {'count': 0}
        plotting.channelSelectionChanged.connect(lambda: emitted.__setitem__('count', emitted['count'] + 1))

        plotting.setChannelVisible('pp', False)
        assert 'pp' not in plotting._visible_channels
        assert emitted['count'] == 1

        plotting.setChannelVisible('pm', False)
        plotting.setChannelVisible('mp', False)
        # The last visible channel cannot be hidden.
        plotting.setChannelVisible('mm', False)
        assert plotting._visible_channels == frozenset({'mm'})

        plotting.setChannelVisible('pp', True)
        assert 'pp' in plotting._visible_channels

    def test_last_measured_channel_cannot_be_hidden(self, qcore_application):
        """Only the channels the UI offers matter: pp/mm here, pm/mp are not measured."""
        plotting = self._plotting(qcore_application)

        # Exactly the two clicks a user of a pp/mm experiment can perform.
        plotting.setChannelVisible('pp', False)
        plotting.setChannelVisible('mm', False)

        # mm stays visible: unmeasured pm/mp in the global set must not be
        # mistaken for "another visible channel".
        assert 'mm' in plotting._visible_channels
        assert [row['channel'] for row in plotting.getExperimentChannels(0) if row['visible']] == ['mm']

    def test_single_channel_experiment_cannot_be_blanked(self, qcore_application):
        plotting = Plotting1d(
            project_lib=FakeProjectLib(FakePolarizedExperiment({'pp': FakeDataset([0.1], [1e-2])})), parent=None
        )

        plotting.setChannelVisible('pp', False)

        assert 'pp' in plotting._visible_channels
        assert [row['channel'] for row in plotting.getExperimentChannels(0) if row['visible']] == ['pp']

    def test_four_channel_experiment_can_hide_all_but_one(self, qcore_application):
        channels = {name: FakeDataset([0.1], [1e-2]) for name in ('pp', 'pm', 'mp', 'mm')}
        plotting = Plotting1d(project_lib=FakeProjectLib(FakePolarizedExperiment(channels)), parent=None)

        for name in ('pp', 'pm', 'mp'):
            plotting.setChannelVisible(name, False)
        plotting.setChannelVisible('mm', False)

        assert plotting._visible_channels == frozenset({'mm'})

    def test_channel_state_is_notified_when_the_experiment_changes(self, qcore_application):
        """`currentExperimentIsPolarized`/`experimentChannelList` must not go stale."""
        project = FakeProjectLib(_polarized_experiment())
        project._experiments[1] = FakeDataset([0.1, 0.2], [1e-2, 1e-3])  # unpolarized
        plotting = Plotting1d(project_lib=project, parent=None)
        emitted = {'count': 0}
        plotting.experimentChannelsChanged.connect(lambda: emitted.__setitem__('count', emitted['count'] + 1))

        assert plotting.currentExperimentIsPolarized is True

        # Switching to the unpolarized experiment: the backend notifies QML and
        # both properties report the new experiment.
        project.current_experiment_index = 1
        plotting.notifyExperimentChannelsChanged()

        assert emitted['count'] == 1
        assert plotting.currentExperimentIsPolarized is False
        assert plotting.experimentChannelList == []

        project.current_experiment_index = 0
        plotting.notifyExperimentChannelsChanged()

        assert emitted['count'] == 2
        assert plotting.currentExperimentIsPolarized is True
        assert [row['channel'] for row in plotting.experimentChannelList] == ['pp', 'mm']

    def test_channel_selection_also_notifies_channel_state(self, qcore_application):
        plotting = self._plotting(qcore_application)
        emitted = {'count': 0}
        plotting.experimentChannelsChanged.connect(lambda: emitted.__setitem__('count', emitted['count'] + 1))

        plotting.setChannelVisible('pp', False)

        # The selector rows carry `visible`, so they must be re-read as well.
        assert emitted['count'] == 1

    def test_library_without_channel_api_is_reported_not_silently_empty(self, qcore_application):
        class LegacyProjectLib:
            """A library predating the channel API: no channel argument, no predicate."""

            def __init__(self, experiment):
                self._experiments = {0: experiment}
                self.current_experiment_index = 0
                self.models = [SimpleNamespace()]
                self.q_min = 0.0
                self.q_max = 1.0

            def experimental_data_for_model_at_index(self, index):
                return self._experiments[index]

        plotting = Plotting1d(project_lib=LegacyProjectLib(_polarized_experiment()), parent=None)

        with pytest.raises(RuntimeError, match='experiment_is_polarized_at_index is missing'):
            plotting._require_channel_api()
        # The slot itself stays safe for QML, but the failure is logged as an error.
        assert plotting.getExperimentChannelDataPoints(0, 'pp') == []

    def test_accessor_without_channel_argument_is_reported(self, qcore_application):
        """The predicate alone is not enough: the accessor must take `channel`."""

        class HalfUpdatedProjectLib(FakeProjectLib):
            def experimental_data_for_model_at_index(self, index):
                return self._experiments[index]

        plotting = Plotting1d(project_lib=HalfUpdatedProjectLib(_polarized_experiment()), parent=None)

        with pytest.raises(RuntimeError, match='no channel argument'):
            plotting._require_channel_api()

    def test_current_library_satisfies_the_channel_api(self, qcore_application):
        from easyreflectometry import Project as RealProject

        plotting = Plotting1d(project_lib=RealProject(), parent=None)

        assert plotting._check_channel_api() == ''

    def test_experiment_data_points_use_first_visible_channel(self, qcore_application):
        plotting = self._plotting(qcore_application)
        pp_points = plotting.getExperimentDataPoints(0)
        assert [point['x'] for point in pp_points] == [0.1, 0.2]

        plotting.setChannelVisible('pp', False)
        mm_points = plotting.getExperimentDataPoints(0)
        assert [point['x'] for point in mm_points] == [0.1, 0.3]

    def test_per_channel_data_points(self, qcore_application):
        plotting = self._plotting(qcore_application)
        mm_points = plotting.getExperimentChannelDataPoints(0, 'mm')
        assert [point['x'] for point in mm_points] == [0.1, 0.3]
        assert plotting.getExperimentChannelDataPoints(0, 'pm') == []  # not measured


class TestEndToEndPolarizedImport:
    def test_import_and_display_through_real_project(self, qcore_application, tmp_path):
        """Full chain: Experiment QObject → logic → real Project lib → Plotting1d channels."""
        from easyreflectometry import Project as RealProject
        from EasyReflectometryApp.Backends.Py.experiment import Experiment

        q = np.linspace(0.01, 0.2, 15)
        reflectivity = np.exp(-q * 30)
        paths = []
        for name in ('run_uu.dat', 'run_dd.dat'):
            path = tmp_path / name
            np.savetxt(path, np.column_stack([q, reflectivity, 0.01 * reflectivity]))
            # The QML FileDialog hands over file:/// URLs; mirror that here.
            paths.append(path.as_uri())

        project = RealProject()
        project.calculator = 'refl1d'
        project.default_model()
        experiment = Experiment(project_lib=project)

        rows = experiment.suggestPolarizedChannels(','.join(paths))
        assert [row['channel'] for row in rows] == ['pp', 'mm']

        experiment.loadPolarized(rows)

        assert project.experiment_is_polarized_at_index(0) is True
        plotting = Plotting1d(project_lib=project, parent=None)
        assert plotting.currentExperimentIsPolarized is True
        channels = plotting.getExperimentChannels(0)
        assert [row['channel'] for row in channels] == ['pp', 'mm']
        pp_points = plotting.getExperimentChannelDataPoints(0, 'pp')
        assert len(pp_points) == len(q)

    def test_imported_experiment_becomes_the_current_one(self, qcore_application, tmp_path):
        """With an experiment already loaded, the import must not stay invisible."""
        from easyreflectometry import Project as RealProject
        from EasyReflectometryApp.Backends.Py.experiment import Experiment

        q = np.linspace(0.01, 0.2, 15)
        reflectivity = np.exp(-q * 30)
        paths = []
        for name in ('plain.dat', 'run_uu.dat', 'run_dd.dat'):
            path = tmp_path / name
            np.savetxt(path, np.column_stack([q, reflectivity, 0.01 * reflectivity]))
            paths.append(path)

        project = RealProject()
        project.calculator = 'refl1d'
        project.default_model()
        project.load_experiment_for_model_at_index(str(paths[0]), 0)
        experiment = Experiment(project_lib=project)

        loaded = []
        experiment.experimentLoaded.connect(loaded.append)
        experiment.loadPolarized(
            [
                {'path': str(paths[1]), 'channel': 'pp'},
                {'path': str(paths[2]), 'channel': 'mm'},
            ]
        )

        # The polarized group is experiment 1, and the app is told to select it.
        assert project.experiment_is_polarized_at_index(1) is True
        assert loaded == [1]


class TestSwitchingBetweenExperiments:
    """State that must follow the current experiment, not the previous one."""

    @staticmethod
    def _two_polarized_projects():
        """Two polarized experiments with different channels and q grids."""
        first = FakePolarizedExperiment(
            {
                'pp': FakeDataset([0.1, 0.2], [1e-2, 1e-3]),
                'pm': FakeDataset([0.1, 0.2], [1e-4, 1e-5]),
                'mp': FakeDataset([0.1, 0.2], [1e-4, 1e-5]),
                'mm': FakeDataset([0.1, 0.2], [2e-2, 2e-3]),
            }
        )
        second = FakePolarizedExperiment({'pp': FakeDataset([0.5, 0.6], [3e-2, 3e-3])})
        project = FakeProjectLib(first)
        project._experiments[1] = second
        return project

    def test_channel_points_follow_the_current_experiment(self, qcore_application):
        project = self._two_polarized_projects()
        plotting = Plotting1d(project_lib=project, parent=None)

        assert [point['x'] for point in plotting.getExperimentChannelDataPoints(0, 'pp')] == [0.1, 0.2]

        project.current_experiment_index = 1
        plotting.notifyExperimentChannelsChanged()

        # Still polarized, so `isPolarizedMode` does not flip — the channel list
        # and the plotted points must change all the same.
        assert plotting.currentExperimentIsPolarized is True
        assert [row['channel'] for row in plotting.experimentChannelList] == ['pp']
        assert [point['x'] for point in plotting.getExperimentChannelDataPoints(1, 'pp')] == [0.5, 0.6]

    def test_hidden_channel_is_restored_when_the_new_experiment_needs_it(self, qcore_application):
        project = self._two_polarized_projects()
        plotting = Plotting1d(project_lib=project, parent=None)

        # Hide everything except mm on the four-channel experiment.
        for channel in ('pp', 'pm', 'mp'):
            plotting.setChannelVisible(channel, False)
        assert plotting._visible_channels == frozenset({'mm'})

        # Experiment 1 measures only pp, which is currently hidden: without
        # renormalization its chart would be empty and the user could not fix it.
        project.current_experiment_index = 1
        plotting.notifyExperimentChannelsChanged()

        assert [row['channel'] for row in plotting.experimentChannelList if row['visible']] == ['pp']

    def test_selection_is_kept_when_the_new_experiment_still_has_a_visible_channel(self, qcore_application):
        project = self._two_polarized_projects()
        project._experiments[1] = FakePolarizedExperiment(
            {'pp': FakeDataset([0.5], [3e-2]), 'mm': FakeDataset([0.5], [3e-3])}
        )
        plotting = Plotting1d(project_lib=project, parent=None)
        plotting.setChannelVisible('pp', False)

        project.current_experiment_index = 1
        plotting.notifyExperimentChannelsChanged()

        # mm is still visible on the new experiment, so the user's choice stands.
        assert [row['channel'] for row in plotting.experimentChannelList if row['visible']] == ['mm']

    def test_refused_hide_still_notifies_so_the_checkbox_rebinds(self, qcore_application):
        plotting = Plotting1d(project_lib=FakeProjectLib(_polarized_experiment()), parent=None)
        plotting.setChannelVisible('pp', False)
        emitted = {'count': 0}
        plotting.experimentChannelsChanged.connect(lambda: emitted.__setitem__('count', emitted['count'] + 1))

        plotting.setChannelVisible('mm', False)  # last measured channel: refused

        assert plotting._visible_channels == frozenset({'pm', 'mp', 'mm'})
        assert [row['channel'] for row in plotting.experimentChannelList if row['visible']] == ['mm']
        # Without this the checkbox stays unchecked while the channel is plotted.
        assert emitted['count'] == 1

    def test_axes_span_every_visible_channel(self, qcore_application):
        """Channel files need not share a q grid; the chart must not clip one."""
        plotting = Plotting1d(project_lib=FakeProjectLib(_polarized_experiment()), parent=None)

        # pp spans 0.1–0.2, mm spans 0.1–0.3.
        assert plotting.experimentMaxX == 0.3
        assert plotting.experimentMinX == 0.1

        plotting.setChannelVisible('mm', False)
        assert plotting.experimentMaxX == 0.2


class TestMultiExperimentChannelExpansion:
    """Selecting several experiments must not collapse a polarized one to one channel."""

    def _analysis(self, visible_channels=None):
        from EasyReflectometryApp.Backends.Py import analysis as analysis_module

        analysis = analysis_module.Analysis.__new__(analysis_module.Analysis)
        experiment = _polarized_experiment()
        project = FakeProjectLib(experiment)
        project._experiments[1] = FakeDataset([0.1, 0.4], [3e-2, 3e-3])  # unpolarized
        analysis._experiments_logic = SimpleNamespace(
            _project_lib=project,
            available=lambda: ['polarized', 'plain'],
        )
        analysis._selected_experiment_indices = [0, 1]
        analysis._plotting = SimpleNamespace(_visible_channels=frozenset(visible_channels or {'pp', 'mm'}))
        return analysis

    def test_polarized_experiment_expands_to_one_entry_per_visible_channel(self):
        rows = self._analysis().get_individual_experiment_data_list(expand_channels=True)

        assert [row['channel'] for row in rows] == ['pp', 'mm', '']
        assert [row['index'] for row in rows] == [0, 0, 1]
        # Distinct series identity per channel, and per-experiment hue kept.
        assert len({row['color'] for row in rows[:2]}) == 2
        assert '↑↑ pp' in rows[0]['name'] and '↓↓ mm' in rows[1]['name']

    def test_hidden_channels_are_not_plotted(self):
        rows = self._analysis(visible_channels={'mm'}).get_individual_experiment_data_list(expand_channels=True)

        assert [row['channel'] for row in rows] == ['mm', '']

    def test_flat_list_keeps_one_entry_per_experiment(self):
        """Consumers that are not channel aware yet must not get duplicate series."""
        rows = self._analysis().get_individual_experiment_data_list()

        assert [row['channel'] for row in rows] == ['', '']
        assert [row['index'] for row in rows] == [0, 1]

    def test_flat_list_follows_the_visible_channel(self):
        rows = self._analysis(visible_channels={'mm'}).get_individual_experiment_data_list()

        # The flattened polarized entry shows the first *visible* channel.
        assert list(rows[0]['data'].x) == [0.1, 0.3]

    def test_concatenated_data_follows_the_visible_channel(self):
        combined = self._analysis(visible_channels={'mm'}).get_concatenated_experiment_data()

        # mm spans 0.1/0.3, the unpolarized experiment 0.1/0.4; pp (0.1/0.2) is
        # hidden and must not be the one that gets concatenated.
        assert 0.2 not in list(combined.x)
        assert 0.3 in list(combined.x)

    def test_channel_shade_keeps_hue_and_varies_lightness(self):
        from EasyReflectometryApp.Backends.Py.logic.experiments import channel_shade

        shades = {channel: channel_shade('#7BA6C4', channel) for channel in ('pp', 'pm', 'mp', 'mm')}

        assert len(set(shades.values())) == 4
        assert channel_shade('not-a-color', 'pp') == 'not-a-color'


class TestProjectLogicPolarized:
    def test_sync_q_max_walks_polarized_channels(self):
        lib = SimpleNamespace(
            _experiments={0: _polarized_experiment()},
            q_max=0.05,
        )
        logic = ProjectLogic.__new__(ProjectLogic)
        logic._project_lib = lib
        # 0.3 is the largest q over all channels (mm); q_max should follow it.
        changed = logic._sync_q_max_with_loaded_experiments()
        assert changed is True
        assert lib.q_max >= 0.3