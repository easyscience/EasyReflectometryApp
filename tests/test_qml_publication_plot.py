"""Runtime check of the publication-style reflectivity charts (#401).

Testers asked for the R(q) plot to be closer to publication-ready:

- a frame on all four sides of the plot area (PlotFrame), not only the left and bottom axis lines;
- minor ticks on the logarithmic q-axis (2×…9× of each decade, and between the fractional-base
  ticks LogQAxis switches to when zoomed inside one decade);
- an adjustable measured-data marker size (Globals.Variables.experimentMarkerSize).

This loads the real Experiment and Analysis views with the real backend and a shipped
multi-contrast example and inspects the drawn charts. A QApplication cannot coexist with the
QCoreApplication the other tests share, so the harness runs in a subprocess (as in
test_qml_plot_transforms.py). Pass a directory as the harness's third argument to also save
screenshots of the charts.
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
    shots_dir = sys.argv[3] if len(sys.argv) > 3 else ''
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

        function measuredSeries(chart) {
            const found = []
            for (let i = 0; i < chart.count; i++) {
                const serie = chart.series(i)
                if (serie.visible && (serie.name.endsWith(' - Data') || serie.name.endsWith(' - Measured')))
                    found.push(serie)
            }
            return found
        }

        function act(action) {
            if (action === 'load') Globals.BackendWrapper.projectLoadExample(examplePath)
            else if (action === 'select all') Globals.BackendWrapper.analysisSetSelectedExperimentIndices([0, 1, 2])
            else if (action === 'marker size 2') Globals.Variables.experimentMarkerSize = 2.0
            else if (action === 'log q on') Globals.Variables.logarithmicQAxis = true
            else if (action === 'zoom in one decade') {
                const views = charts()
                for (const view in views) {
                    const axis = views[view].currentXAxis()
                    axis.min = 0.031
                    axis.max = 0.046
                }
            }
        }

        function measure() {
            const result = {}
            const views = charts()
            for (const view in views) {
                const chart = views[view]
                const area = chart.plotArea
                let frame = null
                for (let i = 0; i < chart.children.length; i++) {
                    const child = chart.children[i]
                    if (child.objectName === 'plotFrame')
                        frame = { x: child.x, y: child.y, width: child.width, height: child.height,
                                  border: child.border.width }
                }
                const measured = measuredSeries(chart)
                const axis = chart.currentXAxis()
                result[view] = {
                    plotArea: { x: area.x, y: area.y, width: area.width, height: area.height },
                    frame: frame,
                    markerSizes: measured.map(serie => serie.markerSize),
                    xAxis: axis ? { log: axis.base !== undefined, base: axis.base,
                                    minorTickCount: axis.minorTickCount, lineVisible: axis.lineVisible }
                                : null,
                }
            }
            return result
        }

        function shoot(dir, tag) {
            const views = charts()
            for (const view in views)
                views[view].grabToImage(r => r.saveToFile(dir + '/' + view + '_' + tag + '.png'))
        }
    }
    """ % tuple((app_dir / 'Gui' / 'Pages' / page).as_uri() for page in
                ('Experiment/MainContent/ExperimentView.qml', 'Analysis/MainContent/CombinedView.qml'))

    STEPS = ['load', 'select all', 'measure', 'marker size 2', 'log q on', 'measure',
             'zoom in one decade', 'measure']

    def report_warnings(mode, context, message):
        if any(name in str(context.file) for name in
               ('harness.qml', 'ExperimentView.qml', 'CombinedView.qml', 'PlotFrame.qml', 'LogQAxis.qml',
                'MeasuredScatter.js')):
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
            QMetaObject.invokeMethod(window, name, *(Q_ARG('QVariant', arg) for arg in args))
            return None
        value = QMetaObject.invokeMethod(window, name, Q_RETURN_ARG('QVariant'))
        return value.toVariant() if hasattr(value, 'toVariant') else value

    def step(index):
        if index == len(STEPS):
            print('RESULT ' + json.dumps(results), flush=True)
            # Let any screenshot grabs finish saving.
            QTimer.singleShot(500, app.quit)
            return
        if STEPS[index] == 'measure':
            results.append(call('measure'))
            if shots_dir:
                call('shoot', shots_dir, str(len(results)))
            QTimer.singleShot(300, lambda: step(index + 1))
            return
        call('act', STEPS[index])
        QTimer.singleShot(1500 if index == 0 else 500, lambda: step(index + 1))

    QTimer.singleShot(500, lambda: step(0))
    QTimer.singleShot(120000, lambda: (print('HARNESS: timed out'), os._exit(3)))
    sys.exit(app.exec())
    '''
)


def run_harness(tmp_path, shots_dir=None):
    script = tmp_path / 'publication_plot_harness.py'
    script.write_text(HARNESS, encoding='utf-8')
    environment = dict(os.environ)
    environment.setdefault('QT_QPA_PLATFORM', 'offscreen')
    environment.setdefault('QT_QUICK_BACKEND', 'software')
    arguments = [sys.executable, str(script), str(APP), str(APP / 'Examples' / 'FilmContrasts' / 'project.json')]
    if shots_dir:
        arguments.append(str(shots_dir))
    completed = subprocess.run(  # noqa: S603 - our own interpreter running our own script
        arguments,
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=180,
        env=environment,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output[-4000:]
    assert [line for line in completed.stdout.splitlines() if line.startswith('QMLWARNING')] == []
    return json.loads(completed.stdout.split('RESULT ', 1)[1].splitlines()[0])


def test_reflectivity_charts_are_framed_scaled_and_minor_ticked(tmp_path):
    pytest.importorskip('PySide6.QtCharts')
    pytest.importorskip('EasyApplication')
    linear, log, zoomed = run_harness(tmp_path, os.environ.get('ERA_PLOT_SHOTS'))

    for result in (linear, log, zoomed):
        for view, chart in result.items():
            # The frame covers the plot area exactly, on all four sides.
            assert chart['frame'] is not None, view
            for key in ('x', 'y', 'width', 'height'):
                assert chart['frame'][key] == pytest.approx(chart['plotArea'][key]), (view, key)
            assert chart['frame']['border'] == 1

    for view, chart in linear.items():
        # One measured series per selected experiment, dots at the default size.
        assert chart['markerSizes'] == [2, 2, 2], view

    for view, chart in log.items():
        # Marker size 2× applied to the recreated series.
        assert chart['markerSizes'] == [4, 4, 4], view
        # Decades: Qt's automatic 2…9 minor ticks; the frame replaces the axis line.
        assert chart['xAxis']['log'], view
        assert chart['xAxis']['base'] == pytest.approx(10), view
        assert chart['xAxis']['minorTickCount'] == -1, view
        assert chart['xAxis']['lineVisible'] is False, view

    for view, chart in zoomed.items():
        # Inside one decade: a fractional base, with explicit minor ticks between its ticks.
        assert chart['xAxis']['base'] < 10, view
        assert chart['xAxis']['minorTickCount'] == 4, view
