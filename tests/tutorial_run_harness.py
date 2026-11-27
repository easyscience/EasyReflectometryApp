"""Runs every shipped tutorial in the real application window, offscreen (tests/test_tutorials_run.py).

    python tests/tutorial_run_harness.py <settings.ini>

Starts the window as main.py does, with `pySettingsPath` pointed at the given file. For each
tutorial: start it as the Home page does, then for every step wait until its control is framed,
run **Show me** on a step with a condition and wait for it to complete, and press **Next**
unless the step moves on by itself. Prints `RESULT {...}` as JSON at the end.
"""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / 'EasyReflectometryApp'
sys.path.insert(0, str(APP))

import EasyApplication  # noqa: E402
from Backends.Py import PyBackend  # noqa: E402
from PySide6.QtCore import Q_ARG  # noqa: E402
from PySide6.QtCore import QMetaObject  # noqa: E402
from PySide6.QtCore import QObject  # noqa: E402
from PySide6.QtCore import QTimer  # noqa: E402
from PySide6.QtCore import QUrl  # noqa: E402
from PySide6.QtQml import QQmlApplicationEngine  # noqa: E402
from PySide6.QtQml import qmlRegisterSingletonType  # noqa: E402
from Startup import Application  # noqa: E402

STEP_TIMEOUT_S = 60
POLL_MS = 100


def main() -> None:
    app = Application(sys.argv[:1])
    # Before any engine exists (see main.py).
    qmlRegisterSingletonType(QObject, 'Backends', 1, 0, 'PyBackend', lambda engine: PyBackend())
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty('isTestMode', False)
    engine.rootContext().setContextProperty('pySettingsPath', QUrl.fromLocalFile(sys.argv[1]).toString())
    engine.addImportPath(str(APP))
    engine.addImportPath(str(Path(EasyApplication.__path__[0]).parent))
    engine.load(QUrl.fromLocalFile(str(APP / 'Gui' / 'ApplicationWindow.qml')))
    if not engine.rootObjects():
        print('HARNESS: the window failed to load', flush=True)
        sys.exit(2)
    window = engine.rootObjects()[0]
    window.setProperty('width', 1600)
    window.setProperty('height', 1000)
    panel = window.property('tutorialPanel')
    wrapper = panel.property('backend')  # Globals.BackendWrapper

    def read(item, name):
        value = item.property(name)
        return value.toVariant() if hasattr(value, 'toVariant') else value

    def call(item, name, *args):
        QMetaObject.invokeMethod(item, name, *(Q_ARG('QVariant', arg) for arg in args))

    result = {'docked': window.property('tutorialPanelDocked'), 'tutorials': []}
    queue = list(read(wrapper, 'tutorialAvailable'))
    current = {}

    def next_tutorial():
        if not queue:
            print('RESULT ' + json.dumps(result), flush=True)
            app.quit()
            return
        tutorial = queue.pop(0)
        result['tutorials'].append({'id': tutorial['id'], 'steps': [], 'state': ''})
        current.clear()
        current['deadline'] = time.monotonic() + STEP_TIMEOUT_S
        # The previous tutorial left an edited example, which the start would ask about first.
        call(wrapper, 'tutorialStop')
        call(window, 'resetToInitialState')
        call(window, 'startTutorial', tutorial)  # as the Home page's list does
        QTimer.singleShot(POLL_MS, poll)

    def poll():
        record = result['tutorials'][-1]
        state = read(wrapper, 'tutorialState')
        if state != 'active' and not current.get('started'):
            if time.monotonic() > current['deadline']:
                record['state'] = 'did not start'
                next_tutorial()
            else:
                QTimer.singleShot(POLL_MS, poll)
            return
        current['started'] = True
        if state != 'active':
            record['state'] = state
            next_tutorial()
            return
        step = read(wrapper, 'tutorialStep')
        if step['id'] != current.get('id'):
            current.update(id=step['id'], deadline=time.monotonic() + STEP_TIMEOUT_S, acted=False)
            record['steps'].append({'id': step['id'], 'framed': False})
        framed = read(panel, 'frameItem') is not None
        record['steps'][-1]['framed'] |= framed
        if time.monotonic() > current['deadline']:
            record['steps'][-1].update(message=step['message'] or read(panel, 'showMeError'), note=read(panel, 'frameNote'))
            record['state'] = 'timed out'
            if os.environ.get('HARNESS_SCREENSHOT'):
                window.grabWindow().save(os.environ['HARNESS_SCREENSHOT'])
            next_tutorial()
            return
        if step['hasCondition'] and step['state'] != 'done':
            if not current['acted'] and read(panel, 'showMeEnabled'):
                current['acted'] = True
                call(panel, 'showMe')
        elif step['canNext'] and not step['advance'] and (record['steps'][-1]['framed'] or not step['target']):
            call(wrapper, 'tutorialNext')
        QTimer.singleShot(POLL_MS, poll)

    QTimer.singleShot(500, next_tutorial)
    QTimer.singleShot(240_000, lambda: (print('HARNESS: timed out', flush=True), os._exit(3)))
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
