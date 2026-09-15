// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

// The selected layer's moment angle as a dial rather than a number: the same
// arrow the Structure view and the SLD band draw, with the guide field H fixed
// to the right and the θM values the parameter table edits on the rim.
//
// Dragging inside the circle asks for a new direction through `phiRequested`;
// the owner decides whether to write it. The text field stays authoritative -
// this is a coarse pointer, snapped to `snapDegrees`.
Item {
    id: root

    // Physical moment direction, degrees counterclockwise from H.
    property real phi: 0
    // The parameter the table edits, shown alongside so the two stay connected.
    property real thetaM: 270
    property bool hasMoment: true
    // Whether a drag may ask for a new angle at all.
    property bool editable: false
    property int snapDegrees: 5

    signal phiRequested(real phi)

    implicitWidth: EaStyle.Sizes.fontPixelSize * 6
    implicitHeight: implicitWidth
    width: implicitWidth
    height: implicitHeight

    readonly property real radius: Math.min(width, height) / 2 - EaStyle.Sizes.fontPixelSize

    Canvas {
        id: dial

        anchors.fill: parent
        antialiasing: true

        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()
            const cx = width / 2
            const cy = height / 2
            const r = root.radius

            ctx.strokeStyle = EaStyle.Colors.chartGridLine
            ctx.lineWidth = 1
            ctx.beginPath()
            ctx.arc(cx, cy, r, 0, 2 * Math.PI)
            ctx.stroke()

            // Ticks every 90 degrees: the four cardinal points need no
            // trigonometry, which keeps the angle convention out of this file.
            ctx.beginPath()
            ctx.moveTo(cx + r, cy);  ctx.lineTo(cx + r * 0.85, cy)
            ctx.moveTo(cx - r, cy);  ctx.lineTo(cx - r * 0.85, cy)
            ctx.moveTo(cx, cy + r);  ctx.lineTo(cx, cy + r * 0.85)
            ctx.moveTo(cx, cy - r);  ctx.lineTo(cx, cy - r * 0.85)
            ctx.stroke()
        }
    }

    // Rim labels: the θM the parameter table would show for that direction.
    // θM = 270 is the guide field (`GUIDE_FIELD_ANGLE` in the library), and θM
    // grows clockwise on screen from there.
    Repeater {
        model: [{theta: '270', dx: 1, dy: 0}, {theta: '0', dx: 0, dy: -1},
                {theta: '90', dx: -1, dy: 0}, {theta: '180', dx: 0, dy: 1}]

        EaElements.Label {
            x: root.width / 2 + modelData.dx * root.radius * 1.18 - width / 2
            y: root.height / 2 + modelData.dy * root.radius * 1.18 - height / 2
            text: modelData.theta
            color: EaStyle.Colors.themeForegroundMinor
        }
    }

    EaElements.Label {
        x: root.width / 2 + root.radius * 0.55
        y: root.height / 2 - root.radius * 0.45 - height
        text: "H"
        color: EaStyle.Colors.themeForegroundMinor
    }

    MagnetizationArrow {
        anchors.centerIn: parent
        width: 2 * root.radius * 0.9
        height: width
        phi: root.phi
        hasMoment: root.hasMoment
        color: EaStyle.Colors.themeForegroundHovered
        outlineColor: "transparent"
    }

    MouseArea {
        id: drag

        anchors.fill: parent
        enabled: root.editable
        cursorShape: root.editable ? Qt.CrossCursor : Qt.ArrowCursor

        onPositionChanged: if (pressed) root.requestFrom(mouseX, mouseY)
        onPressed: root.requestFrom(mouseX, mouseY)
    }

    // The one place a screen position becomes an angle: y is measured down, so
    // the vertical component is negated to get a counterclockwise phi. The
    // *drawing* never does this - `MagnetizationArrow` rotates instead.
    function requestFrom(x, y) {
        const dx = x - width / 2
        const dy = height / 2 - y
        if (Math.abs(dx) < 1 && Math.abs(dy) < 1) {
            return
        }
        const degrees = (Math.atan2(dy, dx) * 180 / Math.PI + 360) % 360
        phiRequested(Math.round(degrees / snapDegrees) * snapDegrees % 360)
    }

    ToolTip.visible: hover.hovered
    ToolTip.text: root.hasMoment
                  ? qsTr("Moment: %1° from H (θM %2°)").arg(root.phi.toFixed(1)).arg(root.thetaM.toFixed(1))
                    + (root.editable ? '\n' + qsTr("Drag to set the angle (%1° steps)").arg(root.snapDegrees)
                                     : '\n' + qsTr("θM follows a constraint or a running fit and cannot be dragged"))
                  : qsTr("ρM is zero: there is no direction to show")

    HoverHandler {
        id: hover
    }
}
