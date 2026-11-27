"""The tutorial backend part (Backends/Py/tutorial.py): its wiring to the other parts, with stub
parts, and one run against the real backend and the shipped example."""

import time
from pathlib import Path
from types import SimpleNamespace

import pytest
from easyscience import global_object
from PySide6.QtCore import QCoreApplication
from PySide6.QtCore import QObject
from PySide6.QtCore import Signal

from EasyReflectometryApp.Backends.Py import tutorial as tutorial_module
from EasyReflectometryApp.Backends.Py.tutorial import SESSION_REPLACED
from EasyReflectometryApp.Backends.Py.tutorial import Tutorial


@pytest.fixture
def clear_global_map():
    """A real backend registers its objects by name; another one in the same process collides."""
    global_object.registry.clear()
    yield
    global_object.registry.clear()


class StubProject(QObject):
    sessionReplaced = Signal()
    externalCreatedChanged = Signal()
    externalNameChanged = Signal()
    isExample = True
    created = False
    name = 'Example'


class StubSample(QObject):
    modelsTableChanged = Signal()
    assembliesIndexChanged = Signal()
    externalSampleChanged = Signal()
    modelsNames = ['Film']
    currentAssemblyName = 'Superphase'
    assembliesNames = ['Superphase', 'Film', 'Subphase']
    materials = [{'label': 'Si', 'sld': '2.07'}, {'label': 'Film', 'sld': '2.0'}]
    layers = [{'label': 'Film', 'material': 'Film', 'thickness': '250.0', 'roughness': '3.0'}]


class StubPlotting(QObject):
    magneticProfileChanged = Signal()
    visibleSldCurves = ['spin_up', 'spin_down']


class StubAnalysis(QObject):
    fittingChanged = Signal()
    prefitCheckFailed = Signal(str, str)
    parametersChanged = Signal()
    minimizerChanged = Signal()
    experimentsChanged = Signal()

    def __init__(self):
        super().__init__()
        self.fittingRunning = False
        self.fitSuccess = False
        self.fitCancelled = False
        self.fitChi2 = 0.0
        self.showFitResultsDialog = False
        self.experimentsAvailable = ['data']
        self.experimentsModelIndices = [0]
        self.freeParametersCount = 1
        self.thickness = 250.0
        self._parameters_logic = SimpleNamespace(
            all_parameters=lambda: [{'alias': 'film_thickness', 'value': self.thickness, 'fit': True}]
        )

    def end_fit(self, success=False, cancelled=False):
        self.fittingRunning = True
        self.fittingChanged.emit()
        self.fittingRunning, self.fitSuccess, self.fitCancelled = False, success, cancelled
        self.fittingChanged.emit()


def _step(step_id, done='', advance=False, hint=''):
    return {
        'id': step_id,
        'title': step_id,
        'body': '',
        'page': 'analysis',
        'sidebarTab': '',
        'target': '',
        'done': done,
        'actions': [],
        'advance': advance,
        'requires': '',
        'hint': hint,
        'more': '',
    }


def _tutorial(qcore_application, *steps):
    project, analysis = StubProject(), StubAnalysis()
    part = Tutorial(project, StubSample(), analysis, SimpleNamespace(minimizer='Bumps_lm'), StubPlotting())
    part._tutorials['test'] = {'id': 'test', 'title': 'Test', 'examplePath': '/x/project.json', 'steps': list(steps)}
    part.start('test')
    return part, project, analysis


def _wait(predicate, seconds=5.0):
    deadline = time.monotonic() + seconds
    while not predicate() and time.monotonic() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.01)
    return predicate()


def test_the_shipped_tutorials_are_offered(qcore_application):
    part = Tutorial(StubProject(), StubSample(), StubAnalysis(), SimpleNamespace(minimizer=''), StubPlotting())

    assert part.available, 'no tutorials shipped'
    for tutorial in part.available:
        assert set(tutorial) == {'id', 'title', 'summary', 'minutes', 'examplePath'}
        # '' for a tutorial that starts from an empty project
        assert tutorial['examplePath'] == '' or Path(tutorial['examplePath']).is_file(), tutorial['id']
    assert part.state == 'idle' and part.step == {}


def test_a_successful_fit_completes_a_fit_step(qcore_application):
    part, _, analysis = _tutorial(qcore_application, _step('fit', done='step.fits_finished >= 1'))

    analysis.end_fit(success=True)

    assert part.step['state'] == 'done' and part.step['canNext']


@pytest.mark.parametrize('outcome', ['cancelled', 'failed', 'refused'])
def test_other_fit_outcomes_show_the_hint(qcore_application, outcome):
    part, _, analysis = _tutorial(qcore_application, _step('fit', done='step.fits_finished >= 1', hint='Again.'))

    if outcome == 'refused':
        analysis.prefitCheckFailed.emit('Invalid Parameter Bounds', 'min > max')
    else:
        analysis.end_fit(cancelled=outcome == 'cancelled')

    assert part.step['state'] == 'waiting' and part.step['message'] == 'Again.'


def test_a_parameter_change_is_checked_at_once(qcore_application):
    part, _, analysis = _tutorial(qcore_application, _step('value', done="abs(params.value('film_thickness') - 200) < 5"))

    analysis.thickness = 200.0
    analysis.parametersChanged.emit()

    assert part.step['state'] == 'done'


