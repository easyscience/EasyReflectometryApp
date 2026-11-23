// SPDX-FileCopyrightText: 2026 EasyReflectometryApp contributors
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometryApp project <https://github.com/easyscience/EasyReflectometryApp>

// Startup splash card, shown while the GUI thread is blocked by imports and by loading
// ApplicationWindow.qml. All motion comes from Animators, which run on the render thread
// and therefore keep going while the GUI thread is busy. Keep it that way: no
// NumberAnimation, Behavior, Timer or BusyIndicator, and no import besides QtQuick
// (see MD/SPLASH-DESIGN.md, tests/test_startup.py).
import QtQuick

Rectangle {
    id: root

    property string status: ''
    property string version: ''
    // Set by splash.py once per startup step: fill the bar from `from` to `to` (fractions
    // of the startup) over `ms` milliseconds.
    property var step: ({ from: 0, to: 0, ms: 0 })

    onStepChanged: {
        fillAnimator.stop()
        fillAnimator.from = -track.width * (1 - root.step.from)
        fillAnimator.to = -track.width * (1 - root.step.to)
        fillAnimator.duration = Math.max(root.step.ms, 1)
        fillAnimator.start()
    }

    readonly property color accent: '#4ec1ef'
    readonly property color textColor: '#e9e9e9'

    width: 480
    height: 280
    color: '#303030'
    border { color: root.accent; width: 1 }

    Item {
        id: mark

        width: 96
        height: 96
        y: 44
        anchors.horizontalCenter: parent.horizontalCenter

        Rectangle {  // halo, pulsing outwards behind the logo
            anchors.fill: parent
            radius: 22
            color: 'transparent'
            border { color: root.accent; width: 3 }

            ScaleAnimator on scale { from: 1.0; to: 1.7; duration: 1800; loops: Animation.Infinite }
            OpacityAnimator on opacity { from: 0.6; to: 0.0; duration: 1800; loops: Animation.Infinite }
        }

        Image {
            anchors.fill: parent
            source: '../Gui/Resources/Logo/App.svg'
            sourceSize: Qt.size(192, 192)
        }
    }

    Column {
        anchors { top: mark.bottom; topMargin: 28; horizontalCenter: parent.horizontalCenter }
        spacing: 4

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: 'EasyReflectometry'
            color: root.textColor
            font.pixelSize: 22
        }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.version ? `v${root.version}` : ''
            color: root.textColor
            opacity: 0.6
            font.pixelSize: 13
        }

        Item { width: 1; height: 14 }

        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: root.status
            color: root.textColor
            font.pixelSize: 13
        }
    }

    Item {  // progress along the bottom edge: a full-width fill slid in from the left
        id: track

        anchors { left: parent.left; right: parent.right; bottom: parent.bottom; margins: 1 }
        height: 8
        clip: true

        Rectangle {
            anchors.fill: parent
            color: root.accent
            opacity: 0.2
        }

        Rectangle {
            id: fill

            x: -width  // empty until the first step
            width: parent.width
            height: parent.height
            color: root.accent
        }

        XAnimator {
            id: fillAnimator

            target: fill
            easing.type: Easing.OutQuad  // slows towards the step's end, where a late step waits
        }
    }
}
