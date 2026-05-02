// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtCharts

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements

import Gui.Components as GuiComponents
import Gui.Globals as Globals


Rectangle {
    id: root

    color: EaStyle.Colors.chartBackground

    property bool showLegend: false

    // Expose for external reset / zoom sync calls from CombinedView / SldView wrapper
    readonly property alias chartView: chartView

    // Dynamically created per-experiment series in multi-experiment mode
    property var residualSeries: []

    ChartView {
        id: chartView

        anchors.fill: parent
        anchors.topMargin: EaStyle.Sizes.toolButtonHeight - EaStyle.Sizes.fontPixelSize - 1
        anchors.margins: -12

        antialiasing: true
        legend.visible: false
        backgroundRoundness: 0
        backgroundColor: EaStyle.Colors.chartBackground
        plotAreaColor: EaStyle.Colors.chartPlotAreaBackground

        property bool allowZoom: true
        property bool allowHover: true

        property double xRange: Globals.BackendWrapper.plottingResidualMaxX - Globals.BackendWrapper.plottingResidualMinX

        // Logarithmic axis control
        property bool useLogQAxis: Globals.Variables.logarithmicQAxis

        ValueAxis {
            id: axisX
            visible: !chartView.useLogQAxis
            titleText: "q (Å⁻¹)"
            property double minAfterReset: Globals.BackendWrapper.plottingResidualMinX - chartView.xRange * 0.01
            property double maxAfterReset: Globals.BackendWrapper.plottingResidualMaxX + chartView.xRange * 0.01
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

        LogValueAxis {
            id: axisXLog
            visible: chartView.useLogQAxis
            titleText: "q (Å⁻¹)"
            property double minAfterReset: Math.max(Globals.BackendWrapper.plottingResidualMinX, 1e-6)
            property double maxAfterReset: Globals.BackendWrapper.plottingResidualMaxX * 1.1
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

        onUseLogQAxisChanged: {
            refreshResidualChart()
            Qt.callLater(resetAxes)
        }

        function currentXAxis() {
            return useLogQAxis ? axisXLog : axisX
        }

        property double yRange: Globals.BackendWrapper.plottingResidualMaxY - Globals.BackendWrapper.plottingResidualMinY

        ValueAxis {
            id: axisY
            // titleText: "(Model − Experiment) / σ"
            titleText: "(M-E)/σ"
            property double minAfterReset: {
                const maxAbs = Math.max(Math.abs(Globals.BackendWrapper.plottingResidualMinY), Math.abs(Globals.BackendWrapper.plottingResidualMaxY))
                return -maxAbs - maxAbs * 0.05
            }
            property double maxAfterReset: {
                const maxAbs = Math.max(Math.abs(Globals.BackendWrapper.plottingResidualMinY), Math.abs(Globals.BackendWrapper.plottingResidualMaxY))
                return maxAbs + maxAbs * 0.05
            }
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

        function resetAxes() {
            if (useLogQAxis) {
                if (axisXLog) {
                    axisXLog.min = axisXLog.minAfterReset
                    axisXLog.max = axisXLog.maxAfterReset
                }
            } else {
                if (axisX) {
                    axisX.min = axisX.minAfterReset
                    axisX.max = axisX.maxAfterReset
                }
            }
            if (axisY) {
                axisY.min = axisY.minAfterReset
                axisY.max = axisY.maxAfterReset
            }
        }

        // Zero reference line — always visible, not affected by scale/bkg toggles
        LineSeries {
            id: zeroLine
            axisX: axisX
            axisY: axisY
            useOpenGL: EaGlobals.Vars.useOpenGL
            color: EaStyle.Colors.chartGridLine
            width: 1
            style: Qt.DotLine

            Component.onCompleted: {
                // Span the full residual X domain
                zeroLine.append(Globals.BackendWrapper.plottingResidualMinX, 0)
                zeroLine.append(Globals.BackendWrapper.plottingResidualMaxX, 0)
            }
        }

        // Single-experiment residual series (hidden in multi-experiment mode)
        LineSeries {
            id: singleResidualSerie
            axisX: axisX
            axisY: axisY
            useOpenGL: EaGlobals.Vars.useOpenGL
            width: 1
            color: Globals.Variables.experimentColor(
                Globals.BackendWrapper.analysisExperimentsCurrentIndex
            )
            visible: !isMultiExperimentMode
            onHovered: (point, state) => showMainTooltip(chartView, dataToolTip, point, state)
        }

        GuiComponents.ChartToolbar {
            chartView: chartView
            showLegend: root.showLegend
            onShowLegendChanged: root.showLegend = showLegend
        }

        // Legend
        Rectangle {
            visible: root.showLegend

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

                // Single experiment
                EaElements.Label {
                    visible: !isPolarizationMode && !isMultiExperimentMode
                    text: '━  ' + qsTr('Residual')
                    color: singleResidualSerie.color
                }

                Repeater {
                    model: isPolarizationMode ? visiblePolarizationChannels() : []
                    delegate: Row {
                        spacing: EaStyle.Sizes.fontPixelSize * 0.3

                        Rectangle {
                            width: EaStyle.Sizes.fontPixelSize * 0.8
                            height: 3
                            color: modelData.color || '#1f77b4'
                            anchors.verticalCenter: parent.verticalCenter
                        }

                        EaElements.Label {
                            text: `${modelData.label || modelData.key} ${qsTr('residual')}`
                            font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.8
                            color: EaStyle.Colors.themeForeground
                            anchors.verticalCenter: parent.verticalCenter
                        }
                    }
                }

                // Multi-experiment
                Repeater {
                    model: !isPolarizationMode && isMultiExperimentMode ? Globals.BackendWrapper.plottingIndividualExperimentDataList : []
                    delegate: Row {
                        spacing: EaStyle.Sizes.fontPixelSize * 0.3

                        Rectangle {
                            width: EaStyle.Sizes.fontPixelSize * 0.8
                            height: 3
                            color: modelData.color || '#1f77b4'
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
            }
        }

        EaElements.ToolTip {
            id: dataToolTip
            arrowLength: 0
            textFormat: Text.RichText
        }

        GuiComponents.ChartMouseControls {
            chartView: chartView
        }
    }

    // Multi-experiment mode flag
    property bool isMultiExperimentMode: {
        try { return Globals.BackendWrapper.plottingIsMultiExperimentMode || false }
        catch (e) { return false }
    }
    property bool isPolarizationMode: Globals.BackendWrapper.polarizationAvailable

    // Re-populate charts when backend signals a data/range refresh
    Connections {
        target: Globals.BackendWrapper.activeBackend?.plotting ?? null
        enabled: target !== null
        function onSampleChartRangesChanged() {
            refreshResidualChart()
        }
    }

    Connections {
        target: Globals.BackendWrapper
        function onPolarizationDisplayChanged() { refreshResidualChart() }
        function onPolarizationDataChanged() { refreshResidualChart() }
    }

    Component.onCompleted: {
        Qt.callLater(refreshResidualChart)
    }

    // Dynamic series for log mode (single experiment)
    property var logResidualSerie: null

    function refreshResidualChart() {
        // Update zero-line span to match new range
        zeroLine.clear()
        zeroLine.append(Globals.BackendWrapper.plottingResidualMinX, 0)
        zeroLine.append(Globals.BackendWrapper.plottingResidualMaxX, 0)

        if (isPolarizationMode) {
            _refreshPolarizationResiduals()
        } else if (isMultiExperimentMode) {
            _refreshMultiExperiment()
        } else {
            _refreshSingleExperiment()
        }
    }

    function _refreshPolarizationResiduals() {
        singleResidualSerie.clear()
        singleResidualSerie.visible = false
        _clearMultiExperimentSeries()

        if (logResidualSerie) {
            chartView.removeSeries(logResidualSerie)
            logResidualSerie = null
        }

        var xAxisToUse = chartView.currentXAxis()
        var experiments = []
        if (isMultiExperimentMode) {
            experiments = Globals.BackendWrapper.plottingIndividualExperimentDataList
        } else {
            const expIndex = Globals.BackendWrapper.analysisExperimentsCurrentIndex
            experiments = [{
                index: expIndex,
                name: `Exp ${expIndex + 1}`,
                hasData: true
            }]
        }

        for (let expPos = 0; expPos < experiments.length; expPos++) {
            const expData = experiments[expPos]
            if (!expData.hasData) continue

            const channels = visibleChannelsForExperiment(expData.index)
            for (let channelIndex = 0; channelIndex < channels.length; channelIndex++) {
                const channel = channels[channelIndex]
                const labelPrefix = expData.name || `Exp ${expData.index + 1}`
                const serie = chartView.createSeries(ChartView.SeriesTypeLine,
                                                      `${labelPrefix} - ${channel.label || channel.key}`,
                                                      xAxisToUse, axisY)
                serie.color = channel.color || '#1f77b4'
                serie.width = 1
                serie.style = isMultiExperimentMode ? experimentLineStyle(expData.index) : Qt.SolidLine
                serie.useOpenGL = EaGlobals.Vars.useOpenGL
                serie.hovered.connect((point, state) => showMainTooltip(chartView, dataToolTip, point, state))

                const points = Globals.BackendWrapper.plottingGetPolarizationResidualDataPoints(expData.index, channel.key)
                for (let pointIndex = 0; pointIndex < points.length; pointIndex++) {
                    serie.append(points[pointIndex].x, points[pointIndex].y)
                }

                residualSeries.push(serie)
            }
        }
    }

    function _refreshSingleExperiment() {
        // Remove any lingering multi-experiment series
        _clearMultiExperimentSeries()

        // Clean up previous log mode series
        if (logResidualSerie) {
            chartView.removeSeries(logResidualSerie)
            logResidualSerie = null
        }

        const expIdx = Globals.BackendWrapper.analysisExperimentsCurrentIndex
        const points = Globals.BackendWrapper.plottingGetResidualDataPoints(expIdx)

        if (chartView.useLogQAxis) {
            // Log mode: use dynamic series on log axis
            singleResidualSerie.visible = false

            logResidualSerie = chartView.createSeries(ChartView.SeriesTypeLine, "residual_log", axisXLog, axisY)
            logResidualSerie.color = singleResidualSerie.color
            logResidualSerie.width = singleResidualSerie.width
            logResidualSerie.useOpenGL = EaGlobals.Vars.useOpenGL

            for (let i = 0; i < points.length; i++) {
                logResidualSerie.append(points[i].x, points[i].y)
            }
        } else {
            // Linear mode: use static series
            singleResidualSerie.visible = !isMultiExperimentMode
            singleResidualSerie.clear()
            for (let i = 0; i < points.length; i++) {
                singleResidualSerie.append(points[i].x, points[i].y)
            }
        }
    }

    function _refreshMultiExperiment() {
        singleResidualSerie.clear()
        singleResidualSerie.visible = false
        _clearMultiExperimentSeries()

        // Clean up log mode single series
        if (logResidualSerie) {
            chartView.removeSeries(logResidualSerie)
            logResidualSerie = null
        }

        var xAxisToUse = chartView.currentXAxis()
        const experimentDataList = Globals.BackendWrapper.plottingIndividualExperimentDataList
        for (let i = 0; i < experimentDataList.length; i++) {
            const expData = experimentDataList[i]
            if (!expData.hasData) continue

            const serie = chartView.createSeries(ChartView.SeriesTypeLine,
                                                  expData.name || `Exp ${i + 1}`,
                                                  xAxisToUse, axisY)
            serie.color = expData.color
            serie.width = 1
            serie.useOpenGL = EaGlobals.Vars.useOpenGL
            serie.hovered.connect((point, state) => showMainTooltip(chartView, dataToolTip, point, state))

            const points = Globals.BackendWrapper.plottingGetResidualDataPoints(expData.index)
            for (let j = 0; j < points.length; j++) {
                serie.append(points[j].x, points[j].y)
            }

            residualSeries.push(serie)
        }
    }

    function _clearMultiExperimentSeries() {
        for (let i = 0; i < residualSeries.length; i++) {
            if (residualSeries[i]) chartView.removeSeries(residualSeries[i])
        }
        residualSeries = []
    }

    function visibleChannelsForExperiment(expIndex) {
        const selectedKeys = Globals.BackendWrapper.polarizationVisibleChannelKeys || []
        const channels = Globals.BackendWrapper.polarizationGetExperimentChannels(expIndex) || []
        const visibleChannels = []
        for (let i = 0; i < channels.length; i++) {
            const channel = channels[i]
            if (!channel || channel.enabled === false) continue
            if (selectedKeys.indexOf(channel.key) === -1) continue
            visibleChannels.push(channel)
        }
        return visibleChannels
    }

    function visiblePolarizationChannels() {
        const selectedKeys = Globals.BackendWrapper.polarizationVisibleChannelKeys || []
        const channels = Globals.BackendWrapper.polarizationChannels || []
        const visibleChannels = []
        for (let i = 0; i < channels.length; i++) {
            const channel = channels[i]
            if (!channel || channel.enabled === false) continue
            if (selectedKeys.indexOf(channel.key) === -1) continue
            visibleChannels.push(channel)
        }
        return visibleChannels
    }

    function experimentLineStyle(expIndex) {
        switch (expIndex % 4) {
        case 1: return Qt.DashLine
        case 2: return Qt.DotLine
        case 3: return Qt.DashDotLine
        default: return Qt.SolidLine
        }
    }

    function showMainTooltip(chart, tooltip, point, state) {
        if (!chart.allowHover) return
        const pos = chart.mapToPosition(Qt.point(point.x, point.y))
        tooltip.x = pos.x
        tooltip.y = pos.y
        tooltip.text = `<p align="left">q: ${point.x.toFixed(4)}<br/>σ: ${point.y.toFixed(3)}</p>`
        tooltip.parent = chart
        tooltip.visible = state
    }
}
