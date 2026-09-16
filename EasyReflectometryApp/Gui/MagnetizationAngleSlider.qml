// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

// The selected layer's moment angle as a slider across the full 0-360° range,
// with the guide field reference and the resulting arrow beside it.
//
// The slider edits θM - the parameter the table shows and a fit varies - so it
// writes exactly what the θM text field writes, and 0-360 is that parameter's
// own range. The arrow draws φ, the direction the moment *physically* points,
// which the backend derives: a negative ρM is the same moment reversed, so the
// arrow can turn while θM stays where it was put.
Row {
    id: root

    // The parameter being edited, in degrees.
    property real thetaM: 270
    // Physical moment direction, degrees counterclockwise from H. Display only.
    property real phi: 0
    property bool hasMoment: true
    // Whether the slider may be moved at all.
    property bool editable: false
    // The drag resolution, as on the dial this replaces.
    property int snapDegrees: 5

    signal thetaMRequested(real thetaM)

    readonly property real glyphSize: EaStyle.Sizes.fontPixelSize * 1.5

    width: EaStyle.Sizes.sideBarContentWidth
    spacing: EaStyle.Sizes.fontPixelSize * 0.5

    EaElements.Label {
        id: nameLabel
        anchors.verticalCenter: parent.verticalCenter
        width: EaStyle.Sizes.fontPixelSize * 2
        text: qsTr("θM")
    }

    EaElements.Slider {
        id: slider

        anchors.verticalCenter: parent.verticalCenter
        // Whatever the fixed columns do not take.
        width: root.width - nameLabel.width - valueLabel.width - guideField.width - root.glyphSize
               - 4 * root.spacing

        from: 0
        to: 360
        stepSize: root.snapDegrees
        // stepSize alone only snaps the keyboard and the wheel; the dial this
        // replaces snapped the drag too.
        snapMode: Slider.SnapAlways
        enabled: root.editable

        onMoved: root.thetaMRequested(value)
    }

    // The model owns the value; a drag only borrows it. Not a plain `value:`
    // binding: dragging assigns `value` imperatively and would break it for
    // good, after which the handle stops following the model. A Binding stands
    // aside while the handle is held and reasserts itself on release, so a
    // write the model refused or clamped snaps the handle back instead of
    // leaving it showing an angle the layer does not have.
    Binding {
        target: slider
        property: "value"
        value: root.thetaM
        when: !slider.pressed
        restoreMode: Binding.RestoreNone
    }

    EaElements.Label {
        id: valueLabel
        anchors.verticalCenter: parent.verticalCenter
        width: EaStyle.Sizes.fontPixelSize * 3.5
        horizontalAlignment: Text.AlignRight
        text: root.thetaM.toFixed(1) + "°"
        color: EaStyle.Colors.themeForegroundMinor
    }

    // The reference the arrow is measured from, next to the arrow itself.
    GuideFieldLegend {
        id: guideField
        anchors.verticalCenter: parent.verticalCenter
        glyphSize: root.glyphSize
    }

    MagnetizationArrow {
        anchors.verticalCenter: parent.verticalCenter
        width: root.glyphSize
        height: root.glyphSize
        phi: root.phi
        hasMoment: root.hasMoment
        color: EaStyle.Colors.themeForegroundHovered
        outlineColor: "transparent"
    }

    ToolTip.visible: hover.hovered
    ToolTip.text: root.hasMoment
                  ? qsTr("Moment: %1° from H (θM %2°)").arg(root.phi.toFixed(1)).arg(root.thetaM.toFixed(1))
                    + (root.editable ? '\n' + qsTr("Drag to set θM (%1° steps)").arg(root.snapDegrees)
                                     : '\n' + qsTr("θM follows a constraint or a running fit and cannot be dragged"))
                  : qsTr("ρM is zero: there is no direction to show")

    HoverHandler {
        id: hover
    }
}
