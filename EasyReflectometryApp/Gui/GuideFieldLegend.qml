// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

// The "H →" reference every arrow view puts on screen, so the direction of the
// guide field is visible rather than remembered. Drawn with the same component
// as the moment arrows: at phi = 0 for the default in-plane field (the zero of
// phi), at 180 when the field is reversed. A field tilted out of the sample
// plane has no in-plane arrow; its angle is shown instead.
Row {
    id: root

    property real glyphSize: EaStyle.Sizes.fontPixelSize * 1.5
    readonly property var field: Globals.BackendWrapper.sampleMagneticField

    spacing: EaStyle.Sizes.fontPixelSize * 0.25

    EaElements.Label {
        anchors.verticalCenter: parent.verticalCenter
        text: "H"
        color: EaStyle.Colors.themeForegroundMinor
    }

    MagnetizationArrow {
        visible: root.field.in_plane
        anchors.verticalCenter: parent.verticalCenter
        width: root.glyphSize
        height: root.glyphSize
        phi: root.field.phi
        color: EaStyle.Colors.themeForegroundMinor
        outlineColor: "transparent"
    }

    EaElements.Label {
        visible: !root.field.in_plane
        anchors.verticalCenter: parent.verticalCenter
        text: qsTr("tilted, %1°").arg(Number(root.field.guide_field_angle).toFixed(1))
        color: EaStyle.Colors.themeForegroundMinor
    }

    ToolTip.visible: hover.hovered
    ToolTip.text: root.field.in_plane
                  ? qsTr("Guide field direction. Arrows point the way the moment does in the sample plane; with the default field θM = 270° points along H (no spin flip).")
                  : qsTr("The guide field is tilted out of the sample plane (angle %1° about the beam). Arrows still show the moment in the sample plane.")
                    .arg(Number(root.field.guide_field_angle).toFixed(1))

    HoverHandler {
        id: hover
    }
}
