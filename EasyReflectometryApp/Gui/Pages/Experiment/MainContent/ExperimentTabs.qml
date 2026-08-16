// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import EasyApplication.Gui.Style as EaStyle

import Gui as Gui
import Gui.Globals as Globals

// The Experiment page's main content: the reflectivity chart, plus a spin
// asymmetry tab for an experiment that measured both non-spin-flip channels.
// While SA is unavailable the tab strip has no height and no buttons, so the
// page looks exactly as it did before polarized support existed.
Item {
    id: root

    readonly property bool spinAsymmetryAvailable: Globals.BackendWrapper.plottingSpinAsymmetryAvailable

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TabBar {
            id: tabBar

            visible: root.spinAsymmetryAvailable
            Layout.fillWidth: true
            Layout.preferredHeight: root.spinAsymmetryAvailable ? EaStyle.Sizes.toolButtonHeight : 0

            background: Rectangle { color: EaStyle.Colors.chartBackground }

            TabButton {
                text: qsTr("Reflectivity")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                implicitHeight: EaStyle.Sizes.toolButtonHeight
            }
            TabButton {
                text: qsTr("Spin asymmetry")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                implicitHeight: EaStyle.Sizes.toolButtonHeight
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            // Falling back to the reflectivity chart also covers the case where
            // SA disappears while its tab is selected.
            currentIndex: root.spinAsymmetryAvailable ? tabBar.currentIndex : 0

            ExperimentView {}

            Gui.SpinAsymmetryChart {
                // Measured only: the model curve belongs on the Analysis page,
                // this is the "do I have a magnetic signal?" view.
                showCalculated: false
                showLegend: Globals.Variables.showLegendOnExperimentPage
                onShowLegendChanged: Globals.Variables.showLegendOnExperimentPage = showLegend
            }
        }
    }

    onSpinAsymmetryAvailableChanged: {
        if (!spinAsymmetryAvailable) {
            tabBar.currentIndex = 0
        }
    }
}
