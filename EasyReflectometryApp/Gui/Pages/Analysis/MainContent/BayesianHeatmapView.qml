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

    onVisibleChanged: if (visible) updateHeatmap()

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: EaStyle.Sizes.fontPixelSize
        spacing: EaStyle.Sizes.fontPixelSize

        // Parameter selection row + save button
        RowLayout {
            Layout.fillWidth: true
            visible: Globals.BackendWrapper.bayesianResultAvailable

            EaElements.Label {
                text: qsTr("X-axis:")
            }
            EaElements.ComboBox {
                id: paramXCombo
                Layout.fillWidth: true
                model: Globals.BackendWrapper.bayesianParamNames
                onCurrentIndexChanged: updateHeatmap()
            }
            EaElements.Label {
                text: qsTr("Y-axis:")
            }
            EaElements.ComboBox {
                id: paramYCombo
                Layout.fillWidth: true
                model: Globals.BackendWrapper.bayesianParamNames
                currentIndex: Math.min(1, model ? model.length - 1 : 0)
                onCurrentIndexChanged: updateHeatmap()
            }

            EaElements.Button {
                text: qsTr("Save")
                enabled: Globals.BackendWrapper.bayesianHeatmapPlotUrl !== ''
                onClicked: Globals.BackendWrapper.bayesianSavePlot(
                    Globals.BackendWrapper.bayesianHeatmapPlotUrl
                )
            }
        }

        // Heatmap image (rendered as PNG via matplotlib)
        Image {
            id: heatmapImage
            Layout.fillWidth: true
            Layout.fillHeight: true
            fillMode: Image.PreserveAspectFit
            source: Globals.BackendWrapper.bayesianHeatmapPlotUrl || ''
            cache: false
            visible: source !== ''
        }

        // Placeholder: no results available
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: !Globals.BackendWrapper.bayesianResultAvailable

            EaElements.Label {
                anchors.centerIn: parent
                text: qsTr("No Bayesian results available.")
                color: EaStyle.Colors.themeForegroundMinor
            }
        }

        // Placeholder: results available but no parameters loaded
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: Globals.BackendWrapper.bayesianResultAvailable
                     && heatmapImage.source === ''

            EaElements.Label {
                anchors.centerIn: parent
                text: qsTr("Select two parameters above to display the joint posterior density.")
                color: EaStyle.Colors.themeForegroundMinor
            }
        }
    }

    function updateHeatmap() {
        if (paramXCombo.currentIndex >= 0 && paramYCombo.currentIndex >= 0) {
            Globals.BackendWrapper.bayesianComputeHeatmap(
                paramXCombo.currentIndex, paramYCombo.currentIndex
            )
        }
    }

    Component.onCompleted: updateHeatmap()
}
