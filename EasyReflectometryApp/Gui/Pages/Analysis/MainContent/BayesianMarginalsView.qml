// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCharts

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


Rectangle {
    id: container

    color: EaStyle.Colors.chartBackground

    EaElements.Label {
        anchors.centerIn: parent
        visible: !Globals.BackendWrapper.bayesianResultAvailable
        text: qsTr("No Bayesian results available.")
        color: EaStyle.Colors.themeForegroundMinor
    }

    GridLayout {
        anchors.fill: parent
        anchors.margins: EaStyle.Sizes.fontPixelSize
        columnSpacing: EaStyle.Sizes.fontPixelSize * 0.5
        rowSpacing: EaStyle.Sizes.fontPixelSize * 0.5
        columns: Math.min(3, Globals.BackendWrapper.bayesianMarginals.length || 1)
        visible: Globals.BackendWrapper.bayesianResultAvailable

        Repeater {
            model: Globals.BackendWrapper.bayesianMarginals

            delegate: Rectangle {
                Layout.fillWidth: true
                Layout.fillHeight: true
                Layout.preferredWidth: 300
                Layout.preferredHeight: 220
                color: EaStyle.Colors.chartBackground
                border.color: EaStyle.Colors.chartGridLine
                border.width: 1

                ColumnLayout {
                    anchors.fill: parent
                    anchors.margins: 4
                    spacing: 2

                    EaElements.Label {
                        Layout.fillWidth: true
                        text: modelData.name
                                + "  (" + Number(modelData.mean).toFixed(4)
                                + " ± " + Number(modelData.std).toFixed(4) + ")"
                                + "\n95% CI: [" + Number(modelData.ci_low).toFixed(4)
                                + ", " + Number(modelData.ci_high).toFixed(4) + "]"
                        horizontalAlignment: Text.AlignHCenter
                        font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.85
                        wrapMode: Text.WordWrap
                    }

                    ChartView {
                        id: histogramChart
                        Layout.fillWidth: true
                        Layout.fillHeight: true
                        legend.visible: false
                        antialiasing: true
                        backgroundColor: "transparent"

                        ValueAxis {
                            id: xAxis
                            titleText: modelData.name
                            labelsFont.pixelSize: EaStyle.Sizes.fontPixelSize * 0.75
                        }
                        ValueAxis {
                            id: yAxis
                            min: 0
                            labelsFont.pixelSize: EaStyle.Sizes.fontPixelSize * 0.75
                        }

                        BarSeries {
                            id: barSeries
                            axisX: xAxis
                            axisY: yAxis
                            barWidth: 0.9
                            BarSet {
                                label: modelData.name
                                values: modelData.counts
                                color: EaStyle.Colors.themeAccent || "#3498db"
                            }
                        }

                        Component.onCompleted: {
                            if (modelData.binCenters && modelData.binCenters.length > 0) {
                                xAxis.min = modelData.binCenters[0]
                                xAxis.max = modelData.binCenters[modelData.binCenters.length - 1]
                            }
                            if (modelData.counts && modelData.counts.length > 0) {
                                yAxis.max = Math.max.apply(null, modelData.counts) * 1.1
                            }
                        }
                    }
                }
            }
        }
    }
}
