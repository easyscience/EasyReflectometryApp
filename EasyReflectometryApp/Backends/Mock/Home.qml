pragma Singleton

import QtQuick

QtObject {

    property bool created: false

    readonly property var version: {
        'number': '1.1.1',
        'date': '28 May 2025',
    }

    readonly property var urls: {
        'homepage': 'https://easyreflectometry.org',
        'issues': 'https://github.com/EasyScience/EasyReflectometryApp/issues',
        'license': 'https://github.com/EasyScience/EasyReflectometryApp/blob/master/LICENSE.md',
        'documentation': 'https://easyscience.github.io/EasyReflectometryApp/',
        'dependencies': 'https://github.com/EasyScience/EasyReflectometryApp/blob/master/DEPENDENCIES.md',
    }
}