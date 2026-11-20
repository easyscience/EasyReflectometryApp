import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / 'EasyReflectometryApp' / 'Gui'
ANALYSIS = GUI / 'Pages' / 'Analysis'


def _read(path: Path) -> str:
    return path.read_text(encoding='utf-8')


def test_status_bar_shows_short_progress_and_hides_final_chi2_while_running():
    status_bar_qml = _read(GUI / 'StatusBar.qml')

    assert "keyText: qsTr('Fit')" in status_bar_qml
    assert 'visible: Globals.BackendWrapper.analysisFittingRunning' in status_bar_qml
    assert 'FitProgressText.statusText(Globals.BackendWrapper.analysisFitProgress)' in status_bar_qml
    # Calculator and Minimizer make room while a run is active
    assert status_bar_qml.count('visible: !Globals.BackendWrapper.analysisFittingRunning\n') == 2
    # The final chi² (or a kept cancelled fit's) is hidden while a run is active
    assert ('!Globals.BackendWrapper.analysisFittingRunning && '
            '(Globals.BackendWrapper.analysisFitChi2 > 0 || isCancelled)') in status_bar_qml
    # The run kind comes from the progress map, not from the editable minimizer selection
    assert 'analysisIsBayesianSelected' not in status_bar_qml


def test_fit_status_dialog_stays_results_only():
    dialog_qml = _read(ANALYSIS / 'Sidebar' / 'Basic' / 'Popups' / 'FitStatusDialog.qml')

    assert 'visible: Globals.BackendWrapper.analysisShowFitResultsDialog' in dialog_qml
    assert 'standardButtons: Dialog.Ok' in dialog_qml
    assert 'Refinement Running' not in dialog_qml
    assert 'Globals.BackendWrapper.analysisStopFit()' not in dialog_qml
    assert 'analysisFitProgress' not in dialog_qml


def test_fit_buttons_toggle_between_start_and_cancel_via_start_stop_action():
    layout_qml = _read(ANALYSIS / 'Layout.qml')
    fitting_group_qml = _read(ANALYSIS / 'Sidebar' / 'Basic' / 'Groups' / 'Fitting.qml')

    label = (
        "Globals.BackendWrapper.analysisFittingRunning ? qsTr('Cancel fitting') : "
        "(Globals.BackendWrapper.analysisIsBayesianSelected ? qsTr('Start sampling') : qsTr('Start fitting'))"
    )
    assert label in layout_qml
    assert 'Globals.BackendWrapper.analysisFittingStartStop()' in layout_qml
    assert label in fitting_group_qml
    assert 'Globals.BackendWrapper.analysisFittingStartStop()' in fitting_group_qml


def test_fit_status_dialog_is_loaded_once_at_stable_page_scope():
    layout_qml = _read(ANALYSIS / 'Layout.qml')
    fitting_group_qml = _read(ANALYSIS / 'Sidebar' / 'Basic' / 'Groups' / 'Fitting.qml')

    assert "source: 'Sidebar/Basic/Popups/FitStatusDialog.qml'" in layout_qml
    assert 'FitStatusDialog.qml' not in fitting_group_qml


def test_progress_is_shown_in_the_footer_and_the_strip_not_the_basic_group():
    layout_qml = _read(ANALYSIS / 'Layout.qml')
    fitting_group_qml = _read(ANALYSIS / 'Sidebar' / 'Basic' / 'Groups' / 'Fitting.qml')
    window_qml = _read(GUI / 'ApplicationWindow.qml')

    # Footer: under both sidebar tabs, with the detailed text and a clock for the elapsed time
    assert 'Gui.FitProgressBar {' in layout_qml
    assert 'FitProgressText.detailText(fitFooter.progress, fitFooter.now)' in layout_qml
    assert 'running: fitFooter.active' in layout_qml
    # The placeholder bar (a fixed 50 %) and its label are gone from the Basic group
    assert 'ProgressBar' not in fitting_group_qml
    assert 'analysisFitProgressMessage' not in fitting_group_qml
    # Strip: a sibling of the status bar, hidden with it on the Home page
    assert 'Gui.FitProgressBar {' in window_qml
    assert "visible: progress.phase !== '' && EaGlobals.Vars.appBarCurrentIndex !== 0" in window_qml
    assert 'FitProgressBar FitProgressBar.qml' in _read(GUI / 'qmldir')


def test_the_progress_map_is_mirrored_in_the_wrapper_and_the_mock():
    wrapper = _read(GUI / 'Globals' / 'BackendWrapper.qml')
    mock = _read(ROOT / 'EasyReflectometryApp' / 'Backends' / 'Mock' / 'Analysis.qml')

    assert 'readonly property var analysisFitProgress: activeBackend.analysis.fitProgress' in wrapper
    assert "readonly property var fitProgress: ({ phase: ''" in mock
    # The per-tick properties the map replaced are gone
    for removed in ('analysisFitIteration', 'analysisFitProgressMessage', 'analysisSampleProgress'):
        assert removed not in wrapper


