// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtCharts

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Charts as EaCharts

import Gui as Gui
import Gui.Components as GuiComponents
import Gui.Globals as Globals


Rectangle {
    id: container

    color: EaStyle.Colors.chartBackground

    // Track model count changes to refresh charts
    property int modelCount: Globals.BackendWrapper.sampleModels.length
    property bool isPolarizationMode: Globals.BackendWrapper.polarizationAvailable

    // Store dynamically created series
    property var sampleSeries: []

    SplitView {
        anchors.fill: parent
        orientation: Qt.Vertical

        // Sample Chart (2/3 height)
        Rectangle {
            id: sampleContainer
            SplitView.fillHeight: true
            SplitView.preferredHeight: parent.height * 0.67
            SplitView.minimumHeight: 100
            color: EaStyle.Colors.chartBackground

            ChartView {
                id: sampleChartView

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

                property double xRange: Globals.BackendWrapper.plottingSampleMaxX - Globals.BackendWrapper.plottingSampleMinX

                // Logarithmic axis control
                property bool useLogQAxis: Globals.Variables.logarithmicQAxis

                ValueAxis {
                    id: sampleAxisX
                    visible: !sampleChartView.useLogQAxis
                    titleText: "q (Å⁻¹)"
                    // min/max set imperatively to avoid binding reset during zoom
                    property double minAfterReset: Globals.BackendWrapper.plottingSampleMinX - sampleChartView.xRange * 0.01
                    property double maxAfterReset: Globals.BackendWrapper.plottingSampleMaxX + sampleChartView.xRange * 0.01
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
                    id: sampleAxisXLog
                    visible: sampleChartView.useLogQAxis
                    titleText: "q (Å⁻¹)"
                    // min/max set for log scale - ensure positive values
                    property double minAfterReset: Math.max(Globals.BackendWrapper.plottingSampleMinX, 1e-6)
                    property double maxAfterReset: Globals.BackendWrapper.plottingSampleMaxX * 1.1
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

                property double yRange: Globals.BackendWrapper.plottingSampleMaxY - Globals.BackendWrapper.plottingSampleMinY

                ValueAxis {
                    id: sampleAxisY
                    titleText: "Log10 " + Globals.BackendWrapper.plottingYAxisTitle
                    // min/max set imperatively to avoid binding reset during zoom
                    property double minAfterReset: Globals.BackendWrapper.plottingSampleMinY - sampleChartView.yRange * 0.01
                    property double maxAfterReset: Globals.BackendWrapper.plottingSampleMaxY + sampleChartView.yRange * 0.01
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
                        sampleAxisXLog.min = sampleAxisXLog.minAfterReset
                        sampleAxisXLog.max = sampleAxisXLog.maxAfterReset
                    } else {
                        sampleAxisX.min = sampleAxisX.minAfterReset
                        sampleAxisX.max = sampleAxisX.maxAfterReset
                    }
                    sampleAxisY.min = sampleAxisY.minAfterReset
                    sampleAxisY.max = sampleAxisY.maxAfterReset
                }

                // Handle logarithmic axis changes
                onUseLogQAxisChanged: {
                    Qt.callLater(container.recreateAllSeries)
                    Qt.callLater(resetAxes)
                }

                GuiComponents.ChartToolbar {
                    chartView: sampleChartView
                    showLegend: Globals.Variables.showLegendOnSamplePage
                    onShowLegendChanged: Globals.Variables.showLegendOnSamplePage = showLegend
                    onInteractionModeChanged: sldChart.chartView.allowZoom = allowZoom
                    onResetClicked: sldChart.chartView.resetAxes()
                }

                // Legend showing all models or channels
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

                        Repeater {
                            model: container.isPolarizationMode ? container.visiblePolarizationChannels() : []
                            EaElements.Label {
                                text: `━  ${modelData.label || modelData.key} (${modelData.description || ''})`
                                color: modelData.color || EaStyle.Colors.themeAccent
                            }
                        }

                        Repeater {
                            model: container.isPolarizationMode ? [] : container.modelCount
                            EaElements.Label {
                                text: '━  ' + Globals.BackendWrapper.sampleModels[index].label
                                color: Globals.BackendWrapper.sampleModels[index].color
                            }
                        }
                    }
                }

                EaElements.ToolTip {
                    id: sampleDataToolTip

                    arrowLength: 0
                    textFormat: Text.RichText
                }

                GuiComponents.ChartMouseControls {
                    chartView: sampleChartView
                }

                Component.onCompleted: {
                    Globals.References.pages.sample.mainContent.sampleView = sampleChartView
                }
            }
        }

        // SLD Chart (1/3 height)
        Gui.SldChart {
            id: sldChart

            SplitView.fillHeight: true
            SplitView.preferredHeight: parent.height * 0.33
            SplitView.minimumHeight: 80

            showLegend: Globals.Variables.showLegendOnSamplePage
            reverseZAxis: Globals.Variables.reverseSldZAxis
            onShowLegendChanged: Globals.Variables.showLegendOnSamplePage = showLegend

            Component.onCompleted: {
                Globals.References.pages.sample.mainContent.sldView = sldChart.chartView
            }
        }
    }

    // Create series dynamically when model count changes
    onModelCountChanged: {
        Qt.callLater(recreateAllSeries)
    }

    onIsPolarizationModeChanged: {
        Qt.callLater(recreateAllSeries)
    }

    // Refresh all chart series when model data changes
    Connections {
        target: Globals.BackendWrapper
        function onSamplePageDataChanged() {
            refreshAllCharts()
        }
        function onSamplePageResetAxes() {
            sampleCombinedResetAxesTimer.start()
            sldCombinedResetAxesTimer.start()
        }
        function onPlotModeChanged() {
            refreshAllCharts()
            // Delay resetAxes to allow axis range properties to update first
            sampleCombinedResetAxesTimer.start()
        }
        function onChartAxesResetRequested() {
            // Reset axes when model is loaded (e.g., from ORSO file)
            sampleCombinedResetAxesTimer.start()
        }
        function onPolarizationDisplayChanged() {
            Qt.callLater(recreateAllSeries)
            sampleCombinedResetAxesTimer.start()
        }
        function onPolarizationDataChanged() {
            refreshAllCharts()
        }
    }

    Timer {
        id: sampleCombinedResetAxesTimer
        interval: 75
        repeat: false
        onTriggered: {
            sampleChartView.resetAxes()
            sldChart.chartView.resetAxes()
        }
    }

    Timer {
        id: sldCombinedResetAxesTimer
        interval: 75
        repeat: false
        onTriggered: sldChart.chartView.resetAxes()
    }

    Component.onCompleted: {
        Qt.callLater(recreateAllSeries)
    }

    // Recreate all series for all models
    function recreateAllSeries() {
        // Remove old sample series
        for (let i = 0; i < sampleSeries.length; i++) {
            if (sampleSeries[i] && sampleSeries[i].serie) {
                sampleChartView.removeSeries(sampleSeries[i].serie)
            }
        }
        sampleSeries = []

        // Determine which x-axis to use for sample chart based on log setting
        const sampleXAxisToUse = sampleChartView.useLogQAxis ? sampleAxisXLog : sampleAxisX

        // Create new series for each model
        const models = Globals.BackendWrapper.sampleModels
        if (container.isPolarizationMode) {
            const channels = visiblePolarizationChannels()
            for (let modelIndex = 0; modelIndex < models.length; modelIndex++) {
                for (let channelIndex = 0; channelIndex < channels.length; channelIndex++) {
                    const channel = channels[channelIndex]
                    const label = models.length > 1 ? `${models[modelIndex].label} - ${channel.label || channel.key}` : (channel.label || channel.key)
                    const sampleLine = sampleChartView.createSeries(ChartView.SeriesTypeLine, label, sampleXAxisToUse, sampleAxisY)
                    sampleLine.color = channel.color || models[modelIndex].color
                    sampleLine.width = 2
                    sampleLine.style = models.length > 1 ? modelLineStyle(modelIndex) : Qt.SolidLine
                    sampleLine.useOpenGL = EaGlobals.Vars.useOpenGL
                    sampleLine.hovered.connect((point, state) => showMainTooltip(sampleChartView, sampleDataToolTip, point, state))
                    sampleSeries.push({
                        serie: sampleLine,
                        modelIndex: modelIndex,
                        channelKey: channel.key
                    })
                }
            }

            refreshAllCharts()
            return
        }

        for (let k = 0; k < models.length; k++) {
            // Create sample series
            const sampleLine = sampleChartView.createSeries(ChartView.SeriesTypeLine, models[k].label, sampleXAxisToUse, sampleAxisY)
            sampleLine.color = models[k].color
            sampleLine.width = 2
            sampleLine.useOpenGL = EaGlobals.Vars.useOpenGL
            // Connect hovered signal for tooltip
            sampleLine.hovered.connect((point, state) => showMainTooltip(sampleChartView, sampleDataToolTip, point, state))
            sampleSeries.push({ serie: sampleLine, modelIndex: k, channelKey: null })
        }

        // Populate data
        refreshAllCharts()
    }

    // Refresh data in all series
    function refreshAllCharts() {
        // Refresh sample series
        for (let i = 0; i < sampleSeries.length; i++) {
            const seriesSet = sampleSeries[i]
            const series = seriesSet ? seriesSet.serie : null
            if (series) {
                series.clear()
                const points = container.isPolarizationMode && seriesSet.channelKey
                               ? Globals.BackendWrapper.plottingGetSampleChannelDataPoints(seriesSet.modelIndex, seriesSet.channelKey)
                               : Globals.BackendWrapper.plottingGetSampleDataPointsForModel(seriesSet.modelIndex)
                for (let p = 0; p < points.length; p++) {
                    series.append(points[p].x, points[p].y)
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

    function visiblePolarizationChannels() {
        const selectedKeys = Globals.BackendWrapper.polarizationVisibleChannelKeys || []
        const channels = Globals.BackendWrapper.polarizationChannels || []
        const visibleChannels = []
        for (let i = 0; i < channels.length; i++) {
            const channel = channels[i]
            if (!channel || channel.enabled === false || channel.hasCalculated === false) continue
            if (selectedKeys.indexOf(channel.key) === -1) continue
            visibleChannels.push(channel)
        }
        return visibleChannels
    }

    function modelLineStyle(index) {
        switch (index % 4) {
        case 1: return Qt.DashLine
        case 2: return Qt.DotLine
        case 3: return Qt.DashDotLine
        default: return Qt.SolidLine
        }
    }
}