def test_replacing_the_session_stops_the_tutorial(qcore_application):
    part, project, _ = _tutorial(qcore_application, _step('read'))

    project.sessionReplaced.emit()

    assert part.state == 'stopped' and part.stopReason == SESSION_REPLACED


def test_a_navigation_step_moves_on_by_itself(qcore_application, monkeypatch):
    monkeypatch.setattr(tutorial_module, 'AUTO_ADVANCE_MS', 10)
    part, _, _ = _tutorial(qcore_application, _step('open', done="ui.page == 'analysis'", advance=True), _step('read'))

    part.reportUi('page', 'analysis')

    assert _wait(lambda: part.stepIndex == 1)


def test_finishing_without_a_skip_reports_the_tutorial_completed_once(qcore_application):
    part, _, analysis = _tutorial(qcore_application, _step('fit', done='step.fits_finished >= 1'), _step('read'))
    completed = []
    part.completed.connect(completed.append)

    analysis.end_fit(success=True)
    part.next()
    part.next()
    analysis.end_fit(success=True)  # after the end: nothing more

    assert part.state == 'finished' and completed == ['test']


def test_finishing_after_a_skip_is_not_completed(qcore_application):
    part, _, _ = _tutorial(qcore_application, _step('fit', done='step.fits_finished >= 1'), _step('read'))
    completed = []
    part.completed.connect(completed.append)

    part.skip()
    part.next()

    assert part.state == 'finished' and completed == []


def test_stop_closes_the_tutorial(qcore_application):
    part, _, _ = _tutorial(qcore_application, _step('read'))

    part.stop()

    assert part.state == 'idle' and part.stepCount == 0


def test_the_pilot_with_the_real_backend(qcore_application, clear_global_map):
    from EasyReflectometryApp.Backends.Py.py_backend import PyBackend

    backend = PyBackend()
    part, analysis = backend.tutorial, backend.analysis
    backend.project.loadExample(part.available[0]['examplePath'])
    part.start('simple-fitting')
    part.next()  # the sample
    part.reportUi('page', 'analysis')
    part.next()  # open the Analysis page, without waiting for it to move on by itself
    part.next()  # compare
    part.next()  # the parameters
    assert part.step['id'] == 'start-fit' and part.step['state'] == 'waiting'

    # The table filter does not change what a condition reads.
    analysis.setVariabilityFilterCriteria('fixed')
    assert part._facts()['params'].value('polymer_film_film_thickness') == pytest.approx(250.0)

    analysis.fittingStartStop()
    assert _wait(lambda: not analysis.fittingRunning, seconds=60)
    assert part.step['state'] == 'done'

    backend.project.reset()
    assert part.state == 'stopped'


def test_sample_and_plot_facts_follow_their_signals(qcore_application):
    part, _, _ = _tutorial(
        qcore_application,
        _step('film', done="sample.assembly == 'Fe film'"),
        _step('curve', done="plot.sld_curves.count('rho_m') == 1"),
    )
    sample, plotting = part._sample, part._plotting

    sample.currentAssemblyName = 'Fe film'
    sample.assembliesIndexChanged.emit()
    assert part.step['state'] == 'done'

    part.next()
    plotting.visibleSldCurves = ['spin_up', 'spin_down', 'rho_m']
    plotting.magneticProfileChanged.emit()
    assert part.step['state'] == 'done'


def test_the_sample_view_is_a_ui_fact(qcore_application):
    part, _, _ = _tutorial(qcore_application, _step('structure', done="ui.sample_view == 'structure'"))

    part.reportUi('sample_view', 'structure')

    assert part.step['state'] == 'done'


def test_material_and_layer_facts(qcore_application):
    part, _, _ = _tutorial(
        qcore_application,
        _step('material', done="abs(sample.material_slds.get('dPS', 0) - 6.4) < 0.05"),
        _step(
            'layer',
            done="len(sample.layers) >= 2 and sample.layers[-1].material == 'dPS' and sample.layers[-1].thickness == 50",
        ),
    )
    sample = part._sample
    # A material that is not there yet reads as absent, not as an error.
    assert part.step['state'] == 'waiting'

    sample.materials = [*StubSample.materials, {'label': 'dPS', 'sld': '6.4'}]
    sample.externalSampleChanged.emit()
    assert part.step['state'] == 'done'

    part.next()
    sample.layers = [*StubSample.layers, {'label': 'dPS Layer', 'material': 'dPS', 'thickness': '50.0', 'roughness': '3.3'}]
    sample.externalSampleChanged.emit()
    assert part.step['state'] == 'done'


def test_a_sample_import_does_not_stop_a_tutorial(qcore_application, clear_global_map):
    # Loading a sample from a file replaces the models, not the session: a tutorial may ask for it.
    from EasyReflectometryApp.Backends.Py.logic.tutorial import DATA_DIR
    from EasyReflectometryApp.Backends.Py.py_backend import PyBackend

    backend = PyBackend()
    part = backend.tutorial
    part.start(part.available[0]['id'])

    backend.project.sampleLoad((DATA_DIR / 'film_contrasts.ort').as_posix(), False)
    assert part.state == 'active'

    backend.project.reset()
    assert part.state == 'stopped'
