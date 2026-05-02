// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import EasyApplication.Gui.Style as EaStyle

import Gui as Gui
import Gui.Globals as Globals


Item {
    id: root

    // Expose the SLD chartView so existing Globals.References remain valid
    readonly property alias sldChartView: sldChart.chartView

    // Called by CombinedView to reset both lower tabs together
    function resetAllAxes() {
        sldChart.chartView.resetAxes()
        if (spinAsymmetryLoader.item) {
            spinAsymmetryLoader.item.chartView.resetAxes()
        }
        residualsView.chartView.resetAxes()
    }

    // Called by CombinedView to sync pan/zoom mode from the top toolbar
    function setAllowZoom(value) {
        sldChart.chartView.allowZoom = value
        if (spinAsymmetryLoader.item) {
            spinAsymmetryLoader.item.setAllowZoom(value)
        }
        residualsView.chartView.allowZoom = value
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        TabBar {
            id: tabBar
            Layout.fillWidth: true
            Layout.preferredHeight: EaStyle.Sizes.toolButtonHeight

            background: Rectangle { color: EaStyle.Colors.chartBackground }

            TabButton {
                text: qsTr("SLD")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                implicitHeight: EaStyle.Sizes.toolButtonHeight
            }
            TabButton {
                visible: Globals.BackendWrapper.polarizationAvailable
                width: visible ? implicitWidth : 0
                text: qsTr("Spin asymmetry")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                implicitHeight: EaStyle.Sizes.toolButtonHeight
            }
            TabButton {
                text: qsTr("Residuals")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                implicitHeight: EaStyle.Sizes.toolButtonHeight
            }
        }

        StackLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            currentIndex: Globals.BackendWrapper.polarizationAvailable ?
                          tabBar.currentIndex :
                          (tabBar.currentIndex === 0 ? 0 : 2)

            Gui.SldChart {
                id: sldChart
                showLegend: Globals.Variables.showLegendOnAnalysisPage
                onShowLegendChanged: Globals.Variables.showLegendOnAnalysisPage = showLegend
            }

            Loader {
                id: spinAsymmetryLoader
                active: Globals.BackendWrapper.polarizationAvailable
                source: "SpinAsymmetryView.qml"

                onActiveChanged: {
                    if (!active && tabBar.currentIndex === 1) {
                        tabBar.currentIndex = 0
                    }
                }
            }

            ResidualsView {
                id: residualsView
                showLegend: Globals.Variables.showLegendOnAnalysisResidualsTab
                onShowLegendChanged: Globals.Variables.showLegendOnAnalysisResidualsTab = showLegend
            }
        }
    }

    Component.onCompleted: {
        Globals.References.pages.analysis.mainContent.sldView = sldChart.chartView
    }
}

