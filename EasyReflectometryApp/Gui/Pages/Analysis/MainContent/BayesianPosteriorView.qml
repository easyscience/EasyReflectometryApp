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

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: EaStyle.Sizes.fontPixelSize
        spacing: EaStyle.Sizes.fontPixelSize

        // Convergence summary header
        EaElements.Label {
            visible: Globals.BackendWrapper.bayesianResultAvailable
                     && Globals.BackendWrapper.bayesianPosterior !== null
            text: "Bayesian MCMC Sampling Results\n"
                + "Posterior draws: " + Globals.BackendWrapper.bayesianPosterior.nDraws
                + "  |  Parameters: " + Globals.BackendWrapper.bayesianPosterior.paramNames.join(", ")
            wrapMode: Text.WordWrap
        }

        EaElements.Label {
            visible: !Globals.BackendWrapper.bayesianResultAvailable
            text: qsTr("No Bayesian results available. Run a BUMPS-DREAM sampling to see posterior distributions.")
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.WordWrap
        }

        // Marginal histograms grid
        Flow {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: EaStyle.Sizes.fontPixelSize * 0.5

            Repeater {
                model: Globals.BackendWrapper.bayesianMarginals

                delegate: Rectangle {
                    width: Math.max(200, Math.min(400, container.width / 2 - EaStyle.Sizes.fontPixelSize))
                    height: 220
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
                            horizontalAlignment: Text.AlignHCenter
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
                            }
                            ValueAxis {
                                id: yAxis
                                min: 0
                            }

                            BarSeries {
                                id: barSeries
                                axisX: xAxis
                                axisY: yAxis
                                barWidth: 0.9
                                BarSet {
                                    label: modelData.name
                                    values: modelData.counts
                                    color: "#3498db"
                                }
                            }

                            Component.onCompleted: {
                                // Set x-axis range from bin centers
                                if (modelData.binCenters && modelData.binCenters.length > 0) {
                                    xAxis.min = modelData.binCenters[0]
                                    xAxis.max = modelData.binCenters[modelData.binCenters.length - 1]
                                }
                                yAxis.max = Math.max.apply(null, modelData.counts) * 1.1
                            }
                        }
                    }
                }
            }
        }
    }
}
