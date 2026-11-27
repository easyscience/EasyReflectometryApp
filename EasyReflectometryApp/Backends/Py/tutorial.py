"""The interactive tutorial as seen from QML: the run of logic.tutorial wired to the other backend parts.

See MD/INTERACTIVE_TUTORIALS_DESIGN.md. QML loads the tutorial's example first (through
`replaceSessionWithExample` in ApplicationWindow.qml) and then calls `start`; it performs the
**Show me** actions itself and reports the UI state the conditions read with `reportUi`.
"""

from types import SimpleNamespace

from PySide6.QtCore import Property
from PySide6.QtCore import QObject
from PySide6.QtCore import QTimer
from PySide6.QtCore import Signal
from PySide6.QtCore import Slot

from .logic.tutorial import ParameterFacts
from .logic.tutorial import TutorialRun
from .logic.tutorial import available_tutorials

SESSION_REPLACED = 'Another project was loaded or the app was reset, so the tutorial stopped.'
AUTO_ADVANCE_MS = 1000


class Tutorial(QObject):
    changed = Signal()
    # A tutorial finished without a skipped step; QML saves its id in the settings file.
    completed = Signal(str)

    def __init__(self, project, sample, analysis, status, plotting, parent=None):
        super().__init__(parent)
        self._project = project
        self._sample = sample
        self._analysis = analysis
        self._status = status
        self._plotting = plotting
        self._tutorials = {tutorial['id']: tutorial for tutorial in available_tutorials()}
        self._run = None
        # Kept between runs: QML reports changes only.
        self._ui = {'page': 'home', 'plot_tab': 'sld', 'sample_view': 'reflectivity'}
        self._fit_was_running = False

        self._auto_advance = QTimer(self)
        self._auto_advance.setSingleShot(True)
        self._auto_advance.setInterval(AUTO_ADVANCE_MS)
        self._auto_advance.timeout.connect(self._advance_automatically)

        project.externalProjectLoaded.connect(self._on_session_replaced)
        project.externalProjectReset.connect(self._on_session_replaced)
        analysis.fittingChanged.connect(self._on_fitting_changed)
        analysis.prefitCheckFailed.connect(lambda _title, _message: self._on_fit_ended('refused'))
        for signal in (
            analysis.parametersChanged,
            analysis.minimizerChanged,
            analysis.experimentsChanged,
            sample.modelsTableChanged,
            sample.assembliesIndexChanged,
            sample.externalSampleChanged,  # magnetism and other sample edits
            plotting.magneticProfileChanged,  # the magnetic curves shown
            project.externalCreatedChanged,
            project.externalNameChanged,
        ):
            signal.connect(self._evaluate)

    # QML interface

    @Property('QVariantList', constant=True)
    def available(self) -> list[dict]:
        """[{id, title, summary, minutes, examplePath}] in display order."""
        return [
            {key: tutorial[key] for key in ('id', 'title', 'summary', 'minutes', 'examplePath')}
            for tutorial in self._tutorials.values()
        ]

    @Property(str, notify=changed)
    def state(self) -> str:
        """idle | active | finished | stopped"""
        return self._run.state if self._run else 'idle'

    @Property(str, notify=changed)
    def stopReason(self) -> str:
        return self._run.stop_reason if self._run else ''

    @Property(str, notify=changed)
    def tutorialId(self) -> str:
        return self._run.definition['id'] if self._run else ''

    @Property(str, notify=changed)
    def title(self) -> str:
        return self._run.definition['title'] if self._run else ''

    @Property(str, notify=changed)
    def examplePath(self) -> str:
        return self._run.definition['examplePath'] if self._run else ''

    @Property(int, notify=changed)
    def stepIndex(self) -> int:
        return self._run.index if self._run else 0

    @Property(int, notify=changed)
    def stepCount(self) -> int:
        return len(self._run.steps) if self._run else 0

    @Property('QVariantMap', notify=changed)
    def step(self) -> dict:
        if self._run is None:
            return {}
        step = self._run.step
        return {
            **{
                key: step[key] for key in ('id', 'title', 'body', 'page', 'sidebarTab', 'target', 'actions', 'advance', 'more')
            },
            'hasCondition': bool(step['done']),
            'state': self._run.step_state,
            'message': self._run.message,
            'canNext': self._run.can_next,
            'isLast': self._run.index == len(self._run.steps) - 1,
        }

    @Slot(str)
    def start(self, tutorial_id: str) -> None:
        """Start a tutorial whose example QML has just loaded."""
        self._run = TutorialRun(self._tutorials[tutorial_id], self._facts)
        self._fit_was_running = self._analysis.fittingRunning
        self._after_change()

    @Slot()
    def stop(self) -> None:
        self._run = None
        self._after_change()

    @Slot()
    def next(self) -> None:
        if self._run and self._run.next():
            if self._run.completed:
                self.completed.emit(self._run.definition['id'])
            self._after_change()

    @Slot()
    def previous(self) -> None:
        if self._run:
            self._run.previous()
            self._after_change()

    @Slot()
    def skip(self) -> None:
        if self._run:
            self._run.skip()
            self._after_change()

    @Slot(str, str)
    def reportUi(self, key: str, value: str) -> None:
        """`ui.<key>` changed in the GUI ('page', 'plot_tab', 'sample_view')."""
        if self._ui.get(key) != value:
            self._ui[key] = value
            self._evaluate()

    # Facts and events

    def _facts(self) -> dict:
        project, sample, analysis = self._project, self._sample, self._analysis
        return {
            'ui': SimpleNamespace(**self._ui),
            'project': SimpleNamespace(is_example=project.isExample, created=project.created, name=project.name),
            'models': SimpleNamespace(count=len(sample.modelsNames), names=list(sample.modelsNames)),
            'sample': SimpleNamespace(assembly=sample.currentAssemblyName),
            'plot': SimpleNamespace(sld_curves=list(self._plotting.visibleSldCurves)),
            'experiments': SimpleNamespace(
                count=len(analysis.experimentsAvailable), names=list(analysis.experimentsAvailable)
            ),
            'params': ParameterFacts(analysis.freeParametersCount, analysis._parameters_logic.all_parameters),
            'fit': SimpleNamespace(
                running=analysis.fittingRunning,
                minimizer=self._status.minimizer,
                reduced_chi2=analysis.fitChi2,
                success=analysis.fitSuccess,
                cancelled=analysis.fitCancelled,
                results_dialog_open=analysis.showFitResultsDialog,
            ),
        }

    def _evaluate(self) -> None:
        if self._run and self._run.state == 'active':
            self._run.evaluate()
            self._after_change()

    def _on_fitting_changed(self) -> None:
        running = self._analysis.fittingRunning
        if self._fit_was_running and not running:
            if self._analysis.fitSuccess:
                self._on_fit_ended('finished')
            else:
                self._on_fit_ended('cancelled' if self._analysis.fitCancelled else 'failed')
        else:
            self._evaluate()  # e.g. the results dialog was closed
        self._fit_was_running = running

    def _on_fit_ended(self, outcome: str) -> None:
        if self._run:
            self._run.fit_ended(outcome)
            self._after_change()

    def _on_session_replaced(self) -> None:
        if self._run:
            self._run.stop(SESSION_REPLACED)
            self._after_change()

    def _after_change(self) -> None:
        if self._run and self._run.auto_advance:
            if not self._auto_advance.isActive():
                self._auto_advance.start()
        else:
            self._auto_advance.stop()
        self.changed.emit()

    def _advance_automatically(self) -> None:
        if self._run and self._run.auto_advance:
            self.next()
