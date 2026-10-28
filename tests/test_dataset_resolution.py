"""Each dataset is drawn, reported and sampled with the resolution it was measured with.

The library fits every dataset (every spin channel of a polarized experiment)
with its own resolution; the model's resolution follows the first dataset only.
These tests pin that the application shows and samples the same curve the
fit compares a dataset to, not the model's curve.
"""

from unittest.mock import patch

import numpy as np
import pytest
from easyreflectometry import Project
from easyreflectometry.model import Pointwise
from easyscience import global_object

from EasyReflectometryApp.Backends.Py.logic import summary as summary_module
from EasyReflectometryApp.Backends.Py.plotting_1d import Plotting1d
from tests.test_logic_summary import FakeGridSpecModule
from tests.test_logic_summary import FakePyplot


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.map._clear()
    yield
    global_object.map._clear()


def _write_file(path, q, relative_sigma_q):
    r = np.exp(-40 * q) + 1e-6
    np.savetxt(path, np.column_stack([q, r, 0.05 * r, relative_sigma_q * q]), header='Qz R sR sQz')
    return path


def two_datasets_on_one_model(tmp_path) -> Project:
    """One model, a sharp and a broad measurement: the model follows the sharp one."""
    q = np.linspace(0.01, 0.3, 40)
    project = Project()
    project.default_model()
    project.load_new_experiment(_write_file(tmp_path / 'sharp.txt', q, 0.002))
    project.load_new_experiment(_write_file(tmp_path / 'broad.txt', q, 0.08))
    assert project.experiments[1].model is project.models[0]
    assert isinstance(project.experiments[1].resolution_function, Pointwise)
    return project


class TestAnalysisCurve:
    def test_each_dataset_is_drawn_with_its_own_resolution(self, qcore_application, tmp_path):
        project = two_datasets_on_one_model(tmp_path)
        plotting = Plotting1d(project_lib=project, parent=None)

        for index in (0, 1):
            points = plotting._get_aligned_analysis_values(index)
            q = np.array([point['q'] for point in points])
            drawn = np.array([point['calculated'] for point in points])
            expected = project.model_data_for_experiment_at_index(index, q_range=q).y
            np.testing.assert_allclose(drawn, expected, rtol=1e-12)

    def test_a_narrowed_q_range_keeps_the_widths_of_overlapping_measurements(self, qcore_application, tmp_path):
        # Two measurements of one contrast on the same q grid with very different
        # widths: the merged dataset holds every q twice. Restricting the q range
        # must not change the curve at the points that remain.
        q = np.array([0.01, 0.03, 0.05, 0.08, 0.10, 0.15, 0.20, 0.25, 0.30])
        project = Project()
        project.default_model()
        project.load_new_experiment(_write_file(tmp_path / 'sharp.txt', q, 0.002))
        project.append_to_experiment_at_index(0, _write_file(tmp_path / 'broad.txt', q, 0.08))
        merged = project.experiments[0]
        full = np.asarray(project.model_data_for_experiment_at_index(0).y)
        project.q_min = 0.03
        project.q_max = 0.25
        plotting = Plotting1d(project_lib=project, parent=None)

        points = plotting._get_aligned_analysis_values(0)

        x = np.asarray(merged.x)
        mask = (x >= 0.03) & (x <= 0.25)
        np.testing.assert_allclose([point['q'] for point in points], x[mask])
        np.testing.assert_allclose([point['calculated'] for point in points], full[mask], rtol=1e-12)

    def test_the_second_dataset_is_not_drawn_with_the_models_resolution(self, qcore_application, tmp_path):
        project = two_datasets_on_one_model(tmp_path)
        plotting = Plotting1d(project_lib=project, parent=None)

        points = plotting._get_aligned_analysis_values(1)
        q = np.array([point['q'] for point in points])
        drawn = np.array([point['calculated'] for point in points])

        assert not np.allclose(drawn, project.model_data_for_model_at_index(0, q_range=q).y, rtol=1e-3)


class TestReportCurve:
    def test_each_dataset_is_reported_with_its_own_resolution(self, qcore_application, tmp_path):
        project = two_datasets_on_one_model(tmp_path)
        model = project.models[0]

        for index in (0, 1):
            dataset = project.experiments[index]
            curve = summary_module.Summary._calculated_curve(
                model, np.asarray(dataset.x), resolution_function=dataset.resolution_function
            )
            np.testing.assert_allclose(curve, project.model_data_for_experiment_at_index(index).y, rtol=1e-12)

    def test_make_plot_passes_each_datasets_resolution(self, tmp_path, monkeypatch):
        project = two_datasets_on_one_model(tmp_path)
        logic = summary_module.Summary(project)
        seen = []

        def calculated_curve(model, x, channel=None, resolution_function=None):
            seen.append(resolution_function)
            return np.ones_like(x)

        monkeypatch.setattr(summary_module.Summary, '_calculated_curve', staticmethod(calculated_curve))
        # Real matplotlib next to a QCoreApplication crashes the test process; the
        # summary tests' fakes record the calls instead.
        monkeypatch.setattr(logic, '_plt', lambda: FakePyplot())
        monkeypatch.setattr(logic, '_gridspec', lambda: FakeGridSpecModule)

        logic.make_plot(10.0, 8.0)

        assert seen == [project.experiments[0].resolution_function, project.experiments[1].resolution_function]


