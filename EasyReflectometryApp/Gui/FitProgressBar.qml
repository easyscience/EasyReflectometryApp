// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

import EasyApplication.Gui.Style as EaStyle

// A thin progress bar for fitting and sampling, fed with the backend's progress map
// (`analysisFitProgress`). Built from plain rectangles: the native Controls style the
// app runs refuses a customised ProgressBar. A known fraction (0..1) fills the track;
// an unknown one (-1, a fit has no knowable end) sweeps a short segment across it.
Rectangle {
    id: bar

    property var progress: ({ phase: '', fraction: -1 })

    readonly property bool indeterminate: !(progress.fraction >= 0)
    // Animated while the fraction is unknown: 0..1 across the track.
    property real sweep: 0

    implicitHeight: 3
    clip: true
    color: EaStyle.Colors.appBorder
    // Cancelling: still busy, but no longer making progress.
    opacity: progress.phase === 'cancelling' ? 0.4 : 1

    Rectangle {
        id: fill

        height: bar.height
        width: bar.indeterminate ? bar.width / 4 : bar.width * Math.min(bar.progress.fraction, 1)
        x: bar.indeterminate ? bar.sweep * (bar.width + width) - width : 0
        color: EaStyle.Colors.themeAccent
    }

    NumberAnimation on sweep {
        running: bar.indeterminate && bar.visible
        loops: Animation.Infinite
        from: 0
        to: 1
        duration: 1500
    }
}
