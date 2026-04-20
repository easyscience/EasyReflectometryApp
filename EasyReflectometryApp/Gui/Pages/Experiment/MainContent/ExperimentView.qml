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

        property alias measured: chartView.calcSerie
        property alias errorUpper: chartView.measSerie
        property alias errorLower: chartView.bkgSerie

        property color currentExperimentColor: Globals.Variables.experimentColor(
            Globals.BackendWrapper.analysisExperimentsCurrentIndex
        )

        calcSerie.color: currentExperimentColor
        bkgSerie.color: measSerie.color
        measSerie.width: 1
        bkgSerie.width: 1

        // Keep scatter series color in sync with selected experiment
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

        // Recreate series when marker style changes
        Connections {
            target: Globals.Variables
            function onExperimentMarkerStyleChanged() {
                chartView.recreateSeriesForCurrentMode()
            }
        }

        function recreateSeriesForCurrentMode() {
            if (isMultiExperimentMode) {
                // Multi-experiment mode: recreate all multi-experiment series
                updateMultiExperimentSeries()
            } else if (useLogQAxis) {
                // Single experiment, log mode: recreate log mode series
                recreateForLogMode()
            } else {
                // Single experiment, linear mode: recreate scatter series
                if (measuredScatterSerie) {
                    chartView.removeSeries(measuredScatterSerie)
                    measuredScatterSerie = null
                }
                measuredScatterSerie = MeasuredScatter.create(chartView, ChartView, ScatterSeries,
                                                              "measured_scatter",
                                                              chartView.axisX, chartView.axisY,
                                                              currentExperimentColor, Globals.Variables.experimentMarkerStyle)
                if (measuredScatterSerie) {
                    measuredScatterSerie.visible = true
                    Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'measuredSerie', measuredScatterSerie)
                    Globals.BackendWrapper.plottingRefreshExperiment()
                }
            }
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
        property bool useStaggeredPlotting: {
            try {
                return Globals.Variables.useStaggeredPlotting || false
            } catch (e) {
                return false
            }
        }
        property double staggeringFactor: {
            try {
                return Globals.Variables.staggeringFactor !== undefined ? Globals.Variables.staggeringFactor : 0.5
            } catch (e) {
                return 0.5
            }
        }

        // Watch for changes in multi-experiment mode
        // onIsMultiExperimentModeChanged: {
        //     // Don't update here - wait for experimentDataChanged signal
        //     // which fires after backend has prepared the data
        //     console.log(`Multi-experiment mode changed to: ${isMultiExperimentMode}`)
        // }

        // Watch for changes in staggered plotting mode
        onUseStaggeredPlottingChanged: {
            // console.log(`ExperimentView detected staggered mode change: ${useStaggeredPlotting}`)
            // console.log(`Multi-experiment mode: ${isMultiExperimentMode}, Series count: ${multiExperimentSeries.length}`)
            if (isMultiExperimentMode && multiExperimentSeries.length > 1) {
                // console.log(`Refreshing ${multiExperimentSeries.length} series with staggered mode: ${useStaggeredPlotting}`)
                // Re-populate all series with new staggering setting
                for (var i = 0; i < multiExperimentSeries.length; i++) {
                    populateExperimentSeries(multiExperimentSeries[i])
                }
                // Adjust Y-axis to fit all staggered experiments
                adjustAxisForStaggering()
            } else {
                console.log(`   Skipping refresh - not in multi-experiment mode or insufficient series`)
            }
        }

        // Watch for changes in staggering factor
        onStaggeringFactorChanged: {
            // console.log(`ExperimentView detected staggering factor change: ${staggeringFactor.toFixed(2)}`)
            if (useStaggeredPlotting && isMultiExperimentMode && multiExperimentSeries.length > 1) {
                // console.log(`Refreshing ${multiExperimentSeries.length} series with new factor`)
                // Re-populate all series with new staggering factor
                for (var i = 0; i < multiExperimentSeries.length; i++) {
                    populateExperimentSeries(multiExperimentSeries[i])
                }
                // Adjust Y-axis to fit all staggered experiments
                adjustAxisForStaggering()
            }
        }

        // Additional watcher directly on Globals.Variables.staggeringFactor
        Connections {
            target: Globals.Variables
            function onStaggeringFactorChanged() {
                // console.log(`Direct watcher: Globals.Variables.staggeringFactor changed to ${Globals.Variables.staggeringFactor}`)
                if (chartView.useStaggeredPlotting && chartView.isMultiExperimentMode && chartView.multiExperimentSeries.length > 1) {
                    // console.log(`Forcing refresh of ${chartView.multiExperimentSeries.length} series`)
                    for (var i = 0; i < chartView.multiExperimentSeries.length; i++) {
                        chartView.populateExperimentSeries(chartView.multiExperimentSeries[i])
                    }
                    chartView.adjustAxisForStaggering()
                }
            }
        }

        function adjustAxisForStaggering() {
            if (!useStaggeredPlotting || !isMultiExperimentMode || multiExperimentSeries.length <= 1) {
                return
            }

            var allMinY = 1e10
            var allMaxY = -1e10

            // Find the bounds of all staggered series
            for (var exp = 0; exp < multiExperimentSeries.length; exp++) {
                var series = multiExperimentSeries[exp].measuredSerie
                for (var i = 0; i < series.count; i++) {
                    var point = series.at(i)
                    allMinY = Math.min(allMinY, point.y)
                    allMaxY = Math.max(allMaxY, point.y)
                }
            }

            // Add 10% padding and apply to Y-axis
            var padding = (allMaxY - allMinY) * 0.1
            chartView.axisY.min = allMinY - padding
            chartView.axisY.max = allMaxY + padding

            // console.log(`📏 Adjusted Y-axis for staggering: [${allMinY.toExponential(2)}, ${allMaxY.toExponential(2)}] with padding`)
        }

        // Watch for changes in multi-experiment selection
        Connections {
            target: Globals.BackendWrapper.activeBackend ?? null
            enabled: target !== null
            function onMultiExperimentSelectionChanged() {
                // Update series when selection changes
                // The function will handle showing/hiding appropriate series
                console.log("Multi-experiment selection changed - updating series")
                chartView.updateMultiExperimentSeries()
            }
        }

        // Watch for plot mode changes (R(q)×q⁴ toggle)
        Connections {
            target: Globals.BackendWrapper
            function onPlotModeChanged() {
                console.debug("ExperimentView: Plot mode changed, refreshing chart")
                Globals.BackendWrapper.plottingRefreshExperiment()
                // Delay resetAxes to allow axis range properties to update first
                experimentResetAxesTimer.start()
            }
            function onChartAxesResetRequested() {
                // Reset axes when model is loaded (e.g., from ORSO file)
                experimentResetAxesTimer.start()
            }
        }

        Timer {
            id: experimentResetAxesTimer
            interval: 75
            repeat: false
            onTriggered: chartView.resetAxes()
        }
        
        property double xRange: Globals.BackendWrapper.plottingExperimentMaxX - Globals.BackendWrapper.plottingExperimentMinX
        axisX.title: "q (Å⁻¹)"
        axisX.min: Globals.BackendWrapper.plottingExperimentMinX - xRange * 0.01
        axisX.max: Globals.BackendWrapper.plottingExperimentMaxX + xRange * 0.01
        axisX.minAfterReset: Globals.BackendWrapper.plottingExperimentMinX - xRange * 0.01
        axisX.maxAfterReset: Globals.BackendWrapper.plottingExperimentMaxX + xRange * 0.01

        // Logarithmic axis control
        property bool useLogQAxis: Globals.Variables.logarithmicQAxis
        axisX.visible: !useLogQAxis

        LogValueAxis {
            id: axisXLog
            visible: chartView.useLogQAxis
            titleText: "q (Å⁻¹)"
            property double minAfterReset: Math.max(Globals.BackendWrapper.plottingExperimentMinX, 1e-6)
            property double maxAfterReset: Globals.BackendWrapper.plottingExperimentMaxX * 1.1
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
                chartView.removeSeries(logModeSeries.errorUpperSerie)
                chartView.removeSeries(logModeSeries.errorLowerSerie)
                logModeSeries = null
            }

            if (isMultiExperimentMode) {
                // Multi-experiment mode: recreate all multi-experiment series with the correct axis
                updateMultiExperimentSeries()
            } else if (useLogQAxis) {
                // Single experiment, log mode: create dynamic series on log axis
                measured.visible = false
                if (measuredScatterSerie) measuredScatterSerie.visible = false
                errorUpper.visible = false
                errorLower.visible = false

                var newMeasured = MeasuredScatter.create(chartView, ChartView, ScatterSeries,
                                                         "measured_log", axisXLog, chartView.axisY,
                                                         chartView.currentExperimentColor, Globals.Variables.experimentMarkerStyle)

                var newErrorUpper = chartView.createSeries(ChartView.SeriesTypeLine, "errorUpper_log", axisXLog, chartView.axisY)
                newErrorUpper.color = errorUpper.color
                newErrorUpper.width = errorUpper.width
                newErrorUpper.useOpenGL = chartView.useOpenGL

                var newErrorLower = chartView.createSeries(ChartView.SeriesTypeLine, "errorLower_log", axisXLog, chartView.axisY)
                newErrorLower.color = errorLower.color
                newErrorLower.width = errorLower.width
                newErrorLower.useOpenGL = chartView.useOpenGL

                logModeSeries = {
                    measuredSerie: newMeasured,
                    errorUpperSerie: newErrorUpper,
                    errorLowerSerie: newErrorLower
                }

                // Register new series with backend and refresh
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'measuredSerie', newMeasured)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'errorUpperSerie', newErrorUpper)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'errorLowerSerie', newErrorLower)
                Globals.BackendWrapper.plottingRefreshExperiment()
            } else {
                // Single experiment, linear mode: restore scatter series
                measured.visible = false
                if (!measuredScatterSerie) {
                    console.warn("ExperimentView.recreateForLogMode: measuredScatterSerie is null - linear mode will render no measured points")
                } else {
                    measuredScatterSerie.visible = true
                }
                errorUpper.visible = true
                errorLower.visible = true

                // Re-register scatter series for measured, static series for errors
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'measuredSerie', measuredScatterSerie)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'errorUpperSerie', errorUpper)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'errorLowerSerie', errorLower)
                Globals.BackendWrapper.plottingRefreshExperiment()
            }

            // Update reference lines on correct axis
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

        property double yRange: Globals.BackendWrapper.plottingExperimentMaxY - Globals.BackendWrapper.plottingExperimentMinY
        axisY.title: "Log10 " + Globals.BackendWrapper.plottingYAxisTitle
        axisY.min: Globals.BackendWrapper.plottingExperimentMinY - yRange * 0.01
        axisY.max: Globals.BackendWrapper.plottingExperimentMaxY + yRange * 0.01
        axisY.minAfterReset: Globals.BackendWrapper.plottingExperimentMinY - yRange * 0.01
        axisY.maxAfterReset: Globals.BackendWrapper.plottingExperimentMaxY + yRange * 0.01

        calcSerie.onHovered: (point, state) => showMainTooltip(chartView, point, state)

        // Multi-experiment series management
        function updateMultiExperimentSeries() {
            // console.log("Updating multi-experiment series...")
            // console.log(`   isMultiExperimentMode: ${isMultiExperimentMode}`)

            // Clear existing multi-experiment series
            clearMultiExperimentSeries()

            if (!isMultiExperimentMode) {
                // Show default series for single experiment
                measured.visible = false
                if (!measuredScatterSerie) {
                    console.warn("ExperimentView.updateMultiExperimentSeries: measuredScatterSerie is null - single mode will render no measured points")
                } else {
                    measuredScatterSerie.visible = true
                    MeasuredScatter.setColor(measuredScatterSerie, currentExperimentColor)
                }
                errorUpper.visible = true
                errorLower.visible = true

                // Re-register scatter series and refresh data
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'measuredSerie', measuredScatterSerie)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'errorUpperSerie', errorUpper)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'errorLowerSerie', errorLower)
                Globals.BackendWrapper.plottingRefreshExperiment()
                return
            }

            // Get experiment data list
            var experimentDataList = Globals.BackendWrapper.plottingIndividualExperimentDataList
            // If no data available yet, keep default series visible as fallback
            if (experimentDataList.length === 0) {
                console.log("No experiment data available - keeping default series visible")
                measured.visible = false
                if (!measuredScatterSerie) {
                    console.warn("ExperimentView.updateMultiExperimentSeries: measuredScatterSerie is null - no-data fallback will render no measured points")
                } else {
                    measuredScatterSerie.visible = true
                }
                errorUpper.visible = true
                errorLower.visible = true

                // Re-register and refresh so this branch matches the
                // single-experiment branch above.
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'measuredSerie', measuredScatterSerie)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'errorUpperSerie', errorUpper)
                Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage', 'errorLowerSerie', errorLower)
                Globals.BackendWrapper.plottingRefreshExperiment()
                return
            }

            // Hide default series in multi-experiment mode (only after we have data)
            measured.visible = false
            if (measuredScatterSerie) measuredScatterSerie.visible = false
            errorUpper.visible = false
            errorLower.visible = false

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
                    chartView.removeSeries(seriesSet.measuredSerie)
                }
                if (seriesSet.errorUpperSerie) {
                    chartView.removeSeries(seriesSet.errorUpperSerie)
                }
                if (seriesSet.errorLowerSerie) {
                    chartView.removeSeries(seriesSet.errorLowerSerie)
                }
            }
            multiExperimentSeries = []
        }

        function createExperimentSeries(expIndex, expName, color) {
            // console.log(` Creating series for experiment ${expIndex}: ${expName} (${color})`)

            var xAxis = currentXAxis()

            // Create measured data series (scatter points)
            var measuredSerie = MeasuredScatter.create(chartView, ChartView, ScatterSeries,
                                                       `${expName} - Data`,
                                                       xAxis, chartView.axisY,
                                                       color, Globals.Variables.experimentMarkerStyle)

            // Create error bound series (lighter colors)
            var errorColor = Qt.darker(color, 1.3)

            var errorUpperSerie = chartView.createSeries(ChartView.SeriesTypeLine,
                                                        `${expName} - Error Upper`,
                                                        xAxis, chartView.axisY)
            errorUpperSerie.color = errorColor
            errorUpperSerie.width = 1
            errorUpperSerie.style = Qt.DashLine
            errorUpperSerie.useOpenGL = chartView.useOpenGL

            var errorLowerSerie = chartView.createSeries(ChartView.SeriesTypeLine,
                                                        `${expName} - Error Lower`,
                                                        xAxis, chartView.axisY)
            errorLowerSerie.color = errorColor
            errorLowerSerie.width = 1
            errorLowerSerie.style = Qt.DashLine
            errorLowerSerie.useOpenGL = chartView.useOpenGL

            // Store references
            var seriesSet = {
                measuredSerie: measuredSerie,
                errorUpperSerie: errorUpperSerie,
                errorLowerSerie: errorLowerSerie,
                expIndex: expIndex,
                expName: expName,
                color: color
            }
            multiExperimentSeries.push(seriesSet)

            // Populate with data
            populateExperimentSeries(seriesSet)
        }

        function populateExperimentSeries(seriesSet) {
            // Get data points from backend
            var dataPoints = Globals.BackendWrapper.plottingGetExperimentDataPoints(seriesSet.expIndex)

            // Clear existing points
            seriesSet.measuredSerie.clear()
            seriesSet.errorUpperSerie.clear()
            seriesSet.errorLowerSerie.clear()

            // Calculate staggering offset if enabled
            var yOffset = 0
            if (useStaggeredPlotting && isMultiExperimentMode && multiExperimentSeries.length > 1) {
                var experimentIndex = seriesSet.expIndex
                var totalExperiments = multiExperimentSeries.length

                // Find the individual experiment's data range
                var expMinY = 1e10
                var expMaxY = -1e10

                for (var j = 0; j < dataPoints.length; j++) {
                    expMinY = Math.min(expMinY, dataPoints[j].y)
                    expMaxY = Math.max(expMaxY, dataPoints[j].y)
                }

                var expDataRange = expMaxY - expMinY

                // Use staggering factor to control offset
                // Factor ranges from 0 (no staggering) to 5.0 (maximum staggering)
                // Each experiment gets offset proportional to the staggering factor
                var offsetStep = expDataRange * 0.5 * staggeringFactor
                yOffset = experimentIndex * offsetStep

                // Ensure we don't exceed reasonable bounds - limit total staggering to 2x original range
                var maxTotalOffset = expDataRange * 5
                var currentTotalOffset = (totalExperiments - 1) * offsetStep

                if (currentTotalOffset > maxTotalOffset) {
                    // Rescale all offsets proportionally to fit within bounds
                    var scaleFactor = maxTotalOffset / currentTotalOffset
                    yOffset = experimentIndex * offsetStep * scaleFactor
                }

            }

            // Add data points with potential offset
            for (var i = 0; i < dataPoints.length; i++) {
                var point = dataPoints[i]
                seriesSet.measuredSerie.append(point.x, point.y + yOffset)
                seriesSet.errorUpperSerie.append(point.x, point.errorUpper + yOffset)
                seriesSet.errorLowerSerie.append(point.x, point.errorLower + yOffset)
            }
        }

        // Tool buttons
        Row {
            id: toolButtons

            x: chartView.plotArea.x + chartView.plotArea.width - width
            y: chartView.plotArea.y - height - EaStyle.Sizes.fontPixelSize

            spacing: 0.25 * EaStyle.Sizes.fontPixelSize

            EaElements.TabButton {
                checked: Globals.Variables.showLegendOnExperimentPage
                autoExclusive: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "align-left"
                ToolTip.text: Globals.Variables.showLegendOnExperimentPage ?
                                  qsTr("Hide legend") :
                                  qsTr("Show legend")
                onClicked: Globals.Variables.showLegendOnExperimentPage = checked
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
            visible: Globals.Variables.showLegendOnExperimentPage

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

                // Single experiment legend
                EaElements.Label {
                    visible: !chartView.isMultiExperimentMode
                    text: Globals.Variables.lineStyleSymbol(chartView.calcSerie.style) + '  I (Measured)'
                    color: chartView.calcSerie.color
                }
                EaElements.Label {
                    visible: !chartView.isMultiExperimentMode
                    text: Globals.Variables.lineStyleSymbol(chartView.measSerie.style) + ' Error'
                    color: chartView.measSerie.color
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
                        text: qsTr("- - - Error bounds")
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
                                                          currentExperimentColor, Globals.Variables.experimentMarkerStyle)
            if (!measuredScatterSerie) {
                console.warn("ExperimentView: failed to create measuredScatterSerie - measured data will not render")
            }
            measured.visible = false

            Globals.References.pages.experiment.mainContent.experimentView = chartView

            Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage',
                                                               'errorUpperSerie',
                                                               errorUpper)
            Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage',
                                                               'errorLowerSerie',
                                                               errorLower)
            Globals.BackendWrapper.plottingSetQtChartsSerieRef('experimentPage',
                                                               'measuredSerie',
                                                               measuredScatterSerie)

            // Initialize multi-experiment support
            // console.log("ExperimentView initialized - checking multi-experiment mode...")
            updateMultiExperimentSeries()

            // Initialize reference lines
            updateReferenceLines()
        }

        // Update series when chart becomes visible
        onVisibleChanged: {
            if (visible && isMultiExperimentMode) {
                updateMultiExperimentSeries()
            }
            if (visible) {
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
