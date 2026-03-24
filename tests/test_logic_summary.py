from types import SimpleNamespace

import numpy as np

from EasyReflectometryApp.Backends.Py.logic import summary as summary_module
from tests.factories import make_assembly
from tests.factories import make_experiment
from tests.factories import make_layer
from tests.factories import make_model
from tests.factories import make_model_collection
from tests.factories import make_project
from tests.factories import make_sample


class FakeSummaryLib:
    def __init__(self, project_lib):
        self.project_lib = project_lib
        self.saved_pdf_path = None

    def compile_html_summary(self, figures=False):
        suffix = ' with figures' if figures else ''
        return f'<html><body><h1>Base{suffix}</h1></body></html>'

    def save_pdf_summary(self, path):
        self.saved_pdf_path = path


class FakeCalculatorRuntime:
    def reflectity_profile(self, x, unique_name):
        return np.asarray(x) * 0 + 0.25


class FakeCalculatorFactory:
    def __call__(self):
        return FakeCalculatorRuntime()


class FakeAxis:
    def __init__(self):
        self.plot_calls = []
        self.errorbar_calls = []
        self.legend_called = False
        self.labels = {}

    def set_xlabel(self, value):
        self.labels['xlabel'] = value

    def set_ylabel(self, value):
        self.labels['ylabel'] = value

    def set_yscale(self, value):
        self.labels['yscale'] = value

    def errorbar(self, *args, **kwargs):
        self.errorbar_calls.append((args, kwargs))

    def plot(self, *args, **kwargs):
        self.plot_calls.append((args, kwargs))

    def has_data(self):
        return bool(self.plot_calls or self.errorbar_calls)

    def legend(self, **kwargs):
        self.legend_called = True


class FakeFigure:
    def __init__(self):
        self.axes = [FakeAxis(), FakeAxis()]
        self.saved = None
        self._index = 0

    def add_subplot(self, *_args, **_kwargs):
        axis = self.axes[self._index]
        self._index += 1
        return axis

    def savefig(self, path, dpi):
        self.saved = (path, dpi)


class FakePyplot:
    def __init__(self):
        self.figure_obj = None
        self.closed = None
        self.show_called = False

    def figure(self, **_kwargs):
        self.figure_obj = FakeFigure()
        return self.figure_obj

    def close(self, figure):
        self.closed = figure

    def show(self):
        self.show_called = True


class FakeGridSpecModule:
    class _GridSpec:
        def __getitem__(self, item):
            return item

    @staticmethod
    def GridSpec(*_args, **_kwargs):
        return FakeGridSpecModule._GridSpec()


def make_summary_project(tmp_path):
    sample = make_sample(
        make_assembly(name='Top', layers=[make_layer(name='Top')]),
        make_assembly(name='Middle', layers=[make_layer(name='Middle')]),
        make_assembly(name='Bottom', layers=[make_layer(name='Bottom')]),
    )
    models = make_model_collection(make_model(name='Model <1>', unique_name='m1', sample=sample, color='#123456'))
    project = make_project(models=models)
    project.path = tmp_path / 'report-dir'
    project._calculator = FakeCalculatorFactory()
    project.experiments = {2: make_experiment('Exp <1>', model=models[0], x=np.array([0.1, 0.2]), y=np.array([1.0, 2.0]), ye=np.array([0.1, 0.2]))}
    project._experiments = project.experiments
    project.sample_data_for_model_at_index = lambda index: SimpleNamespace(x=np.array([0.1]), y=np.array([1.0]))
    project.sld_data_for_model_at_index = lambda index: SimpleNamespace(x=np.array([1.0, 2.0]), y=np.array([3.0, 4.0]))
    return project


def test_summary_html_and_save_operations(tmp_path, monkeypatch):
    monkeypatch.setattr(summary_module, 'SummaryLib', FakeSummaryLib)
    project = make_summary_project(tmp_path)
    logic = summary_module.Summary(project)

    html = logic.as_html
    assert 'All Samples' in html
    assert 'All Experiments' in html
    assert 'Model &lt;1&gt;' in html
    assert 'Exp &lt;1&gt;' in html

    logic.save_as_html()
    html_path = project.path / 'summary.html'
    assert html_path.exists()
    assert 'Base with figures' in html_path.read_text(encoding='utf-8')

    logic.save_as_pdf()
    assert logic._summary.saved_pdf_path == project.path / 'summary.pdf'


def test_summary_make_plot_save_plot_and_show_plot(tmp_path, monkeypatch):
    monkeypatch.setattr(summary_module, 'SummaryLib', FakeSummaryLib)
    project = make_summary_project(tmp_path)
    logic = summary_module.Summary(project)
    fake_pyplot = FakePyplot()
    monkeypatch.setattr(logic, '_plt', lambda: fake_pyplot)
    monkeypatch.setattr(logic, '_gridspec', lambda: FakeGridSpecModule)

    figure = logic.make_plot(10.0, 8.0)

    reflectivity_axis, sld_axis = figure.axes
    assert reflectivity_axis.errorbar_calls
    assert len(reflectivity_axis.plot_calls) == 1
    assert sld_axis.plot_calls
    assert reflectivity_axis.legend_called is True

    target = tmp_path / 'plots' / 'plot.png'
    logic.save_plot(str(target), 10.0, 8.0)
    assert fake_pyplot.figure_obj.saved == (target, 600)
    assert fake_pyplot.closed is fake_pyplot.figure_obj

    logic.show_plot(10.0, 8.0)
    assert fake_pyplot.show_called is True


