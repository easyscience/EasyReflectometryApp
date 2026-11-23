# SPDX-FileCopyrightText: 2026 EasyReflectometryApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2026 Contributors to the EasyReflectometryApp project <https://github.com/easyscience/EasyReflectometryApp>
import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QOffscreenSurface
from PySide6.QtGui import QOpenGLContext
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQuick import QSGRendererInterface
from PySide6.QtWidgets import QApplication


class Application(QApplication):  # QGuiApplication crashes when using in combination with QtCharts
    def __init__(self, sysArgv):
        super(Application, self).__init__(sysArgv)
        self.setApplicationName('EasyReflectometry')
        self.setOrganizationName('EasyScience')
        self.setOrganizationDomain('easyscience.software')
        # On Linux, render file/folder dialogs with Qt itself instead of the
        # desktop's native ones. On desktops that Qt maps to the gtk3 platform
        # theme (GNOME, XFCE, MATE, ...) the native dialog is a GTK window running
        # inside our process, along with the GTK/GLib libraries PyInstaller copied
        # from the build machine; browsing folders then loads the *system's* GVfs,
        # pixbuf and GSettings modules into them and occasionally crashes.
        # The attribute covers both QtQuick.Dialogs and QtWidgets.QFileDialog.
        if sys.platform.startswith('linux'):
            self.setAttribute(Qt.AA_DontUseNativeDialogs)


class Rendering:
    """
    Chooses how the GUI is rendered on Linux.

    In remote-desktop sessions (VISA, xrdp, VNC, X2Go, ...) OpenGL is provided by
    Mesa's software rasteriser (llvmpipe). The Qt Quick scene graph copes with
    that, but Qt WebEngine (the Bayesian plots) additionally runs Chromium's GPU
    thread in-process on the same software GL, with contexts shared with the
    scene graph; the window then stops repainting or freezes ("not responding").
    Telling Chromium to stay off the GPU (``--disable-gpu``) is enough: it
    composites in software instead, and the rest of the GUI keeps using OpenGL.

    The Qt Quick *software* scene graph backend avoids OpenGL altogether. It is
    heavier (every frame is painted on the CPU, ShaderEffect is unavailable) and
    is only used when explicitly requested.
    """

    ENV_VAR = 'EASYREFLECTOMETRY_SOFTWARE_RENDERING'  # '1' forces the software scene graph, '0' leaves Qt alone
    CHROMIUM_FLAGS_ENV_VAR = 'QTWEBENGINE_CHROMIUM_FLAGS'
    CHROMIUM_DISABLE_GPU = '--disable-gpu'
    QT_BACKEND_ENV_VARS = ('QT_QUICK_BACKEND', 'QSG_RHI_BACKEND')
    REMOTE_SESSION_ENV_VARS = ('XRDP_SESSION', 'VNCDESKTOP', 'X2GO_SESSION')
    SOFTWARE_GL_RENDERERS = ('llvmpipe', 'softpipe', 'swrast', 'software rasterizer')
    GL_RENDERER = 0x1F01

    # Return values of configure()
    DEFAULT = 'default'  # nothing changed
    WEBENGINE_SOFTWARE = 'webengine-software'  # Qt Quick on OpenGL, Chromium without GPU
    SOFTWARE = 'software'  # Qt Quick software scene graph, Chromium without GPU

    @staticmethod
    def override(environ):
        """The user's choice from the environment: True/False, or None when not set."""
        value = environ.get(Rendering.ENV_VAR, '').strip().lower()
        if value in ('1', 'true', 'yes', 'on'):
            return True
        if value in ('0', 'false', 'no', 'off'):
            return False
        return None

    @staticmethod
    def isSoftwareGlRenderer(rendererName: str) -> bool:
        rendererName = rendererName.lower()
        return any(name in rendererName for name in Rendering.SOFTWARE_GL_RENDERERS)

    @staticmethod
    def openGlRendererName() -> str:
        """Name of the OpenGL renderer Qt would use, or '' if it cannot be queried."""
        context = QOpenGLContext()
        if not context.create():
            return ''
        surface = QOffscreenSurface()
        surface.setFormat(context.format())
        surface.create()
        if not context.makeCurrent(surface):
            return ''
        try:
            return context.functions().glGetString(Rendering.GL_RENDERER) or ''
        finally:
            context.doneCurrent()

    @staticmethod
    def usesSoftwareGl(environ, platform: str) -> bool:
        """True when OpenGL on this Linux session is (very likely) software rendered."""
        if not platform.startswith('linux'):
            return False
        if any(environ.get(name) for name in Rendering.REMOTE_SESSION_ENV_VARS):
            return True
        return Rendering.isSoftwareGlRenderer(Rendering.openGlRendererName())

    @staticmethod
    def disableWebEngineGpu(environ) -> None:
        """
        Keep Chromium off the GPU. Chromium reads the flags when the first
        WebEngine view is created, so this has to run before the QML is loaded.
        """
        flags = environ.get(Rendering.CHROMIUM_FLAGS_ENV_VAR, '')
        if Rendering.CHROMIUM_DISABLE_GPU in flags.split():
            return
        environ[Rendering.CHROMIUM_FLAGS_ENV_VAR] = f'{flags} {Rendering.CHROMIUM_DISABLE_GPU}'.strip()

    @staticmethod
    def configure(forceSoftware: bool = False, environ=None, platform: str = None) -> str:
        """
        Must be called after the QApplication is created and before the first
        QQuickWindow (i.e. before the QML engine loads the main component).
        :return: one of DEFAULT, WEBENGINE_SOFTWARE, SOFTWARE
        """
        environ = os.environ if environ is None else environ
        platform = sys.platform if platform is None else platform

        override = Rendering.override(environ)
        if forceSoftware or override is True:
            Rendering.disableWebEngineGpu(environ)
            QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Software)
            return Rendering.SOFTWARE
        if override is False:
            return Rendering.DEFAULT
        if any(environ.get(name) for name in Rendering.QT_BACKEND_ENV_VARS):
            return Rendering.DEFAULT  # the user already picked a backend; leave it alone
        if Rendering.usesSoftwareGl(environ, platform):
            Rendering.disableWebEngineGpu(environ)
            return Rendering.WEBENGINE_SOFTWARE
        return Rendering.DEFAULT