class TestPosteriorBand:
    def test_band_is_smeared_with_each_datasets_resolution(self, tmp_path):
        from EasyReflectometryApp.Backends.Py import analysis as analysis_module

        project = two_datasets_on_one_model(tmp_path)
        analysis = analysis_module.Analysis.__new__(analysis_module.Analysis)
        analysis._project_lib = project
        experiments = [project.experiments[0], project.experiments[1]]
        analysis._bayesian_logic = type('Bayes', (), {'posterior': {'draws': np.zeros((4, 1)), 'param_names': ['p']}})()
        seen = []

        def band(draws, names, model, q_values, n_samples=200, resolution_function=None):
            seen.append(resolution_function)
            q = np.asarray(q_values)
            return q, q, q

        with (
            patch('easyreflectometry.analysis.bayesian.posterior_predictive_reflectivity', band),
            patch('easyreflectometry.analysis.bayesian.posterior_predictive_sld_profile', side_effect=RuntimeError),
        ):
            try:
                analysis._compute_and_publish_posterior_predictive()
            except (AttributeError, RuntimeError):
                pass  # signals are not wired on a bare instance; only the band calls matter

        assert seen == [experiment.resolution_function for experiment in experiments]


class TestSampling:
    def test_the_sampler_compares_each_dataset_to_the_curve_the_fit_does(self, tmp_path):
        from easyscience.fitting.minimizers.factory import AvailableMinimizers

        from EasyReflectometryApp.Backends.Py.logic.fitting import Fitting
        from tests.test_polarized_analysis import _StubMinimizers

        project = two_datasets_on_one_model(tmp_path)
        project.minimizer = AvailableMinimizers.Bumps_simplex

        fitter = Fitting(project).prepare_threaded_sample(_StubMinimizers())

        assert fitter is not None
        assert fitter.fit_datasets == [project.experiments[0], project.experiments[1]]
        for index in (0, 1):
            x = project.experiments[index].x
            np.testing.assert_allclose(
                fitter._fit_func[index](x), project.model_data_for_experiment_at_index(index).y, rtol=1e-12
            )
        # The model's own curve is not what the broad dataset is compared to.
        x = project.experiments[1].x
        assert not np.allclose(fitter._fit_func[1](x), project.model_data_for_model_at_index(0, q_range=x).y, rtol=1e-3)


