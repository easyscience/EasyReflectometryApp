# SPDX-FileCopyrightText: 2026 EasyReflectometryApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2026 Contributors to the EasyReflectometryApp project <https://github.com/easyscience/EasyReflectometryApp>
import argparse
import os
import sys
from pathlib import Path

import EasyApplication
from EasyApplication.Logic.Logging import console
from PySide6.QtCore import QObject
from PySide6.QtCore import QUrl
from PySide6.QtCore import qInstallMessageHandler
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQml import qmlRegisterSingletonType

try:
    from PySide6.QtWebEngineQuick import QtWebEngineQuick as _QtWebEngineQuick

    _QtWebEngineQuick.initialize()
except ImportError:
    _QtWebEngineQuick = None

# Suppress matplotlib debug/verbose logging (especially font lookup spam)
import logging as _logging

_logging.getLogger('matplotlib').setLevel(_logging.WARNING)
_logging.getLogger('matplotlib.font_manager').setLevel(_logging.WARNING)

CURRENT_DIR = Path(__file__).parent  # path to qml components of the current project
# Path to the directory that *contains* the installed EasyApplication package, so that
# QML statements like `import EasyApplication.Gui.Style` can be resolved.
EASYAPP_IMPORT_DIR = Path(EasyApplication.__path__[0]).parent
# In the installer build the package is data in an EasyReflectometryApp/ folder next to
# this file; in a source checkout this file is inside the package.
INSTALLER = (CURRENT_DIR / 'EasyReflectometryApp' / 'Gui').is_dir()

if INSTALLER:
    from EasyReflectometryApp.Startup import Application
    from EasyReflectometryApp.Startup import Rendering
    from EasyReflectometryApp.Startup import Splash
else:
    from Startup import Application
    from Startup import Rendering
    from Startup import Splash


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--testmode', action='store_true', help='run the application in test mode')
    parser.add_argument(
        '--software-rendering',
        action='store_true',
        help='render the whole GUI without OpenGL (Qt Quick software backend). By default only the '
        'WebEngine views are kept off the GPU when a software OpenGL renderer is detected.',
    )
    parser.add_argument(
        '--no-splash',
        action='store_true',
        help=f'start without the splash screen (same as {Splash.ENV_VAR}=1)',
    )
    args = parser.parse_args()

    qInstallMessageHandler(console.qmlMessageHandler)
    console.debug('Custom Qt message handler defined')

    app = Application(sys.argv)  # Create the QApplication (Not QGuiApplication)
    console.debug(f'Qt Application created {app}')

    # Has to happen before the first window (the splash) is created
    rendering = Rendering.configure(forceSoftware=args.software_rendering)
    console.debug(f'Rendering mode: {rendering}')

    # Must come before the first QML engine (the splash's) exists: with PySide6 6.10,
    # qmlRegisterSingletonType called once any QQmlEngine exists breaks unrelated QML types
    # (Material's ElevationEffect, used by the EasyApplication dialogs, and with it the main
    # window). PyBackend is only imported under the splash, so the singleton is declared as a
    # plain QObject here and created by QML on first use, as before. QML reads its properties
    # from the real object.
    qmlRegisterSingletonType(QObject, 'Backends', 1, 0, 'PyBackend', lambda engine: PyBackend())
    console.debug('Backend singleton is registered to be accessible from QML via the name PyBackend')

    splash = Splash(enabled=not args.no_splash and os.environ.get(Splash.ENV_VAR) != '1')

    # The slow part of the startup, under the splash. Plain import statements, so that
    # PyInstaller still finds the scientific stack (see MD/SPLASH-DESIGN.md).
    splash.status('Loading the numerical libraries…')
    import numpy  # noqa: F401

    splash.status('Loading the fitting libraries…')
    import easyscience  # noqa: F401

    splash.status('Loading the reflectometry models…')
    import easyreflectometry  # noqa: F401

    splash.status('Loading the backend…')
    if INSTALLER:
        from EasyReflectometryApp.Backends.Py import PyBackend
    else:
        from Backends.Py import PyBackend

    engine = QQmlApplicationEngine()
    console.debug(f'QML application engine created {engine}')

    app.setWindowIcon(QIcon(str(CURRENT_DIR / 'Gui' / 'Resources' / 'Logo' / 'App.svg')))

    engine.rootContext().setContextProperty('isTestMode', args.testmode)

    if INSTALLER:  # Running from installer
        path_main_qml = QUrl.fromLocalFile(CURRENT_DIR / 'EasyReflectometryApp' / 'Gui' / 'ApplicationWindow.qml')
        engine.addImportPath(CURRENT_DIR / 'EasyReflectometryApp')
        engine.addImportPath(CURRENT_DIR)
        engine.addImportPath(str(EASYAPP_IMPORT_DIR))
        console.debug('Paths added where QML searches for components')
    else:  # Running locally
        path_main_qml = CURRENT_DIR / 'Gui' / 'ApplicationWindow.qml'
        engine.addImportPath(CURRENT_DIR)
        engine.addImportPath(str(EASYAPP_IMPORT_DIR))
        console.debug('Paths added where QML searches for components')

    splash.status('Building the interface…')
    engine.load(path_main_qml)
    console.debug('Main QML component loaded')

    if not engine.rootObjects():
        sys.exit(-1)
    splash.handOver(engine.rootObjects()[0])

    console.debug('Application event loop is about to start')
    sys.exit(app.exec())