def test_summary_ordering_and_empty_sections(tmp_path, monkeypatch):
    monkeypatch.setattr(summary_module, 'SummaryLib', FakeSummaryLib)
    project = make_project(models=make_model_collection())
    project.path = tmp_path / 'empty-report'
    project.experiments = {}
    project._experiments = {}
    logic = summary_module.Summary(project)

    assert logic._ordered_experiments() == []
    assert logic._all_models_section_html() == '<h3>All Samples</h3><p>No samples available.</p>'
    assert logic._all_experiments_section_html() == '<h3>All Experiments</h3><p>No experiments available.</p>'


def test_summary_injection_and_explicit_paths(tmp_path, monkeypatch):
    monkeypatch.setattr(summary_module, 'SummaryLib', FakeSummaryLib)
    project = make_summary_project(tmp_path)
    logic = summary_module.Summary(project)
    logic.file_name = 'custom-summary'
    logic.plot_file_name = 'custom-plots'

    injected = logic._inject_multimodel_multiexperiment_sections('<div>base</div>')

    assert 'All Samples' in injected
    assert 'All Experiments' in injected
    assert logic.file_path == project.path / 'custom-summary'
    assert logic.plot_file_path == project.path / 'custom-plots'

    html_target = tmp_path / 'explicit' / 'report.html'
    pdf_target = tmp_path / 'explicit' / 'report.pdf'
    logic.save_as_html(str(html_target))
    logic.save_as_pdf(str(pdf_target))

    assert html_target.exists()
    assert logic._summary.saved_pdf_path == pdf_target


def test_summary_experiment_section_handles_empty_names_missing_models_and_nan_ranges(tmp_path, monkeypatch):
    monkeypatch.setattr(summary_module, 'SummaryLib', FakeSummaryLib)
    project = make_project(models=make_model_collection())
    project.path = tmp_path / 'report'
    project.experiments = [make_experiment('', model=None, x=np.array([]), y=np.array([]), ye=np.array([]))]
    project._experiments = project.experiments
    logic = summary_module.Summary(project)

    html = logic._all_experiments_section_html()

    assert 'Experiment 1' in html
    assert 'N/A' in html
    assert 'nan' in html


def test_summary_make_plot_uses_plain_plot_without_valid_errors_and_sample_fallback(tmp_path, monkeypatch):
    monkeypatch.setattr(summary_module, 'SummaryLib', FakeSummaryLib)
    project = make_summary_project(tmp_path)
    project.experiments = [
        make_experiment('No Errors', model=project.models[0], x=np.array([0.1, 0.2]), y=np.array([1.0, 2.0]), ye=None),
        make_experiment('Mismatched Errors', model=project.models[0], x=np.array([0.3, 0.4]), y=np.array([3.0, 4.0]), ye=np.array([0.5])),
    ]
    project._experiments = project.experiments
    logic = summary_module.Summary(project)
    fake_pyplot = FakePyplot()
    monkeypatch.setattr(logic, '_plt', lambda: fake_pyplot)
    monkeypatch.setattr(logic, '_gridspec', lambda: FakeGridSpecModule)

    figure = logic.make_plot(10.0, 8.0)
    reflectivity_axis = figure.axes[0]
    assert reflectivity_axis.errorbar_calls == []
    assert len(reflectivity_axis.plot_calls) == 4

    project.experiments = []
    project._experiments = []
    project.sample_data_for_model_at_index = lambda index: SimpleNamespace(x=np.array([0.1, 0.2]), y=np.array([2.0, 3.0]))
    project.sld_data_for_model_at_index = lambda index: SimpleNamespace(x=np.array([]), y=np.array([]))
    figure = logic.make_plot(10.0, 8.0)
    reflectivity_axis = figure.axes[0]
    assert reflectivity_axis.legend_called is True


def test_summary_make_plot_skips_empty_series_and_does_not_add_legend_without_reflectivity(tmp_path, monkeypatch):
    monkeypatch.setattr(summary_module, 'SummaryLib', FakeSummaryLib)
    project = make_project(models=make_model_collection(make_model(name='Model A', color='')))
    project.path = tmp_path / 'empty-plots'
    project.experiments = []
    project._experiments = []
    project.sample_data_for_model_at_index = lambda index: SimpleNamespace(x=np.array([]), y=np.array([]))
    project.sld_data_for_model_at_index = lambda index: SimpleNamespace(x=np.array([]), y=np.array([]))
    logic = summary_module.Summary(project)
    fake_pyplot = FakePyplot()
    monkeypatch.setattr(logic, '_plt', lambda: fake_pyplot)
    monkeypatch.setattr(logic, '_gridspec', lambda: FakeGridSpecModule)

    figure = logic.make_plot(10.0, 8.0)
    reflectivity_axis = figure.axes[0]

    assert reflectivity_axis.plot_calls == []
    assert reflectivity_axis.errorbar_calls == []
    assert reflectivity_axis.legend_called is False
