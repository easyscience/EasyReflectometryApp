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

                // Multi-experiment support
                property var multiExperimentSeries: []
                property bool isMultiExperimentMode: {
                    try {
                        return Globals.BackendWrapper.plottingIsMultiExperimentMode || false
                    } catch (e) {
                        return false
                    }
                }

                // Watch for changes in multi-experiment mode property
                onIsMultiExperimentModeChanged: {
                    updateMultiExperimentSeries()
                }

                // Watch for changes in multi-experiment selection
                Connections {
                    target: Globals.BackendWrapper.activeBackend
                    function onMultiExperimentSelectionChanged() {
                        analysisChartView.updateMultiExperimentSeries()
                    }
                }

                // Watch for plot mode changes (R(q)×q⁴ toggle)
                Connections {
                    target: Globals.BackendWrapper
                    function onPlotModeChanged() {
                        console.debug("CombinedView Analysis: Plot mode changed, refreshing chart")
                        Globals.BackendWrapper.plottingRefreshAnalysis()
                        // Delay resetAxes to allow axis range properties to update first
                        combinedAnalysisResetAxesTimer.start()
                    }
                }

                Timer {
                    id: combinedAnalysisResetAxesTimer
                    interval: 50
                    repeat: false
                    onTriggered: analysisChartView.resetAxes()
                }

                // Background reference line series
                LineSeries {
                    id: backgroundRefLine
                    axisX: analysisChartView.axisX
                    axisY: analysisChartView.axisY
                    useOpenGL: analysisChartView.useOpenGL
                    color: "#888888"
                    width: 1
                    style: Qt.DashLine
                    visible: Globals.BackendWrapper.plottingBkgShown
                }

                // Scale reference line series
                LineSeries {
                    id: scaleRefLine
                    axisX: analysisChartView.axisX
                    axisY: analysisChartView.axisY
                    useOpenGL: analysisChartView.useOpenGL
                    color: "#666666"
                    width: 1
                    style: Qt.DotLine
                    visible: Globals.BackendWrapper.plottingScaleShown
                }

                // Update reference lines when visibility changes
                Connections {
                    target: Globals.BackendWrapper.activeBackend.plotting
                    function onReferenceLineVisibilityChanged() {
                        analysisChartView.updateReferenceLines()
                    }
                }

                function updateReferenceLines() {
                    // Update background line
                    backgroundRefLine.clear()
                    if (Globals.BackendWrapper.plottingBkgShown) {
                        var bkgData = Globals.BackendWrapper.plottingGetBackgroundData()
                        for (var i = 0; i < bkgData.length; i++) {
                            backgroundRefLine.append(bkgData[i].x, bkgData[i].y)
                        }
                    }

                    // Update scale line
                    scaleRefLine.clear()
                    if (Globals.BackendWrapper.plottingScaleShown) {
                        var scaleData = Globals.BackendWrapper.plottingGetScaleData()
                        for (var j = 0; j < scaleData.length; j++) {
                            scaleRefLine.append(scaleData[j].x, scaleData[j].y)
                        }
                    }
                }

                // Multi-experiment series management
                function updateMultiExperimentSeries() {
                    // Always get the latest value from backend
                    var isMultiExp = false
                    try {
                        isMultiExp = Globals.BackendWrapper.plottingIsMultiExperimentMode || false
                    } catch (e) {
                        isMultiExp = false
                    }

                    // Clear existing multi-experiment series
                    clearMultiExperimentSeries()

                    if (!isMultiExp) {
                        // Show default series for single experiment
                        measured.visible = true
                        calculated.visible = true
                        return
                    }

                    // Get experiment data list
                    var experimentDataList = Globals.BackendWrapper.plottingIndividualExperimentDataList

                    // If no data available yet, keep default series visible as fallback
                    if (experimentDataList.length === 0) {
                        measured.visible = true
                        calculated.visible = true
                        return
                    }

                    // Hide default series in multi-experiment mode (only after we have data)
                    measured.visible = false
                    calculated.visible = false

                    // Create series for each experiment
                    for (var i = 0; i < experimentDataList.length; i++) {
                        var expData = experimentDataList[i]
                        if (expData.hasData) {
                            createExperimentSeries(expData.index, expData.name, expData.color)
                        }
                    }
                }

                function clearMultiExperimentSeries() {
                    // Remove all dynamically created series
                    for (var i = 0; i < multiExperimentSeries.length; i++) {
                        var seriesSet = multiExperimentSeries[i]
                        if (seriesSet.measuredSerie) {
                            analysisChartView.removeSeries(seriesSet.measuredSerie)
                        }
                        if (seriesSet.calculatedSerie) {
                            analysisChartView.removeSeries(seriesSet.calculatedSerie)
                        }
                    }
                    multiExperimentSeries = []
                }

                function createExperimentSeries(expIndex, expName, color) {
                    // Create measured data series
                    var measuredSerie = analysisChartView.createSeries(ChartView.SeriesTypeLine, 
                                                         `${expName} - Measured`, 
                                                         analysisChartView.axisX, analysisChartView.axisY)
                    measuredSerie.color = color
                    measuredSerie.width = 1
                    measuredSerie.capStyle = Qt.RoundCap
                    measuredSerie.useOpenGL = analysisChartView.useOpenGL

                    // Create calculated data series (slightly different style)
                    var calculatedSerie = analysisChartView.createSeries(ChartView.SeriesTypeLine,
                                                            `${expName} - Calculated`,
                                                            analysisChartView.axisX, analysisChartView.axisY)
                    calculatedSerie.color = color
                    calculatedSerie.width = 2
                    calculatedSerie.capStyle = Qt.RoundCap
                    calculatedSerie.useOpenGL = analysisChartView.useOpenGL

                    // Store references
                    var seriesSet = {
                        measuredSerie: measuredSerie,
                        calculatedSerie: calculatedSerie,
                        expIndex: expIndex,
                        expName: expName,
                        color: color
                    }
                    multiExperimentSeries.push(seriesSet)

                    // Populate with data
                    populateExperimentSeries(seriesSet)
                }

                function populateExperimentSeries(seriesSet) {
                    // Get data points from backend (includes both measured and calculated)
                    var dataPoints = Globals.BackendWrapper.plottingGetAnalysisDataPoints(seriesSet.expIndex)

                    // Clear existing points
                    seriesSet.measuredSerie.clear()
                    seriesSet.calculatedSerie.clear()

                    // Add data points
                    for (var i = 0; i < dataPoints.length; i++) {
                        var point = dataPoints[i]
                        seriesSet.measuredSerie.append(point.x, point.measured)
                        seriesSet.calculatedSerie.append(point.x, point.calculated)
                    }
                }
                
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

                        // Single experiment legend
                        EaElements.Label {
                            visible: !analysisChartView.isMultiExperimentMode
                            text: '━  I (Measured)'
                            color: analysisChartView.measSerie.color
                        }
                        EaElements.Label {
                            visible: !analysisChartView.isMultiExperimentMode
                            text: '━ (Calculated)'
                            color: analysisChartView.calcSerie.color
                        }

                        // Multi-experiment legend
                        Column {
                            visible: analysisChartView.isMultiExperimentMode
                            spacing: EaStyle.Sizes.fontPixelSize * 0.2

                            EaElements.Label {
                                text: qsTr("Multi-experiment view:")
                                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                                font.bold: true
                                color: EaStyle.Colors.themeForeground
                            }

                            Repeater {
                                model: analysisChartView.isMultiExperimentMode ? Globals.BackendWrapper.plottingIndividualExperimentDataList : []
                                delegate: Row {
                                    spacing: EaStyle.Sizes.fontPixelSize * 0.3

                                    Rectangle {
                                        width: EaStyle.Sizes.fontPixelSize * 0.8
                                        height: 3
                                        color: modelData.color || "#1f77b4"
                                        anchors.verticalCenter: parent.verticalCenter
                                    }

                                    EaElements.Label {
                                        text: modelData.name || `Exp ${index + 1}`
                                        font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.8
                                        color: EaStyle.Colors.themeForeground
                                        anchors.verticalCenter: parent.verticalCenter
                                    }
                                }
                            }

                            Rectangle {
                                width: parent.width - 2 * EaStyle.Sizes.fontPixelSize
                                height: 1
                                color: EaStyle.Colors.chartGridLine
                            }

                            EaElements.Label {
                                text: qsTr("━ Measured (thin)")
                                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.7
                                color: EaStyle.Colors.themeForegroundMinor
                            }
                            EaElements.Label {
                                text: qsTr("━ Calculated (thick)")
                                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.7
                                color: EaStyle.Colors.themeForegroundMinor
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

                    // Initialize multi-experiment support
                    updateMultiExperimentSeries()
                    
                    // Initialize reference lines
                    updateReferenceLines()
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
                    Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage',
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
}
