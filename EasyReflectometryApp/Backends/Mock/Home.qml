pragma Singleton

import QtQuick

QtObject {

    property bool created: false

    readonly property var version: {
        'number': '1.2.0',
        'date': '10 March 2026',
    }

    readonly property var urls: {
        'homepage': 'https://easyreflectometry.org',
        'issues': 'https://github.com/EasyScience/EasyReflectometryApp/issues',
        'license': 'https://github.com/EasyScience/EasyReflectometryApp/blob/master/LICENSE.md',
        'documentation': 'https://easyscience.github.io/EasyReflectometryApp/',
        'dependencies': 'https://github.com/EasyScience/EasyReflectometryApp/blob/master/DEPENDENCIES.md',
    }
}