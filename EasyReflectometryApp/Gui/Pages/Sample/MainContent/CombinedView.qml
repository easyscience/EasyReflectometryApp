// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtCharts

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Charts as EaCharts

import Gui.Globals as Globals


Rectangle {
    id: container

    color: EaStyle.Colors.chartBackground

    Column {
        anchors.fill: parent
        spacing: 0

        // Sample Chart (2/3 height)
        Rectangle {
            id: sampleContainer
            width: parent.width
            height: parent.height * 0.67
            color: EaStyle.Colors.chartBackground

            EaCharts.QtCharts1dMeasVsCalc {
                id: sampleChartView

                anchors.fill: parent
                anchors.topMargin: EaStyle.Sizes.toolButtonHeight - EaStyle.Sizes.fontPixelSize - 1

                useOpenGL: EaGlobals.Vars.useOpenGL
                
                property double xRange: Globals.BackendWrapper.plottingSampleMaxX - Globals.BackendWrapper.plottingSampleMinX
                axisX.title: "q (Å⁻¹)"
                axisX.min: Globals.BackendWrapper.plottingSampleMinX - xRange * 0.01
                axisX.max: Globals.BackendWrapper.plottingSampleMaxX + xRange * 0.01
                axisX.minAfterReset: Globals.BackendWrapper.plottingSampleMinX - xRange * 0.01
                axisX.maxAfterReset: Globals.BackendWrapper.plottingSampleMaxX + xRange * 0.01

                property double yRange: Globals.BackendWrapper.plottingSampleMaxY - Globals.BackendWrapper.plottingSampleMinY
                axisY.title: "Log10 R(q)"
                axisY.min: Globals.BackendWrapper.plottingSampleMinY - yRange * 0.01
                axisY.max: Globals.BackendWrapper.plottingSampleMaxY + yRange * 0.01
                axisY.minAfterReset: Globals.BackendWrapper.plottingSampleMinY - yRange * 0.01
                axisY.maxAfterReset: Globals.BackendWrapper.plottingSampleMaxY + yRange * 0.01

                calcSerie.onHovered: (point, state) => showMainTooltip(sampleChartView, sampleDataToolTip, point, state)

                calcSerie.color: {
                    var idx = Globals.BackendWrapper.sampleCurrentModelIndex
                    Globals.BackendWrapper.sampleModels[idx].color
                }

                // Tool buttons
                Row {
                    id: sampleToolButtons

                    x: sampleChartView.plotArea.x + sampleChartView.plotArea.width - width
                    y: sampleChartView.plotArea.y - height - EaStyle.Sizes.fontPixelSize

                    spacing: 0.25 * EaStyle.Sizes.fontPixelSize

                    EaElements.TabButton {
                        checked: Globals.Variables.showLegendOnSamplePage
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "align-left"
                        ToolTip.text: Globals.Variables.showLegendOnSamplePage ?
                                          qsTr("Hide legend") :
                                          qsTr("Show legend")
                        onClicked: Globals.Variables.showLegendOnSamplePage = checked
                    }

                    EaElements.TabButton {
                        checked: sampleChartView.allowHover
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "comment-alt"
                        ToolTip.text: qsTr("Show coordinates tooltip on hover")
                        onClicked: sampleChartView.allowHover = !sampleChartView.allowHover
                    }

                    Item { height: 1; width: 0.5 * EaStyle.Sizes.fontPixelSize }  // spacer

                    EaElements.TabButton {
                        checked: !sampleChartView.allowZoom
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "arrows-alt"
                        ToolTip.text: qsTr("Enable pan")
                        onClicked: {
                            sampleChartView.allowZoom = !sampleChartView.allowZoom
                            sldChartView.allowZoom = sampleChartView.allowZoom
                        }
                    }

                    EaElements.TabButton {
                        checked: sampleChartView.allowZoom
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "expand"
                        ToolTip.text: qsTr("Enable box zoom")
                        onClicked: {
                            sampleChartView.allowZoom = !sampleChartView.allowZoom
                            sldChartView.allowZoom = sampleChartView.allowZoom
                        }
                    }

                    EaElements.TabButton {
                        checkable: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "backspace"
                        ToolTip.text: qsTr("Reset axes")
                        onClicked: {
                            sampleChartView.resetAxes()
                            sldChartView.resetAxes()
                        }
                    }
                }

                // Legend
                Rectangle {
                    visible: Globals.Variables.showLegendOnSamplePage

                    x: sampleChartView.plotArea.x + sampleChartView.plotArea.width - width - EaStyle.Sizes.fontPixelSize
                    y: sampleChartView.plotArea.y + EaStyle.Sizes.fontPixelSize
                    width: childrenRect.width
                    height: childrenRect.height

                    color: EaStyle.Colors.mainContentBackgroundHalfTransparent
                    border.color: EaStyle.Colors.chartGridLine

                    Column {
                        leftPadding: EaStyle.Sizes.fontPixelSize
                        rightPadding: EaStyle.Sizes.fontPixelSize
                        topPadding: EaStyle.Sizes.fontPixelSize * 0.5
                        bottomPadding: EaStyle.Sizes.fontPixelSize * 0.5

                        EaElements.Label {
                            text: '━  I (sample)'
                            color: sampleChartView.calcSerie.color
                        }
                    }
                }

                EaElements.ToolTip {
                    id: sampleDataToolTip

                    arrowLength: 0
                    textFormat: Text.RichText
                }

                // Data is set in python backend (plotting_1d.py)
                Component.onCompleted: {
                    Globals.References.pages.sample.mainContent.sampleView = sampleChartView
                    Globals.BackendWrapper.plottingSetQtChartsSerieRef('samplePage',
                                                                       'sampleSerie',
                                                                       sampleChartView.calcSerie)
                    Globals.BackendWrapper.plottingRefreshSample()
                }

                // Sync X-axis with SLD chart
                onAxisXChanged: syncXAxes()

                Connections {
                    target: sampleChartView.axisX
                    function onMinChanged() { syncXAxes() }
                    function onMaxChanged() { syncXAxes() }
                }
            }
        }

        // SLD Chart (1/3 height)
        Rectangle {
            id: sldContainer
            width: parent.width
            height: parent.height * 0.33
            color: EaStyle.Colors.chartBackground

            EaCharts.QtCharts1dMeasVsCalc {
                id: sldChartView

                anchors.fill: parent
                anchors.topMargin: EaStyle.Sizes.toolButtonHeight - EaStyle.Sizes.fontPixelSize - 1

                useOpenGL: EaGlobals.Vars.useOpenGL

                property double xRange: Globals.BackendWrapper.plottingSldMaxX - Globals.BackendWrapper.plottingSldMinX
                axisX.title: "z (Å)"
                axisX.min: Globals.BackendWrapper.plottingSldMinX - xRange * 0.01
                axisX.max: Globals.BackendWrapper.plottingSldMaxX + xRange * 0.01
                axisX.minAfterReset: Globals.BackendWrapper.plottingSldMinX - xRange * 0.01
                axisX.maxAfterReset: Globals.BackendWrapper.plottingSldMaxX + xRange * 0.01

                property double yRange: Globals.BackendWrapper.plottingSldMaxY - Globals.BackendWrapper.plottingSldMinY
                axisY.title: "SLD (10⁻⁶Å⁻²)"
                axisY.min: Globals.BackendWrapper.plottingSldMinY - yRange * 0.01
                axisY.max: Globals.BackendWrapper.plottingSldMaxY + yRange * 0.01
                axisY.minAfterReset: Globals.BackendWrapper.plottingSldMinY - yRange * 0.01
                axisY.maxAfterReset: Globals.BackendWrapper.plottingSldMaxY + yRange * 0.01

                calcSerie.onHovered: (point, state) => showMainTooltip(sldChartView, sldDataToolTip, point, state)
                calcSerie.color: {
                    const models = Globals.BackendWrapper.sampleModels
                    const idx = Globals.BackendWrapper.sampleCurrentModelIndex

                    if (models && idx >= 0 && idx < models.length) {
                        return models[idx].color
                    }

                    return undefined
                }

                // Legend
                Rectangle {
                    visible: Globals.Variables.showLegendOnSamplePage

                    x: sldChartView.plotArea.x + sldChartView.plotArea.width - width - EaStyle.Sizes.fontPixelSize
                    y: sldChartView.plotArea.y + EaStyle.Sizes.fontPixelSize
                    width: childrenRect.width
                    height: childrenRect.height

                    color: EaStyle.Colors.mainContentBackgroundHalfTransparent
                    border.color: EaStyle.Colors.chartGridLine

                    Column {
                        leftPadding: EaStyle.Sizes.fontPixelSize
                        rightPadding: EaStyle.Sizes.fontPixelSize
                        topPadding: EaStyle.Sizes.fontPixelSize * 0.5
                        bottomPadding: EaStyle.Sizes.fontPixelSize * 0.5

                        EaElements.Label {
                            text: '━  SLD'
                            color: sldChartView.calcSerie.color
                        }
                    }
                }

                EaElements.ToolTip {
                    id: sldDataToolTip

                    arrowLength: 0
                    textFormat: Text.RichText
                }

                // Data is set in python backend (plotting_1d.py)
                Component.onCompleted: {
                    Globals.References.pages.sample.mainContent.sldView = sldChartView
                    Globals.BackendWrapper.plottingSetQtChartsSerieRef('samplePage',
                                                                       'sldSerie',
                                                                       sldChartView.calcSerie)
                    Globals.BackendWrapper.plottingRefreshSLD()
                }
            }
        }
    }

    // Logic
    function showMainTooltip(chart, tooltip, point, state) {
        if (!chart.allowHover) {
            return
        }
        const pos = chart.mapToPosition(Qt.point(point.x, point.y))
        tooltip.x = pos.x
        tooltip.y = pos.y
        tooltip.text = `<p align="left">x: ${point.x.toFixed(3)}<br\>y: ${point.y.toFixed(3)}</p>`
        tooltip.parent = chart
        tooltip.visible = state
    }

    function syncXAxes() {
        // Keep both charts' X axes synchronized
        if (sampleChartView.axisX.min !== sldChartView.axisX.min ||
            sampleChartView.axisX.max !== sldChartView.axisX.max) {
            sldChartView.axisX.min = sampleChartView.axisX.min
            sldChartView.axisX.max = sampleChartView.axisX.max
        }
    }
}
