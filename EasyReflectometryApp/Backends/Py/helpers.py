import os
import sys
from urllib.parse import urlparse

import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtCore import QUrl
from PySide6.QtGui import QOffscreenSurface
from PySide6.QtGui import QOpenGLContext
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQuick import QSGRendererInterface
from PySide6.QtWidgets import QApplication
from uncertainties import ufloat


class IO:
    @staticmethod
    def generalizePath(fpath: str) -> str:
        """
        Generalize the filepath to be platform-specific, so all file operations
        can be performed.
        :param URI rcfPath: URI to the file
        :return URI filename: platform specific URI
        """
        filename = urlparse(fpath).path
        if not sys.platform.startswith('win'):
            return filename
        if filename[0] == '/':
            filename = filename[1:].replace('/', os.path.sep)
        return filename

    @staticmethod
    def localFileToUrl(fpath: str) -> str:
        return QUrl.fromLocalFile(fpath).toString()

    @staticmethod
    def formatMsg(type, *args):
        types = {'main': '*', 'sub': '  -'}
        mark = types[type]
        widths = [22, 21, 20, 10]
        widths[0] -= len(mark)
        msgs = []
        for idx, arg in enumerate(args):
            msgs.append(f'{arg:<{widths[idx]}}')
        msg = ' ▌ '.join(msgs)
        msg = f'{mark} {msg}'
        return msg

    @staticmethod
    def toStdDevSmalestPrecision(value, std_dev):
        if std_dev > 1:
            value_str = f'{round(value)}'
            std_dev_str = f'{round(std_dev)}'
            value_with_std_dev_str = f'{value_str}({std_dev_str})'
        else:
            precision = 1
            std_dev_decimals = precision - int(np.floor(np.log10(std_dev) + 1))
            std_dev = round(std_dev, std_dev_decimals)
            std_dev_str = f'{std_dev:.{std_dev_decimals}f}'
            value = round(value, std_dev_decimals)
            value_str = f'{value:.{std_dev_decimals}f}'
            clipped_std_dev = int(round(std_dev * 10**std_dev_decimals))
            value_with_std_dev_str = f'{value_str}({clipped_std_dev})'
        return value_str, std_dev_str, value_with_std_dev_str

    @staticmethod
    def toStdDevSmalestPrecision_OLD(value, std_dev):
        if std_dev < 10:
            fmt = '.1u'
        else:
            fmt = 'u'
        value_str, std_dev_str = f'{ufloat(value, std_dev):{fmt}}'.split('+/-')
        value_with_std_dev_str = f'{ufloat(value, std_dev):{fmt}S}'
        return value_str, std_dev_str, value_with_std_dev_str

    # def value_with_error_WEB(val, err, precision=2):
    #     """String with value and error in parenthesis with the number of digits given by precision."""
    #     # Number of digits in the error
    #     err_decimals = precision - int(np.floor(np.log10(err) + 1))
    #     # Output error with a "precision" number of significant digits
    #     err_out = round(err, err_decimals)
    #     # Removes leading zeros for fractional errors
    #     if err_out < 1:
    #         err_out = int(round(err_out * 10**err_decimals))
    #         err_format = 0
    #     else:
    #         err_format = int(np.clip(err_decimals, 0, np.inf))

    #     # Format the value to have the same significant digits as the error
    #     val_out = round(val, err_decimals)
    #     val_format = int(np.clip(err_decimals, 0, np.inf))

    #     return f'{val_out:.{val_format}f}({err_out:.{err_format}f})'


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
    Chooses the Qt Quick scene graph backend on Linux.

    In remote-desktop sessions (VISA, xrdp, VNC, X2Go, ...) OpenGL is provided by
    Mesa's software rasteriser and frames are presented through GLX. When the
    remote client disconnects, the X server may stop completing buffer swaps, so
    the next frame blocks the GUI thread inside glXSwapBuffers and the window
    stays frozen ("not responding") after reconnecting. The software scene graph
    backend paints through plain X11 image uploads and never waits on a swap.
    """

    ENV_VAR = 'EASYREFLECTOMETRY_SOFTWARE_RENDERING'  # '1' forces it on, '0' forces it off
    QT_BACKEND_ENV_VARS = ('QT_QUICK_BACKEND', 'QSG_RHI_BACKEND')
    REMOTE_SESSION_ENV_VARS = ('XRDP_SESSION', 'VNCDESKTOP', 'X2GO_SESSION')
    SOFTWARE_GL_RENDERERS = ('llvmpipe', 'softpipe', 'swrast', 'software rasterizer')
    GL_RENDERER = 0x1F01

    @staticmethod
    def softwareRequested(environ, platform: str):
        """
        Decide from the environment alone.
        :return: True/False when decided, None when the OpenGL renderer has to be probed
        """
        override = environ.get(Rendering.ENV_VAR, '').strip().lower()
        if override in ('1', 'true', 'yes', 'on'):
            return True
        if override in ('0', 'false', 'no', 'off'):
            return False
        if not platform.startswith('linux'):
            return False
        if any(environ.get(name) for name in Rendering.QT_BACKEND_ENV_VARS):
            return False  # the user already picked a backend; leave it alone
        if any(environ.get(name) for name in Rendering.REMOTE_SESSION_ENV_VARS):
            return True
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
    def configure(forceSoftware: bool = False) -> bool:
        """
        Must be called after the QApplication is created and before the first
        QQuickWindow (i.e. before the QML engine loads the main component).
        :return: True if the software backend was selected
        """
        useSoftware = True if forceSoftware else Rendering.softwareRequested(os.environ, sys.platform)
        if useSoftware is None:
            useSoftware = Rendering.isSoftwareGlRenderer(Rendering.openGlRendererName())
        if useSoftware:
            QQuickWindow.setGraphicsApi(QSGRendererInterface.GraphicsApi.Software)
        return useSoftware