class TestAppendToSelectedExperiment:
    """"Add file(s) to the selected experiment": one contrast measured as several curves."""

    @staticmethod
    def _backend(project):
        from EasyReflectometryApp.Backends.Py.experiment import Experiment

        return Experiment(project_lib=project)

    @staticmethod
    def _three_column(path, q):
        r = np.exp(-40 * q) + 1e-6
        np.savetxt(path, np.column_stack([q, r, 0.05 * r]), header='Qz R sR')
        return path

    def test_files_are_merged_and_keep_their_own_widths(self, qcore_application, tmp_path):
        project = Project()
        project.default_model()
        low = np.linspace(0.01, 0.1, 10)
        high = np.linspace(0.08, 0.3, 12)
        backend = self._backend(project)
        backend.load(str(_write_file(tmp_path / 'low.txt', low, 0.002)))  # the app's own Load: q range follows
        changed, q_range, failures, cautions = [], [], [], []
        backend.externalExperimentChanged.connect(lambda: changed.append(True))
        backend.qRangeUpdated.connect(lambda: q_range.append(True))
        backend.loadFailed.connect(failures.append)
        backend.loadWarning.connect(cautions.append)

        backend.appendToCurrent([str(_write_file(tmp_path / 'high.txt', high, 0.08))])

        assert failures == [] and cautions == []
        assert len(project.experiments) == 1
        merged = project.experiments[0]
        assert merged.x.size == low.size + high.size
        widths = merged.resolution_function.smearing(merged.x)
        np.testing.assert_allclose(widths[merged.x <= 0.07], 0.002 * merged.x[merged.x <= 0.07])
        np.testing.assert_allclose(widths[merged.x >= 0.11], 0.08 * merged.x[merged.x >= 0.11])
        assert changed == [True]
        assert q_range == [True]  # the merged curve reaches further than the first

    def test_a_file_without_resolution_is_added_with_a_warning(self, qcore_application, tmp_path):
        project = Project()
        project.default_model()
        q = np.linspace(0.01, 0.2, 10)
        project.load_new_experiment(_write_file(tmp_path / 'measured.txt', q, 0.01))
        backend = self._backend(project)
        cautions = []
        backend.loadWarning.connect(cautions.append)

        backend.appendToCurrent(str(self._three_column(tmp_path / 'plain.txt', q + 0.005)))

        assert project.experiments[0].x.size == 2 * q.size
        assert len(cautions) == 1 and cautions[0].startswith('plain.txt:')

    def test_a_failing_file_is_reported_and_the_others_still_load(self, qcore_application, tmp_path):
        project = Project()
        project.default_model()
        q = np.linspace(0.01, 0.2, 10)
        project.load_new_experiment(_write_file(tmp_path / 'first.txt', q, 0.01))
        backend = self._backend(project)
        failures = []
        backend.loadFailed.connect(failures.append)

        missing = str(tmp_path / 'missing.txt')
        backend.appendToCurrent([missing, str(_write_file(tmp_path / 'second.txt', q, 0.02))])

        assert len(failures) == 1 and failures[0].startswith('missing.txt:')
        assert project.experiments[0].x.size == 2 * q.size

    def test_files_from_the_qml_dialog_are_added(self, qcore_application, tmp_path):
        # A QML FileDialog's selectedFiles reaches the slot as a list of QUrl;
        # names with spaces, commas and non-ASCII characters must survive.
        from PySide6.QtCore import QUrl

        project = Project()
        project.default_model()
        q = np.linspace(0.01, 0.2, 10)
        project.load_new_experiment(_write_file(tmp_path / 'first.txt', q, 0.01))
        backend = self._backend(project)
        failures = []
        backend.loadFailed.connect(failures.append)
        names = ['angle 2, run 7.txt', 'Messung ß µ.txt']
        urls = [
            QUrl.fromLocalFile(str(_write_file(tmp_path / name, q + 0.001 * (i + 1), 0.02)))
            for i, name in enumerate(names)
        ]

        backend.appendToCurrent(urls)

        assert failures == []
        assert project.experiments[0].x.size == 3 * q.size

    def test_a_file_url_string_is_added(self, qcore_application, tmp_path):
        from PySide6.QtCore import QUrl

        project = Project()
        project.default_model()
        q = np.linspace(0.01, 0.2, 10)
        project.load_new_experiment(_write_file(tmp_path / 'first.txt', q, 0.01))
        backend = self._backend(project)
        failures = []
        backend.loadFailed.connect(failures.append)
        url = QUrl.fromLocalFile(str(_write_file(tmp_path / 'with space.txt', q + 0.001, 0.02))).toString()

        backend.appendToCurrent([url])

        assert failures == []
        assert project.experiments[0].x.size == 2 * q.size

    def test_refusals_and_warnings_of_one_call_are_reported_together(self, qcore_application, tmp_path):
        # The GUI shows one dialog: per-file emissions would leave only the last visible.
        project = Project()
        project.default_model()
        q = np.linspace(0.01, 0.2, 10)
        project.load_new_experiment(_write_file(tmp_path / 'first.txt', q, 0.01))
        backend = self._backend(project)
        failures, cautions = [], []
        backend.loadFailed.connect(failures.append)
        backend.loadWarning.connect(cautions.append)

        backend.appendToCurrent(
            [
                str(tmp_path / 'missing_a.txt'),
                str(self._three_column(tmp_path / 'plain.txt', q + 0.005)),
                str(tmp_path / 'missing_b.txt'),
            ]
        )

        assert cautions == []
        assert len(failures) == 1
        assert 'missing_a.txt:' in failures[0] and 'missing_b.txt:' in failures[0]
        assert 'plain.txt:' in failures[0]

    def test_the_warning_is_worded_for_the_user(self, qcore_application, tmp_path):
        project = Project()
        project.default_model()
        q = np.linspace(0.01, 0.2, 10)
        project.load_new_experiment(_write_file(tmp_path / 'measured.txt', q, 0.01))
        backend = self._backend(project)
        cautions = []
        backend.loadWarning.connect(cautions.append)

        backend.appendToCurrent([str(self._three_column(tmp_path / 'plain.txt', q + 0.005))])

        assert len(cautions) == 1
        assert 'PercentageFwhm' not in cautions[0] and cautions[0].count('plain.txt') == 1

    def test_appending_to_a_polarized_experiment_is_refused(self, qcore_application, tmp_path):
        from easyreflectometry.data import DataSet1D
        from easyreflectometry.data import PolarizedDataSet

        project = Project()
        project.default_model()
        q = np.linspace(0.01, 0.2, 10)
        channel = DataSet1D(name='pp', x=q, y=np.ones_like(q), ye=np.ones_like(q))
        project._experiments[0] = PolarizedDataSet(name='pol', channels={'pp': channel}, model=project.models[0])
        backend = self._backend(project)
        failures = []
        backend.loadFailed.connect(failures.append)

        backend.appendToCurrent([str(_write_file(tmp_path / 'more.txt', q, 0.02))])

        assert len(failures) == 1 and 'polarized' in failures[0]
