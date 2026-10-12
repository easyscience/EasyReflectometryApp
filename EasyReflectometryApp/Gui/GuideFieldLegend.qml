// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

// The "H →" reference every arrow view puts on screen, so the direction the
// moment angles are measured from is visible rather than remembered. Drawn with
// the same component as the moment arrows, at phi = 0 by definition: the guide
// field *is* the zero of phi.
Row {
    id: root

    property real glyphSize: EaStyle.Sizes.fontPixelSize * 1.5

    spacing: EaStyle.Sizes.fontPixelSize * 0.25

    EaElements.Label {
        anchors.verticalCenter: parent.verticalCenter
        text: "H"
        color: EaStyle.Colors.themeForegroundMinor
    }

    MagnetizationArrow {
        anchors.verticalCenter: parent.verticalCenter
        width: root.glyphSize
        height: root.glyphSize
        phi: 0
        color: EaStyle.Colors.themeForegroundMinor
        outlineColor: "transparent"
    }

    ToolTip.visible: hover.hovered
    ToolTip.text: qsTr("Guide field direction. Moment angles are measured from it: θM = 270° points along H (no spin flip).")

    HoverHandler {
        id: hover
    }
}
