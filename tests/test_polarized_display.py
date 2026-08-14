"""Tests for polarized-experiment support in the plotting backend and logic wrappers."""

from types import SimpleNamespace

import numpy as np
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