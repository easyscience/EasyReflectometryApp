// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtCharts

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Charts as EaCharts

import Gui.Globals as Globals
import "../../../Logic/MeasuredScatter.js" as MeasuredScatter


Rectangle {
    id: container

    color: EaStyle.Colors.chartBackground
    EaCharts.QtCharts1dMeasVsCalc {
        id: chartView

        property alias calculated: chartView.calcSerie
        property alias measured: chartView.measSerie
        bkgSerie.color: measSerie.color
        measSerie.color: Globals.Variables.experimentColor(
            Globals.BackendWrapper.analysisExperimentsCurrentIndex
        )
        measSerie.width: 2
        measSerie.opacity: 0.95
        measSerie.style: Qt.DotLine
        bkgSerie.width: 1
        bkgSerie.style: Qt.DotLine

        // Track current experiment color for scatter series
        property color currentExperimentColor: Globals.Variables.experimentColor(
            Globals.BackendWrapper.analysisExperimentsCurrentIndex
        )
        onCurrentExperimentColorChanged: MeasuredScatter.setColor(measuredScatterSerie, currentExperimentColor)

        anchors.topMargin: EaStyle.Sizes.toolButtonHeight - EaStyle.Sizes.fontPixelSize - 1

        useOpenGL: EaGlobals.Vars.useOpenGL

        // Background reference line series
        LineSeries {
            id: backgroundRefLine
            axisX: chartView.axisX
            axisY: chartView.axisY
            useOpenGL: chartView.useOpenGL
            color: "#888888"
            width: 1
            style: Qt.DashLine
            visible: Globals.BackendWrapper.plottingBkgShown
        }

        // Scale reference line series
        LineSeries {
            id: scaleRefLine
            axisX: chartView.axisX
            axisY: chartView.axisY
            useOpenGL: chartView.useOpenGL
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
                chartView.updateReferenceLines()
            }
        }

        function updateReferenceLines() {
            Globals.BackendWrapper.updateRefLines(backgroundRefLine, scaleRefLine, true)
        }

        // Scatter series for measured data (single experiment, linear mode)
        property var measuredScatterSerie: null

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
            console.log("Analysis: isMultiExperimentMode changed to: " + isMultiExperimentMode)
            updateMultiExperimentSeries()
        }

        // Watch for changes in multi-experiment selection
        Connections {
            target: Globals.BackendWrapper.activeBackend ?? null
            enabled: target !== null
            function onMultiExperimentSelectionChanged() {
                console.log("Analysis: Multi-experiment selection changed - updating series")
                chartView.updateMultiExperimentSeries()
            }
        }

        // Watch for plot mode changes (R(q)×q⁴ toggle)
        Connections {
            target: Globals.BackendWrapper
            function onPlotModeChanged() {
                console.debug("AnalysisView: Plot mode changed, refreshing chart")
                Globals.BackendWrapper.plottingRefreshAnalysis()
                // Delay resetAxes to allow axis range properties to update first
                analysisResetAxesTimer.start()
            }
            function onChartAxesResetRequested() {
                // Reset axes when model is loaded (e.g., from ORSO file)
                analysisResetAxesTimer.start()
            }
            function onSamplePageResetAxes() {
                analysisResetAxesTimer.start()
            }
        }

        Timer {
            id: analysisResetAxesTimer
            interval: 75
            repeat: false
            onTriggered: chartView.resetAxes()
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
            id: axisXLog
            visible: chartView.useLogQAxis
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
            return useLogQAxis ? axisXLog : chartView.axisX
        }

        onUseLogQAxisChanged: {
            recreateForLogMode()
        }

        function recreateForLogMode() {
            // Clean up previous log mode series
            if (logModeSeries) {
                chartView.removeSeries(logModeSeries.measuredSerie)
                chartView.removeSeries(logModeSeries.calculatedSerie)
                logModeSeries = null
            }

            if (isMultiExperimentMode) {
                // Multi-experiment mode: recreate all with the correct axis
                updateMultiExperimentSeries()
            } else if (useLogQAxis) {
                // Single experiment, log mode: create dynamic series on log axis
                measured.visible = false
                if (measuredScatterSerie) measuredScatterSerie.visible = false
                calculated.visible = false

                var newMeasured = MeasuredScatter.create(chartView, ChartView, ScatterSeries,
                                                         "measured_log", axisXLog, chartView.axisY,
                                                         measured.color)

                var newCalculated = chartView.createSeries(ChartView.SeriesTypeLine, "calculated_log", axisXLog, chartView.axisY)
                newCalculated.color = calculated.color
                newCalculated.width = calculated.width
                newCalculated.useOpenGL = chartView.useOpenGL

                logModeSeries = {
                    measuredSerie: newMeasured,
                    calculatedSerie: newCalculated
                }

                // Register new series with backend and refresh
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'measuredSerie', newMeasured)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'calculatedSerie', newCalculated)
                Globals.BackendWrapper.plottingRefreshAnalysis()
            } else {
                // Single experiment, linear mode: restore scatter series
                measured.visible = false
                if (!measuredScatterSerie) {
                    console.warn("AnalysisView.recreateForLogMode: measuredScatterSerie is null - linear mode will render no measured points")
                } else {
                    measuredScatterSerie.visible = true
                }
                calculated.visible = true

                Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'measuredSerie', measuredScatterSerie)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'calculatedSerie', calculated)
                Globals.BackendWrapper.plottingRefreshAnalysis()
            }

            updateReferenceLines()
            Qt.callLater(resetAxes)
        }

        function resetAxes() {
            if (useLogQAxis) {
                if (axisXLog) {
                    axisXLog.min = axisXLog.minAfterReset
                    axisXLog.max = axisXLog.maxAfterReset
                }
            } else {
                if (chartView.axisX) {
                    chartView.axisX.min = chartView.axisX.minAfterReset
                    chartView.axisX.max = chartView.axisX.maxAfterReset
                }
            }
            if (chartView.axisY) {
                chartView.axisY.min = chartView.axisY.minAfterReset
                chartView.axisY.max = chartView.axisY.maxAfterReset
            }
        }

        property double yRange: Globals.BackendWrapper.plottingAnalysisMaxY - Globals.BackendWrapper.plottingAnalysisMinY
        axisY.title: "Log10 " + Globals.BackendWrapper.plottingYAxisTitle
        axisY.min: Globals.BackendWrapper.plottingAnalysisMinY - yRange * 0.01
        axisY.max: Globals.BackendWrapper.plottingAnalysisMaxY + yRange * 0.01
        axisY.minAfterReset: Globals.BackendWrapper.plottingAnalysisMinY - yRange * 0.01
        axisY.maxAfterReset: Globals.BackendWrapper.plottingAnalysisMaxY + yRange * 0.01

        calcSerie.onHovered: (point, state) => showMainTooltip(chartView, point, state)
        calcSerie.color: {
            const colors = Globals.BackendWrapper.modelColorsForExperiment
            const idx = Globals.BackendWrapper.analysisExperimentsCurrentIndex

            if (colors && idx >= 0 && idx < colors.length) {
                return colors[idx]
            }

            return undefined
        }

        // Multi-experiment series management
        function updateMultiExperimentSeries() {
            console.log("Analysis: updateMultiExperimentSeries called, isMultiExperimentMode=" + isMultiExperimentMode)

            // Clear existing multi-experiment series
            clearMultiExperimentSeries()

            if (!isMultiExperimentMode) {
                // Show default series for single experiment
                console.log("Analysis: Single experiment mode - showing default series")
                measured.visible = false
                if (!measuredScatterSerie) {
                    console.warn("AnalysisView.updateMultiExperimentSeries: measuredScatterSerie is null - single mode will render no measured points")
                } else {
                    measuredScatterSerie.visible = true
                    MeasuredScatter.setColor(measuredScatterSerie, currentExperimentColor)
                }
                calculated.visible = true

                // Re-register scatter series and refresh data
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'measuredSerie', measuredScatterSerie)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'calculatedSerie', calculated)
                Globals.BackendWrapper.plottingRefreshAnalysis()
                return
            }

            // Get experiment data list
            var experimentDataList = Globals.BackendWrapper.plottingIndividualExperimentDataList
            console.log("Analysis: experimentDataList length=" + experimentDataList.length)

            // If no data available yet, keep default series visible as fallback
            if (experimentDataList.length === 0) {
                console.log("Analysis: No experiment data available - keeping default series visible")
                measured.visible = false
                if (!measuredScatterSerie) {
                    console.warn("AnalysisView.updateMultiExperimentSeries: measuredScatterSerie is null - no-data fallback will render no measured points")
                } else {
                    measuredScatterSerie.visible = true
                }
                calculated.visible = true

                // Re-register the scatter series and refresh so the chart
                // matches what the single-experiment branch above does.
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'measuredSerie', measuredScatterSerie)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'calculatedSerie', calculated)
                Globals.BackendWrapper.plottingRefreshAnalysis()
                return
            }

            // Hide default series in multi-experiment mode (only after we have data)
            measured.visible = false
            if (measuredScatterSerie) measuredScatterSerie.visible = false
            calculated.visible = false
            console.log("Analysis: Hidden default series, creating " + experimentDataList.length + " experiment series")

            // Create series for each experiment
            for (var i = 0; i < experimentDataList.length; i++) {
                var expData = experimentDataList[i]
                console.log("Analysis: Creating series for experiment " + expData.index + " (" + expData.name + ") with color " + expData.color)
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
                    chartView.removeSeries(seriesSet.measuredSerie)
                }
                if (seriesSet.calculatedSerie) {
                    chartView.removeSeries(seriesSet.calculatedSerie)
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

            // Create measured data series (scatter points)
            var measuredSerie = MeasuredScatter.create(chartView, ChartView, ScatterSeries,
                                                       `${expName} - Measured`,
                                                       xAxis, chartView.axisY,
                                                       color)

            // Create calculated data series using the model's own color
            var calculatedSerie = chartView.createSeries(ChartView.SeriesTypeLine,
                                                        `${expName} - Calculated`,
                                                        xAxis, chartView.axisY)
            calculatedSerie.color = modelColor
            calculatedSerie.width = 2
            calculatedSerie.capStyle = Qt.RoundCap
            calculatedSerie.useOpenGL = chartView.useOpenGL

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
            console.log("Analysis: populateExperimentSeries for exp " + seriesSet.expIndex + " got " + dataPoints.length + " points")

            // Clear existing points
            seriesSet.measuredSerie.clear()
            seriesSet.calculatedSerie.clear()

            // Add data points
            for (var i = 0; i < dataPoints.length; i++) {
                var point = dataPoints[i]
                seriesSet.measuredSerie.append(point.x, point.measured)
                seriesSet.calculatedSerie.append(point.x, point.calculated)
            }

            console.log("Analysis: Added " + dataPoints.length + " points to series for " + seriesSet.expName)
        }

        // Tool buttons
        Row {
            id: toolButtons

            x: chartView.plotArea.x + chartView.plotArea.width - width
            y: chartView.plotArea.y - height - EaStyle.Sizes.fontPixelSize

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
                checked: chartView.allowHover
                autoExclusive: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "comment-alt"
                ToolTip.text: qsTr("Show coordinates tooltip on hover")
                onClicked: chartView.allowHover = !chartView.allowHover
            }

            Item { height: 1; width: 0.5 * EaStyle.Sizes.fontPixelSize }  // spacer

            EaElements.TabButton {
                checked: !chartView.allowZoom
                autoExclusive: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "arrows-alt"
                ToolTip.text: qsTr("Enable pan")
                onClicked: chartView.allowZoom = !chartView.allowZoom
            }

            EaElements.TabButton {
                checked: chartView.allowZoom
                autoExclusive: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "expand"
                ToolTip.text: qsTr("Enable box zoom")
                onClicked: chartView.allowZoom = !chartView.allowZoom
            }

            EaElements.TabButton {
                checkable: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "undo"
                ToolTip.text: qsTr("Reset axes")
                onClicked: chartView.resetAxes()
            }

        }
        // Tool buttons

        // Legend
        Rectangle {
            visible: Globals.Variables.showLegendOnAnalysisPage

            x: chartView.plotArea.x + chartView.plotArea.width - width - EaStyle.Sizes.fontPixelSize
            y: chartView.plotArea.y + EaStyle.Sizes.fontPixelSize
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
                    visible: !chartView.isMultiExperimentMode
                    text: Globals.Variables.lineStyleSymbol(chartView.measSerie.style) + '  I (Measured)'
                    color: chartView.measSerie.color
                }
                EaElements.Label {
                    visible: !chartView.isMultiExperimentMode
                    text: Globals.Variables.lineStyleSymbol(chartView.calcSerie.style) + ' (Calculated)'
                    color: chartView.calcSerie.color
                }

                // Multi-experiment legend
                Column {
                    visible: chartView.isMultiExperimentMode
                    spacing: EaStyle.Sizes.fontPixelSize * 0.2

                    EaElements.Label {
                        text: qsTr("Multi-experiment view:")
                        font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                        font.bold: true
                        color: EaStyle.Colors.themeForeground
                    }

                    Repeater {
                        model: chartView.isMultiExperimentMode ? Globals.BackendWrapper.plottingIndividualExperimentDataList : []
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
                        text: Globals.Variables.lineStyleSymbol(chartView.measSerie.style) + ' ' + qsTr("Measured")
                        font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.7
                        color: EaStyle.Colors.themeForegroundMinor
                    }
                    EaElements.Label {
                        text: Globals.Variables.lineStyleSymbol(chartView.calcSerie.style) + ' ' + qsTr("Calculated")
                        font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.7
                        color: EaStyle.Colors.themeForegroundMinor
                    }
                }
            }
        }
        // Legend

        EaElements.ToolTip {
            id: dataToolTip

            arrowLength: 0
            textFormat: Text.RichText
        }

        // Data is set in python backend (plotting_1d.py)
        Component.onCompleted: {
            // Create scatter series for measured data (single experiment, linear mode)
            measuredScatterSerie = MeasuredScatter.create(chartView, ChartView, ScatterSeries,
                                                          "measured_scatter",
                                                          chartView.axisX, chartView.axisY,
                                                          measured.color)
            if (!measuredScatterSerie) {
                console.warn("AnalysisView: failed to create measuredScatterSerie - measured data will not render")
            }
            measured.visible = false

            Globals.References.pages.analysis.mainContent.analysisView = chartView

            Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage',
                                                               'measuredSerie',
                                                               measuredScatterSerie)
            Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage',
                                                               'calculatedSerie',
                                                               calculated)
            Globals.BackendWrapper.plottingRefreshAnalysis()

            // Initialize multi-experiment support
            updateMultiExperimentSeries()
            
            // Initialize reference lines
            updateReferenceLines()
        }

        // Update series when chart becomes visible
        onVisibleChanged: {
            if (visible) {
                if (isMultiExperimentMode) {
                    updateMultiExperimentSeries()
                } else {
                    // Ensure scatter series has correct color and data after tab switch
                    if (!measuredScatterSerie) {
                        console.warn("AnalysisView.onVisibleChanged: measuredScatterSerie is null - tab switch will render no measured points")
                    } else {
                        MeasuredScatter.setColor(measuredScatterSerie, currentExperimentColor)
                        measuredScatterSerie.visible = true
                    }
                    measured.visible = false
                    Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'measuredSerie', measuredScatterSerie)
                    Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage', 'calculatedSerie', calculated)
                    Globals.BackendWrapper.plottingRefreshAnalysis()
                }
                updateReferenceLines()
            }
        }
    }

    // Logic

    function showMainTooltip(chart, point, state) {
        if (!chartView.allowHover) {
            return
        }
        const pos = chart.mapToPosition(Qt.point(point.x, point.y))
        dataToolTip.x = pos.x
        dataToolTip.y = pos.y
        dataToolTip.text = `<p align="left">x: ${point.x.toFixed(3)}<br\>y: ${point.y.toFixed(3)}</p>`
        dataToolTip.parent = chart
        dataToolTip.visible = state
    }
}
