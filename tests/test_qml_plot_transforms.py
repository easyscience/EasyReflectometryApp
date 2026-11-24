"""Runtime check that the reflectivity charts keep their data in view across plot transforms (#393).

With several experiments selected, the Experiment and Analysis charts draw one series per
experiment, created and filled in QML. A plot-mode change (R(q)×q⁴, linear/log R axis) must refill
those series too: the backend only refills the series it holds, so they once kept the previous
transform's values under the new axis range, and the plot stayed empty until a log-q toggle
rebuilt them.

This loads both real views with the real backend and a shipped multi-contrast example, steps
through the transforms, and counts the points of every drawn series that land inside the plot
area. A QApplication cannot coexist with the QCoreApplication the other tests share, so the
harness runs in a subprocess (as in test_qml_close_behaviour.py).
"""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / 'EasyReflectometryApp'

HARNESS = textwrap.dedent(
    '''
    import json
    import os
    import sys
    from pathlib import Path

    sys.stdout.reconfigure(encoding='utf-8')
    app_dir = Path(sys.argv[1])
    sys.path.insert(0, str(app_dir))

    import EasyApplication
    from PySide6.QtCore import QObject, QTimer, QUrl, qInstallMessageHandler
    from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType
    from PySide6.QtWidgets import QApplication

    QML = """
    import QtQuick
    import Gui.Globals as Globals

    Window {
        width: 1600
        height: 700
        visible: true

        Row {
            anchors.fill: parent
            Loader { width: 800; height: 700; source: "%s" }
            Loader { width: 800; height: 700; source: "%s" }
        }

        function charts() {
            return {
                experiment: Globals.References.pages.experiment.mainContent.experimentView,
                analysis: Globals.References.pages.analysis.mainContent.analysisView,
            }
        }

        function act(action) {
            if (action === 'load') Globals.BackendWrapper.projectLoadExample(examplePath)
            else if (action === 'select all') Globals.BackendWrapper.analysisSetSelectedExperimentIndices([0, 1, 2])
            else if (action === 'toggle rq4') Globals.BackendWrapper.plottingTogglePlotRQ4()
            else if (action === 'toggle log R') Globals.BackendWrapper.plottingToggleYAxisLog()
            else if (action === 'log q on') Globals.Variables.logarithmicQAxis = true
            else if (action === 'log q off') Globals.Variables.logarithmicQAxis = false
            else if (action === 'reset views') { charts().experiment.resetAxes(); charts().analysis.resetAxes() }
        }

        // Per drawn series: how many of its points land inside the plot area.
        function measure() {
            const result = {}
            const views = charts()
            for (const view in views) {
                const chart = views[view]
                const area = chart.plotArea
                const series = []
                for (let i = 0; i < chart.count; i++) {
                    const serie = chart.series(i)
                    if (!serie.visible || serie.count === 0) continue
                    let inside = 0
                    for (let j = 0; j < serie.count; j++) {
                        const pos = chart.mapToPosition(serie.at(j), serie)
                        if (pos.x >= area.x && pos.x <= area.x + area.width
                                && pos.y >= area.y && pos.y <= area.y + area.height) inside++
                    }
                    series.push({ name: serie.name, inside: inside, count: serie.count })
                }
                result[view] = series
            }
            return result
        }
    }
    """ % tuple((app_dir / 'Gui' / 'Pages' / page).as_uri() for page in
                ('Experiment/MainContent/ExperimentView.qml', 'Analysis/MainContent/CombinedView.qml'))

    STEPS = [
        'load', 'select all',
        'toggle rq4', 'toggle rq4',                                # R(q)×q⁴ on and off, linear q
        'log q on', 'toggle rq4', 'toggle rq4', 'reset views',     # the same on a log q axis
        'toggle log R', 'toggle log R', 'log q off',               # linear R and back
    ]
    # Steps after which the drawn data is checked (loading and selecting only set the stage).
    MEASURED_FROM = 2

    def report_warnings(mode, context, message):
        if 'ExperimentView.qml' in str(context.file) or 'CombinedView.qml' in str(context.file):
            if mode.name != 'QtDebugMsg':
                print(f'QMLWARNING {Path(str(context.file)).name}:{context.line}: {message}', flush=True)

    qInstallMessageHandler(report_warnings)
    app = QApplication(sys.argv[:1])
    from Backends.Py import PyBackend

    backends = []
    # Before any QML engine exists (see main.py).
    qmlRegisterSingletonType(QObject, 'Backends', 1, 0, 'PyBackend',
                             lambda engine: backends.append(PyBackend()) or backends[-1])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('isTestMode', False)
    engine.rootContext().setContextProperty('examplePath', sys.argv[2])
    engine.addImportPath(str(app_dir))
    engine.addImportPath(str(Path(EasyApplication.__path__[0]).parent))
    engine.loadData(QML.encode(), QUrl.fromLocalFile(str(app_dir / 'Gui' / 'harness.qml')))
    if not engine.rootObjects():
        print('HARNESS: QML failed to load')
        sys.exit(2)
    window = engine.rootObjects()[0]
    results = []

    def call(name, *args):
        from PySide6.QtCore import Q_ARG, Q_RETURN_ARG, QMetaObject
        if args:
            QMetaObject.invokeMethod(window, name, Q_ARG('QVariant', args[0]))
            return None
        value = QMetaObject.invokeMethod(window, name, Q_RETURN_ARG('QVariant'))
        return value.toVariant() if hasattr(value, 'toVariant') else value

    def step(index):
        if index == len(STEPS):
            print('RESULT ' + json.dumps(results), flush=True)
            app.quit()
            return
        # The action runs to completion before the wait starts: the charts redraw synchronously,
        # and only their 75 ms axis reset is deferred.
        call('act', STEPS[index])
        QTimer.singleShot(1500 if index == 0 else 500, lambda: measure(index))

    def measure(index):
        if index >= MEASURED_FROM:
            results.append({'after': ' > '.join(STEPS[MEASURED_FROM:index + 1]), 'views': call('measure')})
        step(index + 1)

    QTimer.singleShot(500, lambda: step(0))
    QTimer.singleShot(120000, lambda: (print('HARNESS: timed out'), os._exit(3)))
    sys.exit(app.exec())
    '''
)


