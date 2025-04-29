# SPDX-FileCopyrightText: 2024 EasyReflectometryApp contributors
# SPDX-License-Identifier: BSD-3-Clause
# © 2024 Contributors to the EasyReflectometryApp project <https://github.com/easyscience/EasyReflectometryApp>
import argparse
import sys
from pathlib import Path

from EasyApp.Logic.Logging import console
from PySide6.QtCore import QUrl
from PySide6.QtCore import qInstallMessageHandler
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQml import qmlRegisterSingletonType

try:  # Running locally
    from Backends.Py import PyBackend
    from Backends.Py.helpers import Application

    INSTALLER = False
except ImportError:  # Running from installer
    from EasyReflectometryApp.Backends.Py import PyBackend
    from EasyReflectometryApp.Backends.Py.helpers import Application

    INSTALLER = True

CURRENT_DIR = Path(__file__).parent  # path to qml components of the current project


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--testmode', action='store_true', help='run the application in test mode')
    args = parser.parse_args()

    qInstallMessageHandler(console.qmlMessageHandler)
    console.debug('Custom Qt message handler defined')

    qmlRegisterSingletonType(PyBackend, 'Backends', 1, 0, 'PyBackend')
    console.debug('Backend class is registered to be accessible from QML via the name PyBackend')

    app = Application(sys.argv)  # Create the QApplication (Not QGuiApplication)
    console.debug(f'Qt Application created {app}')

    engine = QQmlApplicationEngine()
    console.debug(f'QML application engine created {engine}')

    engine.rootContext().setContextProperty('isTestMode', args.testmode)

    if INSTALLER:  # Running from installer
        path_main_qml = QUrl.fromLocalFile(CURRENT_DIR / 'EasyReflectometryApp' / 'Gui' / 'ApplicationWindow.qml')
        engine.addImportPath(CURRENT_DIR / 'EasyReflectometryApp')
        engine.addImportPath(CURRENT_DIR)
        console.debug('Paths added where QML searches for components')
    else:  # Running locally
        path_main_qml = path_main_qml = CURRENT_DIR / 'Gui' / 'ApplicationWindow.qml'
        engine.addImportPath(CURRENT_DIR)
        engine.addImportPath(CURRENT_DIR / '..' / '..' / 'EasyApp' / 'src')
        console.debug('Paths added where QML searches for components')

    engine.load(path_main_qml)
    console.debug('Main QML component loaded')

    console.debug('Application event loop is about to start')
    if not engine.rootObjects():
        sys.exit(-1)
    sys.exit(app.exec())
