// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCharts

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Charts as EaCharts

import Gui as Gui
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
                measSerie.color: Globals.Variables.experimentColor(
                    Globals.BackendWrapper.analysisExperimentsCurrentIndex
                )
                measSerie.width: 2
                measSerie.opacity: 0.95
                measSerie.style: Qt.DotLine
                bkgSerie.width: 1
                bkgSerie.style: Qt.DotLine

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
                    target: Globals.BackendWrapper.activeBackend ?? null
                    enabled: target !== null
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
                    function onChartAxesResetRequested() {
                        // Reset axes when model is loaded (e.g., from ORSO file)
                        combinedAnalysisResetAxesTimer.start()
                    }
                    function onSamplePageResetAxes() {
                        combinedAnalysisResetAxesTimer.start()
                    }
                }

                Timer {
                    id: combinedAnalysisResetAxesTimer
                    interval: 75
                    repeat: false
                    onTriggered: {
                        analysisChartView.resetAxes()
                        lowerPanel.resetAllAxes()
                    }
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
                    target: Globals.BackendWrapper.activeBackend?.plotting ?? null
                    enabled: target !== null
                    function onReferenceLineVisibilityChanged() {
                        analysisChartView.updateReferenceLines()
                    }
                }

                function updateReferenceLines() {
                    Globals.BackendWrapper.updateRefLines(backgroundRefLine, scaleRefLine, true)
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
                    var xAxis = currentXAxis()

                    // Look up the model color for this experiment
                    var modelColors = Globals.BackendWrapper.modelColorsForExperiment
                    var modelColor = (modelColors && expIndex >= 0 && expIndex < modelColors.length)
                                     ? modelColors[expIndex]
                                     : color

                    // Create measured data series
                    var measuredSerie = analysisChartView.createSeries(ChartView.SeriesTypeLine, 
                                                         `${expName} - Measured`, 
                                                         xAxis, analysisChartView.axisY)
                    measuredSerie.color = color
                    measuredSerie.width = 2
                    measuredSerie.opacity = 0.95
                    measuredSerie.style = Qt.DotLine
                    measuredSerie.capStyle = Qt.RoundCap
                    measuredSerie.useOpenGL = analysisChartView.useOpenGL

                    // Create calculated data series using the model's own color
                    var calculatedSerie = analysisChartView.createSeries(ChartView.SeriesTypeLine,
                                                            `${expName} - Calculated`,
                                                            xAxis, analysisChartView.axisY)
                    calculatedSerie.color = modelColor
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

                // Logarithmic axis control
                property bool useLogQAxis: Globals.Variables.logarithmicQAxis
                axisX.visible: !useLogQAxis

                LogValueAxis {
                    id: analysisAxisXLog
                    visible: analysisChartView.useLogQAxis
                    titleText: "q (Å⁻¹)"
                    property double minAfterReset: Math.max(Globals.BackendWrapper.plottingAnalysisMinX, 1e-6)
                    property double maxAfterReset: Globals.BackendWrapper.plottingAnalysisMaxX * 1.1
                    base: 10
                    color: EaStyle.Colors.chartAxis
                    gridLineColor: EaStyle.Colors.chartGridLine
                    minorGridLineColor: EaStyle.Colors.chartMinorGridLine
                    labelsColor: EaStyle.Colors.chartLabels
                    titleBrush: EaStyle.Colors.chartLabels
                    Component.onCompleted: {
                        min = minAfterReset
                        max = maxAfterReset
                    }
                }

                // Dynamic series for log mode (single experiment)
                property var logModeSeries: null

                function currentXAxis() {
                    return useLogQAxis ? analysisAxisXLog : analysisChartView.axisX
                }

                onUseLogQAxisChanged: {
                    recreateForLogMode()
                }

                function recreateForLogMode() {
                    // Clean up previous log mode series
                    if (logModeSeries) {
                        analysisChartView.removeSeries(logModeSeries.measuredSerie)
                        analysisChartView.removeSeries(logModeSeries.calculatedSerie)
                        logModeSeries = null
                    }

                    if (isMultiExperimentMode) {
                        updateMultiExperimentSeries()
                    } else if (useLogQAxis) {
                        measured.visible = false
                        calculated.visible = false

                        var newMeasured = analysisChartView.createSeries(ChartView.SeriesTypeLine, "measured_log", analysisAxisXLog, analysisChartView.axisY)
                        newMeasured.color = measured.color
                        newMeasured.width = measured.width
                        newMeasured.useOpenGL = analysisChartView.useOpenGL

                        var newCalculated = analysisChartView.createSeries(ChartView.SeriesTypeLine, "calculated_log", analysisAxisXLog, analysisChartView.axisY)
                        newCalculated.color = calculated.color
                        newCalculated.width = calculated.width
                        newCalculated.useOpenGL = analysisChartView.useOpenGL

                        logModeSeries = {
                            measuredSerie: newMeasured,
                            calculatedSerie: newCalculated
                        }

                        Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'measuredSerie', newMeasured)
                        Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'calculatedSerie', newCalculated)
                        Globals.BackendWrapper.plottingRefreshAnalysis()
                    } else {
                        measured.visible = true
                        calculated.visible = true

                        Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'measuredSerie', measured)
                        Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'calculatedSerie', calculated)
                        Globals.BackendWrapper.plottingRefreshAnalysis()
                    }

                    updateReferenceLines()
                    Qt.callLater(resetAxes)
                }

                function resetAxes() {
                    if (useLogQAxis) {
                        if (analysisAxisXLog) {
                            analysisAxisXLog.min = analysisAxisXLog.minAfterReset
                            analysisAxisXLog.max = analysisAxisXLog.maxAfterReset
                        }
                    } else {
                        if (analysisChartView.axisX) {
                            analysisChartView.axisX.min = analysisChartView.axisX.minAfterReset
                            analysisChartView.axisX.max = analysisChartView.axisX.maxAfterReset
                        }
                    }
                    if (analysisChartView.axisY) {
                        analysisChartView.axisY.min = analysisChartView.axisY.minAfterReset
                        analysisChartView.axisY.max = analysisChartView.axisY.maxAfterReset
                    }
                }

                property double yRange: Globals.BackendWrapper.plottingAnalysisMaxY - Globals.BackendWrapper.plottingAnalysisMinY
                axisY.title: "Log10 " + Globals.BackendWrapper.plottingYAxisTitle
                axisY.min: Globals.BackendWrapper.plottingAnalysisMinY - yRange * 0.01
                axisY.max: Globals.BackendWrapper.plottingAnalysisMaxY + yRange * 0.01
                axisY.minAfterReset: Globals.BackendWrapper.plottingAnalysisMinY - yRange * 0.01
                axisY.maxAfterReset: Globals.BackendWrapper.plottingAnalysisMaxY + yRange * 0.01

                calcSerie.onHovered: (point, state) => showMainTooltip(analysisChartView, analysisDataToolTip, point, state)
                calcSerie.color: {
                    const colors = Globals.BackendWrapper.modelColorsForExperiment
                    const idx = Globals.BackendWrapper.analysisExperimentsCurrentIndex

                    if (colors && idx >= 0 && idx < colors.length) {
                        return colors[idx]
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
                            lowerPanel.setAllowZoom(analysisChartView.allowZoom)
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
                            lowerPanel.setAllowZoom(analysisChartView.allowZoom)
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
                            lowerPanel.resetAllAxes()
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
                    Globals.BackendWrapper.plottingRefreshAnalysis()

                    // Initialize multi-experiment support
                    updateMultiExperimentSeries()
                    
                    // Initialize reference lines
                    updateReferenceLines()
                }
            }
        }

        // Lower panel: SLD tab + Residuals tab
        SldView {
            id: lowerPanel

            SplitView.fillHeight: true
            SplitView.preferredHeight: parent.height * 0.33
            SplitView.minimumHeight: 80
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
