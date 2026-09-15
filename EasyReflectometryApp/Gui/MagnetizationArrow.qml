// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

// One layer's in-plane magnetic moment, drawn as a compass arrow seen along the
// surface normal: screen +x is the guide field H, and `phi` is the physical
// moment direction in degrees counterclockwise from it (see
// `magnetic_vector_for_layer` in the library, which is where phi is defined).
//
// The screen mapping is here and NOWHERE else. phi is counterclockwise in a
// y-up frame; `Item.rotation` is clockwise, so it takes exactly one negation.
// The canvas below draws a right-pointing arrow in local coordinates and
// contains no trigonometry at all, so Canvas's y-down axis never enters the
// picture and the two corrections cannot cancel into a mirrored arrow.
//
// Drawn with Canvas rather than QtQuick.Shapes: the installer excludes the
// Shapes plugin (pyproject.toml).
Item {
    id: root

    // Physical moment direction, degrees counterclockwise from the guide field.
    property real phi: 0
    // False for a magnetic layer whose moment is negligible: the direction of a
    // zero-length vector means nothing, so a hollow dot is drawn instead of an
    // arrow. Not the same as a non-magnetic layer, which draws nothing at all.
    property bool hasMoment: true
    property color color: "black"
    // Thin light outline so the glyph stays readable on a saturated box fill.
    property color outlineColor: Qt.rgba(1, 1, 1, 0.75)

    implicitWidth: 16
    implicitHeight: implicitWidth
    width: implicitWidth
    height: implicitHeight

    rotation: -phi

    onPhiChanged: canvas.requestPaint()
    onHasMomentChanged: canvas.requestPaint()
    onColorChanged: canvas.requestPaint()

    Canvas {
        id: canvas

        anchors.fill: parent
        antialiasing: true

        onPaint: {
            const ctx = getContext("2d")
            ctx.reset()

            const cx = width / 2
            const cy = height / 2
            const half = 0.45 * width
            const head = 0.34 * width

            ctx.lineJoin = "round"
            ctx.lineCap = "round"
            ctx.fillStyle = root.color
            ctx.strokeStyle = root.outlineColor
            ctx.lineWidth = 1

            if (!root.hasMoment) {
                // "Magnetic layer, no moment": a hollow dot, not an arrow.
                ctx.beginPath()
                ctx.arc(cx, cy, 0.16 * width, 0, 2 * Math.PI)
                ctx.strokeStyle = root.color
                ctx.stroke()
                return
            }

            // Shaft, tail at -x, tip at +x.
            ctx.beginPath()
            ctx.moveTo(cx - half, cy)
            ctx.lineTo(cx + half - head, cy)
            ctx.strokeStyle = root.color
            ctx.lineWidth = Math.max(1, 0.1 * width)
            ctx.stroke()

            // Head, pointing at +x.
            ctx.beginPath()
            ctx.moveTo(cx + half, cy)
            ctx.lineTo(cx + half - head, cy - 0.5 * head)
            ctx.lineTo(cx + half - head, cy + 0.5 * head)
            ctx.closePath()
            ctx.fill()
            ctx.lineWidth = 1
            ctx.strokeStyle = root.outlineColor
            ctx.stroke()
        }
    }
}
