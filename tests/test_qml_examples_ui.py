"""Runtime check of the Examples group on the Project page (Examples.qml) and of the dialog that
replaces the session with an example (LoadExampleDialog.qml), in a real QML engine.

The source-level checks in test_example_projects.py cannot see a QML error that stops the file
from loading (once, an assignment to the read-only `implicitWidth` of a Label left the examples
list empty). This loads the real files with the Mock backend, measures the "Load an example"
dialog, which takes its width from its content's implicit width, and runs the loading itself as
the Examples list and the tutorials use it.

A QGuiApplication cannot coexist with the QCoreApplication the other tests share, so the
harness runs in a subprocess (as in test_qml_close_behaviour.py).
"""

import json
import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

GUI = Path(__file__).resolve().parents[1] / 'EasyReflectometryApp' / 'Gui'

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
    import EasyApplication.Gui.Style as EaStyle
    import Gui as Gui
    import Gui.Globals as Globals

    Window {
        width: 1200
        height: 800
        visible: true

        Loader {
            id: loader
            width: 400
            height: 600
            source: "%s"
        }

        Gui.LoadExampleDialog { id: replaceDialog }

        // Stand-ins for the application bar's page buttons, which a load enables.
        readonly property var tabs: Globals.References.applicationWindow.appBarCentralTabs
        Component.onCompleted: {
            for (const name of ['projectButton', 'sampleButton', 'experimentButton', 'analysisButton', 'summaryButton']) {
                tabs[name] = Qt.createQmlObject(
                    'import QtQuick; QtObject { property bool enabled: false; property bool checked: false; '
                    + 'function toggle() { checked = !checked } }', this)
            }
        }

        // 0: an edited example, 1: a created project with unsaved changes, 2: own work, no project
        function setState(state) {
            const project = Globals.BackendWrapper.activeBackend.project
            project.created = state === 1
            project.isExample = state === 0
            replaceDialog.example = loader.item.model[1]
            replaceDialog.open()
        }

        function measure() {
            const dialog = replaceDialog
            const message = dialog.contentItem.children[0].children[0]
            return { dialogWidth: dialog.width, messageWidth: message.width, lineCount: message.lineCount,
                     padding: dialog.leftPadding + dialog.rightPadding }
        }

        readonly property var report: ({
            loaderStatus: loader.status,
            rows: loader.status === Loader.Ready ? loader.item.model.length : -1,
            fontPixelSize: EaStyle.Sizes.fontPixelSize,
        })

        // Loading as the Examples list and the tutorials do: at once without unsaved work,
        // after asking with it, and never calling back on Cancel or on a failed load.
        function loading() {
            const project = Globals.BackendWrapper.activeBackend.project
            const examples = loader.item.model
            let calls = 0
            const onLoaded = () => calls += 1
            replaceDialog.close()
            // `visible` lags behind open()/close() by the transitions: count the openings.
            let asks = 0
            replaceDialog.aboutToShow.connect(() => asks += 1)
            project.created = false
            project.isExample = false
            project.hasUnsavedChanges = false

            replaceDialog.request(examples[0], onLoaded)
            const direct = { calls: calls, asked: asks > 0, name: project.name,
                             tabsEnabled: tabs.analysisButton.enabled && tabs.summaryButton.enabled,
                             projectOpen: tabs.projectButton.checked }

            project.hasUnsavedChanges = true
            replaceDialog.request(examples[1], onLoaded)
            const asked = asks === 1
            replaceDialog.close()  // Cancel
            const afterCancel = { calls: calls, name: project.name }

            replaceDialog.request(examples[1], onLoaded)
            replaceDialog.load(replaceDialog.example, replaceDialog.onLoaded)  // what "Load example" does
            replaceDialog.close()
            const afterLoad = { calls: calls, name: project.name }

            project.hasUnsavedChanges = false
            replaceDialog.request({ name: 'Missing', path: 'mock/Missing/project.json' }, onLoaded)
            const afterFailure = calls

            // No path: a new, empty project (a tutorial that builds its own), asked about first.
            project.hasUnsavedChanges = true
            replaceDialog.request({ name: 'A tutorial', path: '' }, onLoaded)
            const emptyTitle = replaceDialog.title
            replaceDialog.load(replaceDialog.example, replaceDialog.onLoaded)
            replaceDialog.close()
            const empty = { calls: calls, isExample: project.isExample, title: emptyTitle }
            return { direct: direct, asked: asked, afterCancel: afterCancel, afterLoad: afterLoad, afterFailure: afterFailure,
                     empty: empty, names: [examples[0].name, examples[1].name] }
        }
    }
    """ % (gui / 'Pages' / 'Project' / 'Sidebar' / 'Basic' / 'Groups' / 'Examples.qml').as_uri()

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('isTestMode', False)
    engine.addImportPath(str(gui.parent))
    engine.addImportPath(str(Path(EasyApplication.__path__[0]).parent))
    engine.loadData(QML.encode(), QUrl.fromLocalFile(str(gui / 'harness.qml')))
    if not engine.rootObjects():
        print('HARNESS: QML failed to load')
        sys.exit(2)
    window = engine.rootObjects()[0]
    result = {'states': []}

    def to_python(value):
        return value.toVariant() if hasattr(value, 'toVariant') else dict(value)

    def call(name, *args):
        from PySide6.QtCore import QMetaObject, Q_ARG, Q_RETURN_ARG
        if args:
            QMetaObject.invokeMethod(window, name, Q_ARG('QVariant', args[0]))
            return None
        return to_python(QMetaObject.invokeMethod(window, name, Q_RETURN_ARG('QVariant')))

    def start():
        result.update(to_python(window.property('report')))
        if result['loaderStatus'] != 1:  # Loader.Ready
            finish()
            return
        step(0)

    def step(state):
        if state == 3:
            result['loading'] = call('loading')
            finish()
            return
        call('setState', state)
        # The Column lays the label out on the next polish, so measure a moment later.
        QTimer.singleShot(200, lambda: (result['states'].append(call('measure')), step(state + 1)))

    def finish():
        print('RESULT ' + json.dumps(result), flush=True)
        app.quit()

    QTimer.singleShot(100, start)
    QTimer.singleShot(20000, lambda: (print('HARNESS: timed out'), os._exit(3)))
    sys.exit(app.exec())
    '''
)


def test_examples_list_loads_and_the_replace_dialog_fits_its_message_and_loads(tmp_path):
    pytest.importorskip('PySide6.QtQml')
    pytest.importorskip('EasyApplication')
    script = tmp_path / 'examples_harness.py'
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
        timeout=90,
        env=environment,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    result = json.loads(completed.stdout.split('RESULT ', 1)[1].splitlines()[0])

    # Qt reports QML errors in the file (bad assignments, unknown properties) on stderr.
    assert [line for line in completed.stderr.splitlines() if 'Examples.qml' in line or 'LoadExampleDialog.qml' in line] == []
    assert result['loaderStatus'] == 1, output
    # The Mock backend lists two examples.
    assert result['rows'] == 2

    cap = result['fontPixelSize'] * 28
    assert len(result['states']) == 3
    for state in result['states']:
        # The message wraps at a readable width, and the dialog is only as wide as the message.
        assert 0 < state['messageWidth'] <= cap, state
        assert state['dialogWidth'] == pytest.approx(state['messageWidth'] + state['padding'], abs=1), state
        assert state['lineCount'] >= 2, state

    loading = result['loading']
    first, second = loading['names']
    # Nothing unsaved: loaded at once, the page tabs enabled and the Project page opened (where
    # a load error is shown), then the caller (a tutorial) is told.
    assert loading['direct'] == {'calls': 1, 'asked': False, 'name': first, 'tabsEnabled': True, 'projectOpen': True}
    # Unsaved work: asked first, and Cancel loads nothing.
    assert loading['asked'] is True
    assert loading['afterCancel'] == {'calls': 1, 'name': first}
    assert loading['afterLoad'] == {'calls': 2, 'name': second}
    # A load that fails does not start what was waiting for it.
    assert loading['afterFailure'] == 2
    # Without a path, the session is reset instead, and then the caller is told.
    assert loading['empty'] == {'calls': 3, 'isExample': False, 'title': 'Start from an empty project'}