# Runtime check of FitProgressBar.qml and Logic/FitProgressText.js in a real QML engine.
# A QGuiApplication cannot coexist with the QCoreApplication the other tests share,
# so the harness runs in a subprocess (as in test_qml_close_behaviour.py).
HARNESS = textwrap.dedent(
    '''
    import json
    import os
    import sys
    from pathlib import Path

    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    import EasyApplication

    gui = Path(sys.argv[1])

    QML = """
    import QtQuick
    import Gui as Gui
    import "%s" as T

    Window {
        width: 200
        height: 20
        visible: true

        Gui.FitProgressBar { id: half; width: 200; progress: ({ phase: 'sampling', fraction: 0.5 }) }
        Gui.FitProgressBar { id: over; width: 200; progress: ({ phase: 'sampling', fraction: 1.2 }) }
        Gui.FitProgressBar { id: busy; width: 200; progress: ({ phase: 'fitting', fraction: -1 }) }
        Gui.FitProgressBar { id: stopping; width: 200; progress: ({ phase: 'cancelling', fraction: -1 }) }

        readonly property var fit: ({ phase: 'fitting', kind: 'fit', fraction: -1, count: 132, total: 1000,
                                      unit: 'evaluations', reducedChi2: 1.23456, startedAtMs: 0 })
        readonly property var bumps: ({ phase: 'fitting', kind: 'fit', fraction: -1, count: 7, total: 0,
                                        unit: 'steps', reducedChi2: 2, startedAtMs: 0 })
        readonly property var burn: ({ phase: 'burn', kind: 'sample', fraction: 0.184, count: 400, total: 2171,
                                       unit: 'generations', reducedChi2: 0, startedAtMs: 0 })
        readonly property var noTotal: ({ phase: 'sampling', kind: 'sample', fraction: -1, count: 50, total: 0,
                                          unit: 'generations', reducedChi2: 0, startedAtMs: 0 })
        readonly property var starting: ({ phase: 'starting', kind: 'sample', fraction: -1, count: 0, total: 0,
                                           unit: 'generations', reducedChi2: 0, startedAtMs: 0 })
        readonly property var cancelling: ({ phase: 'cancelling', kind: 'fit', fraction: -1, count: 9, total: 0,
                                             unit: 'evaluations', reducedChi2: 1, startedAtMs: 0 })

        readonly property var report: ({
                halfFill: half.children[0].width,
                overFill: over.children[0].width,
                busyFill: busy.children[0].width,
                busySweep: busy.sweep,
                halfSweepRunning: half.indeterminate,
                stoppingOpacity: stopping.opacity,
                status: [T.statusText(fit), T.statusText(bumps), T.statusText(burn), T.statusText(noTotal),
                         T.statusText(starting), T.statusText(cancelling)],
                detail: [T.detailText(fit, 42000), T.detailText(burn, 3723000), T.detailText(starting, 3000),
                         T.detailText(cancelling, 5000)],
        })
    }
    """ % (gui / 'Logic' / 'FitProgressText.js').as_uri()

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(gui.parent))
    engine.addImportPath(str(Path(EasyApplication.__path__[0]).parent))
    engine.loadData(QML.encode(), QUrl.fromLocalFile(str(gui / 'harness.qml')))
    if not engine.rootObjects():
        print('HARNESS: QML failed to load')
        sys.exit(2)
    window = engine.rootObjects()[0]
    sweeps = []

    def report():
        value = window.property('report')
        return value.toVariant() if hasattr(value, 'toVariant') else dict(value)

    def sample_sweep():
        sweeps.append(report()['busySweep'])

    def finish():
        result = report()
        result['sweeps'] = sweeps
        print('RESULT ' + json.dumps(result), flush=True)
        app.quit()

    QTimer.singleShot(200, sample_sweep)
    QTimer.singleShot(500, sample_sweep)
    QTimer.singleShot(600, finish)
    QTimer.singleShot(10000, lambda: (print('HARNESS: timed out'), os._exit(3)))
    sys.exit(app.exec())
    '''
)


def test_progress_bar_and_text_in_a_qml_engine(tmp_path):
    pytest.importorskip('PySide6.QtQml')
    pytest.importorskip('EasyApplication')
    script = tmp_path / 'progress_harness.py'
    script.write_text(HARNESS, encoding='utf-8')
    environment = dict(os.environ)
    environment.setdefault('QT_QPA_PLATFORM', 'offscreen')
    environment.setdefault('QT_QUICK_BACKEND', 'software')
    # Without a console, Qt on Windows logs to the debugger instead of stderr.
    environment['QT_FORCE_STDERR_LOGGING'] = '1'

    completed = subprocess.run(  # noqa: S603 - our own interpreter running our own script
        [sys.executable, str(script), str(GUI)],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=60,
        env=environment,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    result = json.loads(completed.stdout.split('RESULT ', 1)[1].splitlines()[0])

    # Qt reports QML warnings (bad bindings, unknown properties) on stderr
    assert [line for line in completed.stderr.splitlines() if 'FitProgress' in line or 'harness' in line] == []
    # A known fraction fills that share of the track, never more than all of it
    assert result['halfFill'] == 100
    assert result['overFill'] == 200
    assert result['halfSweepRunning'] is False
    # An unknown fraction sweeps a quarter-width segment across the track
    assert result['busyFill'] == 50
    assert result['sweeps'][0] != result['sweeps'][1]
    assert result['stoppingOpacity'] < 1

    assert result['status'] == [
        '132 evaluations · reduced χ² 1.2346',
        '7 steps · reduced χ² 2.0000',
        'Burn-in 18 %',
        'Sampling · generation 50',
        'Sampling…',
        'Cancelling…',
    ]
    assert result['detail'] == [
        'Fitting · 132 of max 1000 evaluations · 0:42\nreduced χ² 1.2346',
        'Burn-in · generation 400 of 2171 · 1:02:03',
        'Sampling… · 0:03',
        'Cancelling…',
    ]
