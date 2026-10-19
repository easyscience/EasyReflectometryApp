"""Runtime check of the close path ApplicationWindow.qml relies on.

In Qt 6, `Qt.quit()` does not stop the event loop directly: it asks every top-level window to
close, which runs the window's `onClosing` handler. A handler that rejects the close while the
project is dirty therefore swallows the quit, and a dialog button that calls `Qt.quit()` after
such a handler can never exit. ApplicationWindow.qml handles this with a `discardChangesOnClose`
flag that `onClosing` consults. This test drives a window with the same handler shape through
a real `QGuiApplication` and asserts both halves: the quit is swallowed while dirty, and the
window closes once the flag is set.

The real ApplicationWindow needs the whole application (EasyApplication components, the Globals
singletons, a backend), so the handler shape is reproduced here. The source-level test in
`test_qml_project_save_ui.py` pins that the real handler has that shape.

A `QGuiApplication` cannot coexist with the `QCoreApplication` the other tests share, so the
harness runs in a subprocess.
"""

import os
import subprocess
import sys
import textwrap

import pytest

pytest.importorskip('PySide6.QtQml')

HARNESS = textwrap.dedent(
    '''
    import os
    import sys

    from PySide6.QtCore import QTimer
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine

    QML = b"""
    import QtQuick

    Window {
        id: applicationWindow
        visible: true
        width: 100
        height: 100

        property bool projectHasUnsavedChanges: true
        property bool discardChangesOnClose: false
        property int closingCount: 0

        // Same shape as ApplicationWindow.qml's handler (the prompt itself is not needed here).
        onClosing: function(close) {
            closingCount += 1
            if (projectHasUnsavedChanges && !discardChangesOnClose) {
                close.accepted = false
            }
        }
    }
    """

    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.loadData(QML)
    if not engine.rootObjects():
        print('HARNESS: QML failed to load')
        sys.exit(2)
    window = engine.rootObjects()[0]

    def quit_while_dirty():
        # What "Exit without saving" did before the fix, and what the test-mode timer does.
        app.quit()
        QTimer.singleShot(300, exit_with_discard_flag)

    def exit_with_discard_flag():
        # Still running: the rejected close swallowed the quit.
        print(f'ALIVE after quit while dirty, closingCount={window.property("closingCount")}')
        window.setProperty('discardChangesOnClose', True)
        window.close()  # what "Exit without saving" does now

    def report_exit():
        print(f'EXITING closingCount={window.property("closingCount")}')

    app.aboutToQuit.connect(report_exit)
    QTimer.singleShot(0, quit_while_dirty)
    QTimer.singleShot(10000, lambda: (print('HARNESS: timed out'), os._exit(3)))
    sys.exit(app.exec())
    '''
)


def test_quit_is_swallowed_while_dirty_and_the_discard_flag_lets_the_window_close(tmp_path):
    script = tmp_path / 'close_harness.py'
    script.write_text(HARNESS, encoding='utf-8')
    environment = dict(os.environ)
    environment.setdefault('QT_QPA_PLATFORM', 'offscreen')
    environment.setdefault('QT_QUICK_BACKEND', 'software')
    environment.setdefault('QT_LOGGING_RULES', '*.debug=false')

    completed = subprocess.run(  # noqa: S603 - our own interpreter running our own script
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        timeout=60,
        env=environment,
    )

    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    # First quit: onClosing ran once, rejected the close, and the application kept running.
    assert 'ALIVE after quit while dirty, closingCount=1' in output, output
    # With the flag set, the close is accepted and the application exits.
    assert 'EXITING closingCount=2' in output, output
