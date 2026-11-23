# SPDX-FileCopyrightText: 2026 EasyReflectometryApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2026 Contributors to the EasyReflectometryApp project <https://github.com/easyscience/EasyReflectometryApp>
import ctypes
import sys
from pathlib import Path

import toml
from PySide6.QtCore import QEventLoop
from PySide6.QtCore import QObject
from PySide6.QtCore import QPoint
from PySide6.QtCore import Qt
from PySide6.QtCore import QTimer
from PySide6.QtCore import QUrl
from PySide6.QtCore import Slot
from PySide6.QtQuick import QQuickView

PYPROJECT = Path(__file__).parents[2] / 'pyproject.toml'  # the file the Home page reads the version from


def appVersion() -> str:
    try:
        return toml.load(PYPROJECT)['project']['version']
    except (OSError, KeyError):
        return ''


class Splash(QObject):
    """
    Card shown from just after the QApplication is created until the main window
    has painted its first frame.

    The GUI thread is blocked for most of that time (imports, loading the main QML),
    so the card's animation runs on the Qt Quick render thread (see Splash.qml), and
    the methods below wait just long enough for the card to show each change.
    With ``enabled=False`` no window is created and every method does nothing.
    """

    QML = Path(__file__).with_name('Splash.qml')
    ENV_VAR = 'EASYREFLECTOMETRY_NO_SPLASH'  # '1' disables the splash, like --no-splash
    FLAGS = Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowDoesNotAcceptFocus | Qt.WindowTransparentForInput
    FIRST_FRAME_TIMEOUT_MS = 1000
    STATUS_TIMEOUT_MS = 100
    HAND_OVER_TIMEOUT_MS = 5000

    def __init__(self, enabled: bool = True, parent=None):
        super().__init__(parent)
        self._view = None
        self._window = None
        if not enabled:
            return
        if sys.platform == 'win32':
            # Otherwise Windows may replace a window whose GUI thread is busy for more
            # than ~5 s by a frozen "Not Responding" snapshot, stopping the animation.
            ctypes.windll.user32.DisableProcessWindowsGhosting()
        view = QQuickView()
        view.setFlags(self.FLAGS)
        view.setInitialProperties({'version': appVersion()})
        view.setSource(QUrl.fromLocalFile(str(self.QML)))
        if view.status() != QQuickView.Status.Ready:
            return  # the errors are logged by Qt; start without a splash rather than not at all
        screen = view.screen().availableGeometry()
        view.setPosition(screen.center() - QPoint(view.width() // 2, view.height() // 2))
        view.show()
        self._view = view
        self._waitFor(view.frameSwapped, self.FIRST_FRAME_TIMEOUT_MS)

    def status(self, text: str) -> None:
        """Show the stage that is about to start; returns once the card has the new text."""
        if self._view is None:
            return
        self._view.rootObject().setProperty('status', text)
        # The scene is synchronised from the GUI thread, so the text reaches the screen
        # only if events are processed until then. Waiting for frameSwapped would not do:
        # the animation produces frames all the time, also before the text is synced.
        self._waitFor(self._view.afterSynchronizing, self.STATUS_TIMEOUT_MS)

    def handOver(self, window) -> None:
        """Close the card once `window` has painted its first frame, or after a safety timeout."""
        if self._view is None:
            return
        self._window = window
        window.frameSwapped.connect(self.finish, Qt.QueuedConnection)  # emitted on the render thread
        QTimer.singleShot(self.HAND_OVER_TIMEOUT_MS, self.finish)

    @Slot()
    def finish(self) -> None:
        if self._view is None:
            return
        if self._window is not None:
            self._window.frameSwapped.disconnect(self.finish)  # it is emitted on every frame
            self._window = None
        self._view.close()
        self._view = None

    @staticmethod
    def _waitFor(signal, timeoutMs: int) -> None:
        loop = QEventLoop()
        timer = QTimer(loop)
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)
        signal.connect(loop.quit, Qt.QueuedConnection)  # may be emitted on the render thread
        timer.start(timeoutMs)
        loop.exec()
        signal.disconnect(loop.quit)