def test_multi_experiment_charts_keep_their_data_in_view_across_plot_transforms(tmp_path):
    pytest.importorskip('PySide6.QtCharts')
    pytest.importorskip('EasyApplication')
    script = tmp_path / 'plot_transforms_harness.py'
    script.write_text(HARNESS, encoding='utf-8')
    environment = dict(os.environ)
    environment.setdefault('QT_QPA_PLATFORM', 'offscreen')
    environment.setdefault('QT_QUICK_BACKEND', 'software')

    completed = subprocess.run(  # noqa: S603 - our own interpreter running our own script
        [sys.executable, str(script), str(APP), str(APP / 'Examples' / 'FilmContrasts' / 'project.json')],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=180,
        env=environment,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output[-4000:]
    assert [line for line in completed.stdout.splitlines() if line.startswith('QMLWARNING')] == []
    results = json.loads(completed.stdout.split('RESULT ', 1)[1].splitlines()[0])

    assert len(results) == 9
    for result in results:
        for view, series in result['views'].items():
            measured = [serie for serie in series if serie['name'].endswith((' - Data', ' - Measured'))]
            # One series per selected experiment, on both pages.
            assert len(measured) == 3, (result['after'], view, series)
            for serie in series:
                # Nearly every point in view (the Analysis axis follows the calculated curves,
                # which a few measured points at the reflectivity edge overshoot); a stale
                # series has none.
                assert serie['inside'] >= 0.9 * serie['count'], (result['after'], view, serie)
