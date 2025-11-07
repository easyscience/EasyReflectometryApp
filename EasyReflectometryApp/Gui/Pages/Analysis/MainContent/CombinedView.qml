// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCharts

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Charts as EaCharts

import Gui.Globals as Globals


Rectangle {
    id: container

    color: EaStyle.Colors.chartBackground

    SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical

        // Analysis Chart (2/3 height)
        Rectangle {
            id: analysisContainer
            SplitView.fillHeight: true
            SplitView.preferredHeight: parent.height * 0.67
            SplitView.minimumHeight: 100
            color: EaStyle.Colors.chartBackground

            EaCharts.QtCharts1dMeasVsCalc {
                id: analysisChartView

                property alias calculated: analysisChartView.calcSerie
                property alias measured: analysisChartView.measSerie
                bkgSerie.color: measSerie.color
                measSerie.width: 1
                bkgSerie.width: 1

                anchors.fill: parent
                anchors.topMargin: EaStyle.Sizes.toolButtonHeight - EaStyle.Sizes.fontPixelSize - 1

                useOpenGL: EaGlobals.Vars.useOpenGL
                
                property double xRange: Globals.BackendWrapper.plottingAnalysisMaxX - Globals.BackendWrapper.plottingAnalysisMinX
                axisX.title: "q (Å⁻¹)"
                axisX.min: Globals.BackendWrapper.plottingAnalysisMinX - xRange * 0.01
                axisX.max: Globals.BackendWrapper.plottingAnalysisMaxX + xRange * 0.01
                axisX.minAfterReset: Globals.BackendWrapper.plottingAnalysisMinX - xRange * 0.01
                axisX.maxAfterReset: Globals.BackendWrapper.plottingAnalysisMaxX + xRange * 0.01

                property double yRange: Globals.BackendWrapper.plottingAnalysisMaxY - Globals.BackendWrapper.plottingAnalysisMinY
                axisY.title: "Log10 R(q)"
                axisY.min: Globals.BackendWrapper.plottingAnalysisMinY - yRange * 0.01
                axisY.max: Globals.BackendWrapper.plottingAnalysisMaxY + yRange * 0.01
                axisY.minAfterReset: Globals.BackendWrapper.plottingAnalysisMinY - yRange * 0.01
                axisY.maxAfterReset: Globals.BackendWrapper.plottingAnalysisMaxY + yRange * 0.01

                calcSerie.onHovered: (point, state) => showMainTooltip(analysisChartView, analysisDataToolTip, point, state)
                calcSerie.color: {
                    const models = Globals.BackendWrapper.sampleModels
                    const idx = Globals.BackendWrapper.sampleCurrentModelIndex

                    if (models && idx >= 0 && idx < models.length) {
                        return models[idx].color
                    }

                    return undefined
                }

                // Tool buttons
                Row {
                    id: analysisToolButtons

                    x: analysisChartView.plotArea.x + analysisChartView.plotArea.width - width
                    y: analysisChartView.plotArea.y - height - EaStyle.Sizes.fontPixelSize

                    spacing: 0.25 * EaStyle.Sizes.fontPixelSize

                    EaElements.TabButton {
                        checked: Globals.Variables.showLegendOnAnalysisPage
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "align-left"
                        ToolTip.text: Globals.Variables.showLegendOnAnalysisPage ?
                                          qsTr("Hide legend") :
                                          qsTr("Show legend")
                        onClicked: Globals.Variables.showLegendOnAnalysisPage = checked
                    }

                    EaElements.TabButton {
                        checked: analysisChartView.allowHover
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "comment-alt"
                        ToolTip.text: qsTr("Show coordinates tooltip on hover")
                        onClicked: analysisChartView.allowHover = !analysisChartView.allowHover
                    }

                    Item { height: 1; width: 0.5 * EaStyle.Sizes.fontPixelSize }  // spacer

                    EaElements.TabButton {
                        checked: !analysisChartView.allowZoom
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "arrows-alt"
                        ToolTip.text: qsTr("Enable pan")
                        onClicked: {
                            analysisChartView.allowZoom = !analysisChartView.allowZoom
                            sldChartView.allowZoom = analysisChartView.allowZoom
                        }
                    }

                    EaElements.TabButton {
                        checked: analysisChartView.allowZoom
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "expand"
                        ToolTip.text: qsTr("Enable box zoom")
                        onClicked: {
                            analysisChartView.allowZoom = !analysisChartView.allowZoom
                            sldChartView.allowZoom = analysisChartView.allowZoom
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
                            analysisChartView.resetAxes()
                            sldChartView.resetAxes()
                        }
                    }
                }

                // Legend
                Rectangle {
                    visible: Globals.Variables.showLegendOnAnalysisPage

                    x: analysisChartView.plotArea.x + analysisChartView.plotArea.width - width - EaStyle.Sizes.fontPixelSize
                    y: analysisChartView.plotArea.y + EaStyle.Sizes.fontPixelSize
                    width: childrenRect.width
                    height: childrenRect.height

                    color: EaStyle.Colors.mainContentBackgroundHalfTransparent
                    border.color: EaStyle.Colors.chartGridLine

                    Column {
                        leftPadding: EaStyle.Sizes.fontPixelSize
                        rightPadding: EaStyle.Sizes.fontPixelSize
                        topPadding: EaStyle.Sizes.fontPixelSize * 0.5
                        bottomPadding: EaStyle.Sizes.fontPixelSize * 0.5
                        spacing: EaStyle.Sizes.fontPixelSize * 0.25

                        EaElements.Label {
                            text: '━  I (Measured)'
                            color: analysisChartView.measSerie.color
                        }
                        EaElements.Label {
                            text: '━ (calculated)'
                            color: analysisChartView.calcSerie.color
                        }

                        EaElements.Label {
                            readonly property var selectedIndices: Globals.BackendWrapper.analysisSelectedExperimentIndices || []

                            visible: selectedIndices.length > 1
                            text: qsTr('Selected: %1').arg(selectedIndices.map(index => index + 1).join(', '))
                            color: EaStyle.Colors.themeAccent
                            font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.85
                            wrapMode: Text.NoWrap
                            onSelectedIndicesChanged: console.debug('AnalysisView legend - selected count:', selectedIndices.length)
                        }

                        Rectangle {
                            visible: (Globals.BackendWrapper.analysisExperimentsSelectedCount || 1) > 1
                            width: parent.width - 2 * EaStyle.Sizes.fontPixelSize
                            height: EaStyle.Sizes.fontPixelSize * 3
                            color: "transparent"
                            border.color: EaStyle.Colors.chartGridLine
                            border.width: 1

                            EaElements.Label {
                                anchors.centerIn: parent
                                text: qsTr("Multi-experiment view\n(%1 experiments)")
                                          .arg(Globals.BackendWrapper.analysisExperimentsSelectedCount || 1)
                                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.8
                                color: EaStyle.Colors.themeForegroundHovered
                                horizontalAlignment: Text.AlignHCenter
                            }
                        }
                    }
                }

                EaElements.ToolTip {
                    id: analysisDataToolTip

                    arrowLength: 0
                    textFormat: Text.RichText
                }

                // Data is set in python backend (plotting_1d.py)
                Component.onCompleted: {
                    Globals.References.pages.analysis.mainContent.analysisView = analysisChartView
                    Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage',
                                                                       'measuredSerie',
                                                                       measured)
                    Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage',
                                                                       'calculatedSerie',
                                                                       calculated)
                }

                // Sync X-axis with SLD chart
                onAxisXChanged: syncXAxes()

                Connections {
                    target: analysisChartView.axisX
                    function onMinChanged() { syncXAxes() }
                    function onMaxChanged() { syncXAxes() }
                }
            }
        }

        // SLD Chart (1/3 height)
        Rectangle {
            id: sldContainer
            SplitView.fillHeight: true
            SplitView.preferredHeight: parent.height * 0.33
            SplitView.minimumHeight: 80
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
                    visible: Globals.Variables.showLegendOnAnalysisPage

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
                    Globals.References.pages.analysis.mainContent.sldView = sldChartView
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
        if (analysisChartView.axisX.min !== sldChartView.axisX.min ||
            analysisChartView.axisX.max !== sldChartView.axisX.max) {
            sldChartView.axisX.min = analysisChartView.axisX.min
            sldChartView.axisX.max = analysisChartView.axisX.max
        }
    }
}
