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

    // Whether to show the legend (caller binds to the right page variable)
    property bool showLegend: false

    // Whether to show the z-axis reversed
    property bool reverseZAxis: false

    // Expose the ChartView so callers can store a reference / call resetAxes
    readonly property alias chartView: chartView

    // Track model count changes to refresh charts
    property int modelCount: Globals.BackendWrapper.sampleModels.length
    property bool componentAware: Globals.BackendWrapper.polarizationAvailable

    // Store dynamically created series
    property var sldSeries: []

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

        property double xRange: Globals.BackendWrapper.plottingSldMaxX - Globals.BackendWrapper.plottingSldMinX

        ValueAxis {
            id: axisX
            titleText: "z (Å)"
            property double minAfterReset: Globals.BackendWrapper.plottingSldMinX - chartView.xRange * 0.01
            property double maxAfterReset: Globals.BackendWrapper.plottingSldMaxX + chartView.xRange * 0.01
            reverse: root.reverseZAxis
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

        property double yRange: Globals.BackendWrapper.plottingSldMaxY - Globals.BackendWrapper.plottingSldMinY

        ValueAxis {
            id: axisY
            titleText: "SLD (10⁻⁶Å⁻²)"
            property double minAfterReset: Globals.BackendWrapper.plottingSldMinY - chartView.yRange * 0.01
            property double maxAfterReset: Globals.BackendWrapper.plottingSldMaxY + chartView.yRange * 0.01
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
            axisX.min = axisX.minAfterReset
            axisX.max = axisX.maxAfterReset
            axisY.min = axisY.minAfterReset
            axisY.max = axisY.maxAfterReset
        }

        GuiComponents.ChartToolbar {
            chartView: chartView
            showLegend: root.showLegend
            onShowLegendChanged: root.showLegend = showLegend
        }

        // Legend showing all models
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

                Repeater {
                    model: root.componentAware ? root.visibleSldComponents() : []
                    EaElements.Label {
                        text: `━  ${modelData.label || modelData.key} (${modelData.symbol || ''})`
                        color: modelData.color || EaStyle.Colors.themeAccent
                    }
                }

                Repeater {
                    model: root.componentAware ? [] : root.modelCount
                    EaElements.Label {
                        text: '━  SLD ' + Globals.BackendWrapper.sampleModels[index].label
                        color: Globals.BackendWrapper.sampleModels[index].color
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

    // Create series dynamically when model count changes
    onModelCountChanged: {
        Qt.callLater(recreateAllSeries)
    }

    onComponentAwareChanged: {
        Qt.callLater(recreateAllSeries)
    }

    // Refresh all chart series when data changes
    Connections {
        target: Globals.BackendWrapper
        function onSamplePageDataChanged() {
            refreshAllCharts()
        }
        function onSamplePageResetAxes() {
            resetAxesTimer.start()
        }
        function onPlotModeChanged() {
            refreshAllCharts()
            resetAxesTimer.start()
        }
        function onChartAxesResetRequested() {
            resetAxesTimer.start()
        }
        function onPolarizationDisplayChanged() {
            Qt.callLater(recreateAllSeries)
        }
        function onPolarizationDataChanged() {
            refreshAllCharts()
        }
    }

    Timer {
        id: resetAxesTimer
        interval: 75
        repeat: false
        onTriggered: chartView.resetAxes()
    }

    Component.onCompleted: {
        Qt.callLater(recreateAllSeries)
    }

    function recreateAllSeries() {
        // Remove old series
        for (let i = 0; i < sldSeries.length; i++) {
            if (sldSeries[i] && sldSeries[i].serie) {
                chartView.removeSeries(sldSeries[i].serie)
            }
        }
        sldSeries = []

        if (componentAware) {
            const models = Globals.BackendWrapper.sampleModels
            const components = visibleSldComponents()
            for (let modelIndex = 0; modelIndex < models.length; modelIndex++) {
                for (let componentIndex = 0; componentIndex < components.length; componentIndex++) {
                    const component = components[componentIndex]
                    const label = models.length > 1 ? `${models[modelIndex].label} - ${component.label}` : component.label
                    const line = chartView.createSeries(ChartView.SeriesTypeLine, label, axisX, axisY)
                    line.color = component.color || models[modelIndex].color
                    line.width = 2
                    line.style = models.length > 1 ? experimentLineStyle(modelIndex) : Qt.SolidLine
                    line.useOpenGL = EaGlobals.Vars.useOpenGL
                    line.hovered.connect((point, state) => showMainTooltip(point, state))
                    sldSeries.push({
                        serie: line,
                        modelIndex: modelIndex,
                        componentKey: component.key
                    })
                }
            }

            refreshAllCharts()
            return
        }

        // Create new series for each model
        const models = Globals.BackendWrapper.sampleModels
        for (let k = 0; k < models.length; k++) {
            const line = chartView.createSeries(ChartView.SeriesTypeLine, models[k].label, axisX, axisY)
            line.color = models[k].color
            line.width = 2
            line.useOpenGL = EaGlobals.Vars.useOpenGL
            line.hovered.connect((point, state) => showMainTooltip(point, state))
            sldSeries.push({ serie: line, modelIndex: k, componentKey: null })
        }

        refreshAllCharts()
    }

    function refreshAllCharts() {
        for (let i = 0; i < sldSeries.length; i++) {
            const seriesSet = sldSeries[i]
            const series = seriesSet ? seriesSet.serie : null
            if (series) {
                series.clear()
                const points = componentAware && seriesSet.componentKey
                               ? Globals.BackendWrapper.plottingGetSldComponentDataPoints(seriesSet.modelIndex, seriesSet.componentKey)
                               : Globals.BackendWrapper.plottingGetSldDataPointsForModel(seriesSet.modelIndex)
                for (let p = 0; p < points.length; p++) {
                    series.append(points[p].x, points[p].y)
                }
            }
        }
    }

    function showMainTooltip(point, state) {
        if (!chartView.allowHover) {
            return
        }
        const pos = chartView.mapToPosition(Qt.point(point.x, point.y))
        dataToolTip.x = pos.x
        dataToolTip.y = pos.y
        dataToolTip.text = `<p align="left">x: ${point.x.toFixed(3)}<br\>y: ${point.y.toFixed(3)}</p>`
        dataToolTip.parent = chartView
        dataToolTip.visible = state
    }

    function visibleSldComponents() {
        const selectedKeys = Globals.BackendWrapper.polarizationVisibleSldComponentKeys || []
        const components = Globals.BackendWrapper.polarizationSldComponents || []
        const visibleComponents = []
        for (let i = 0; i < components.length; i++) {
            const component = components[i]
            if (!component || component.enabled === false || component.available === false) continue
            if (selectedKeys.indexOf(component.key) === -1) continue
            visibleComponents.push(component)
        }
        return visibleComponents
    }

    function experimentLineStyle(index) {
        switch (index % 4) {
        case 1: return Qt.DashLine
        case 2: return Qt.DotLine
        case 3: return Qt.DashDotLine
        default: return Qt.SolidLine
        }
    }
}
