// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


Rectangle {
    id: container

    color: EaStyle.Colors.chartBackground

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        // Convergence summary header
        EaElements.Label {
            Layout.fillWidth: true
            Layout.margins: EaStyle.Sizes.fontPixelSize
            visible: Globals.BackendWrapper.bayesianResultAvailable
                     && Globals.BackendWrapper.bayesianPosterior !== null
            text: {
                if (!Globals.BackendWrapper.bayesianPosterior) return ''
                const pp = Globals.BackendWrapper.bayesianPosterior
                return 'Bayesian MCMC Sampling Results\n'
                    + 'Posterior draws: ' + pp.nDraws
            }
            wrapMode: Text.WordWrap
        }

        EaElements.Label {
            Layout.fillWidth: true
            Layout.margins: EaStyle.Sizes.fontPixelSize
            visible: !Globals.BackendWrapper.bayesianResultAvailable
            text: qsTr("No Bayesian results available. Run a BUMPS-DREAM sampling to see posterior distributions.")
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.WordWrap
        }

        // Subtab bar
        TabBar {
            id: subtabBar
            Layout.fillWidth: true
            Layout.preferredHeight: EaStyle.Sizes.toolButtonHeight
            background: Rectangle { color: EaStyle.Colors.chartBackground }

            TabButton {
                text: qsTr("Marginals")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                implicitHeight: EaStyle.Sizes.toolButtonHeight
            }
            TabButton {
                text: qsTr("Corner Plot")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                implicitHeight: EaStyle.Sizes.toolButtonHeight
            }
            TabButton {
                text: qsTr("Traces")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                implicitHeight: EaStyle.Sizes.toolButtonHeight
            }
            TabButton {
                text: qsTr("2D Heatmap")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                implicitHeight: EaStyle.Sizes.toolButtonHeight
            }
            TabButton {
                text: qsTr("Diagnostics")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                implicitHeight: EaStyle.Sizes.toolButtonHeight
            }
        }

        // Sub-view stack
        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: subtabBar.currentIndex

            BayesianMarginalsView { }
            BayesianCornerView { }
            BayesianTraceView { }
            BayesianHeatmapView { }
            BayesianDiagnosticsView { }
        }
    }
}
