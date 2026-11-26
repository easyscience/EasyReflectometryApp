"""Runtime check that the Experiment chart shows only the current project's data after a reset.

Loading an example, resetting the project and loading another example once left the Experiment
chart wrong in two ways:

- On a log q axis the previous project's points stayed on screen next to the new ones: a project
  change re-registered the linear series with the backend and showed them, while the log-q series
  kept their old points.
- The axes kept the previous data's range, so the new data could be out of view until Home was
  clicked: an earlier axis reset (Home, a plot mode or log q toggle) had replaced the range
  bindings, and nothing fitted the axes to the new data.

This loads the real view with the real backend and shipped examples, and after each step reports
every drawn series and how many of its points land inside the plot area. A QApplication cannot
coexist with the QCoreApplication the other tests share, so the harness runs in a subprocess (as
in test_qml_plot_transforms.py).
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
    from PySide6.QtCore import QObject, QTimer, QUrl
    from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType
    from PySide6.QtWidgets import QApplication

    QML = """
    import QtQuick
    import Gui.Globals as Globals

    Window {
        width: 800
        height: 700
        visible: true

        Loader { anchors.fill: parent; source: "%s" }

        function chart() { return Globals.References.pages.experiment.mainContent.experimentView }

        function act(action) {
            if (action === 'load film') Globals.BackendWrapper.projectLoadExample(filmPath)
            else if (action === 'load polymer') Globals.BackendWrapper.projectLoadExample(polymerPath)
            else if (action === 'reset') Globals.BackendWrapper.projectReset()
            else if (action === 'home') chart().resetAxes()
            else if (action === 'log q on') Globals.Variables.logarithmicQAxis = true
            else if (action === 'log q off') Globals.Variables.logarithmicQAxis = false
        }

        // Per drawn series: its size and how many of its points land inside the plot area.
        function measure() {
            const view = chart()
            const area = view.plotArea
            const series = []
            for (let i = 0; i < view.count; i++) {
                const serie = view.series(i)
                if (!serie.visible || serie.count === 0) continue
                let inside = 0
                for (let j = 0; j < serie.count; j++) {
                    const pos = view.mapToPosition(serie.at(j), serie)
                    if (pos.x >= area.x && pos.x <= area.x + area.width
                            && pos.y >= area.y && pos.y <= area.y + area.height) inside++
                }
                series.push({ name: serie.name, inside: inside, count: serie.count })
            }
            return series
        }
    }
    """ % (app_dir / 'Gui' / 'Pages' / 'Experiment' / 'MainContent' / 'ExperimentView.qml').as_uri()

    STEPS = [
        'load film', 'home', 'log q on', 'reset', 'load polymer',  # the reported sequence, log q
        'log q off', 'reset', 'load film',                         # and again on a linear q axis
    ]

    app = QApplication(sys.argv[:1])
    from Backends.Py import PyBackend

    backends = []
    # Before any QML engine exists (see main.py).
    qmlRegisterSingletonType(QObject, 'Backends', 1, 0, 'PyBackend',
                             lambda engine: backends.append(PyBackend()) or backends[-1])
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('isTestMode', False)
    engine.rootContext().setContextProperty('filmPath', sys.argv[2])
    engine.rootContext().setContextProperty('polymerPath', sys.argv[3])
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
        call('act', STEPS[index])
        # Long enough for the deferred (75 ms) axis fit after a data change.
        QTimer.singleShot(800, lambda: measure(index))

    def measure(index):
        results.append({'after': ' > '.join(STEPS[:index + 1]), 'series': call('measure')})
        step(index + 1)

    QTimer.singleShot(500, lambda: step(0))
    QTimer.singleShot(120000, lambda: (print('HARNESS: timed out'), os._exit(3)))
    sys.exit(app.exec())
    '''
)

FILM_POINTS = 180
POLYMER_POINTS = 408


def test_experiment_chart_shows_only_the_new_project_after_a_reset(tmp_path):
    pytest.importorskip('PySide6.QtCharts')
    pytest.importorskip('EasyApplication')
    script = tmp_path / 'experiment_reset_harness.py'
    script.write_text(HARNESS, encoding='utf-8')
    environment = dict(os.environ)
    environment.setdefault('QT_QPA_PLATFORM', 'offscreen')
    environment.setdefault('QT_QUICK_BACKEND', 'software')

    completed = subprocess.run(  # noqa: S603 - our own interpreter running our own script
        [
            sys.executable,
            str(script),
            str(APP),
            str(APP / 'Examples' / 'FilmContrasts' / 'project.json'),
            str(APP / 'Examples' / 'PolymerFilm' / 'project.json'),
        ],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=180,
        env=environment,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output[-4000:]
    steps = json.loads(completed.stdout.split('RESULT ', 1)[1].splitlines()[0])
    assert len(steps) == 8

    def check(result, points):
        series = result['series']
        # One measured series and its two error bounds, all from the current project.
        assert len(series) == 3, (result['after'], series)
        for serie in series:
            assert serie['count'] == points, (result['after'], serie)
            # Nearly every point in view (an error bound at the reflectivity edge may overshoot);
            # axes left on the previous data's range lose a sizeable part.
            assert serie['inside'] >= 0.98 * serie['count'], (result['after'], serie)

    check(steps[0], FILM_POINTS)      # load film
    check(steps[2], FILM_POINTS)      # log q on
    assert steps[3]['series'] == [], steps[3]  # reset: no data, and nothing of the film left
    check(steps[4], POLYMER_POINTS)   # load polymer, on the log q axis
    check(steps[5], POLYMER_POINTS)   # log q off
    assert steps[6]['series'] == [], steps[6]
    check(steps[7], FILM_POINTS)      # load film, on the linear q axis
