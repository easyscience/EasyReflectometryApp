// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtCharts

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements

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

        // Tool buttons
        Row {
            id: toolButtons
            z: 1

            x: chartView.plotArea.x + chartView.plotArea.width - width
            y: chartView.plotArea.y - height - EaStyle.Sizes.fontPixelSize

            spacing: 0.25 * EaStyle.Sizes.fontPixelSize

            EaElements.TabButton {
                checked: root.showLegend
                autoExclusive: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "align-left"
                ToolTip.text: root.showLegend ? qsTr("Hide legend") : qsTr("Show legend")
                onClicked: root.showLegend = checked
            }

            EaElements.TabButton {
                checked: chartView.allowHover
                autoExclusive: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "comment-alt"
                ToolTip.text: qsTr("Show coordinates tooltip on hover")
                onClicked: chartView.allowHover = checked
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
                onClicked: chartView.allowZoom = !checked
            }

            EaElements.TabButton {
                checked: chartView.allowZoom
                autoExclusive: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "expand"
                ToolTip.text: qsTr("Enable box zoom")
                onClicked: chartView.allowZoom = checked
            }

            EaElements.TabButton {
                checkable: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "home"
                ToolTip.text: qsTr("Reset axes")
                onClicked: chartView.resetAxes()
            }
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
                    visible: !isMultiExperimentMode
                    text: '━  ' + qsTr('Residual')
                    color: singleResidualSerie.color
                }

                // Multi-experiment
                Repeater {
                    model: isMultiExperimentMode ? Globals.BackendWrapper.plottingIndividualExperimentDataList : []
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

        // Zoom rectangle
        Rectangle {
            id: recZoom

            property int xScaleZoom: 0
            property int yScaleZoom: 0

            visible: false
            transform: Scale {
                origin.x: 0
                origin.y: 0
                xScale: recZoom.xScaleZoom
                yScale: recZoom.yScaleZoom
            }
            border.color: EaStyle.Colors.appBorder
            border.width: 1
            opacity: 0.9
            color: 'transparent'

            Rectangle {
                anchors.fill: parent
                opacity: 0.5
                color: recZoom.border.color
            }
        }

        // Zoom with left mouse button
        MouseArea {
            id: zoomMouseArea

            enabled: chartView.allowZoom
            anchors.fill: chartView
            acceptedButtons: Qt.LeftButton
            onPressed: {
                recZoom.x = mouseX
                recZoom.y = mouseY
                recZoom.visible = true
            }
            onMouseXChanged: {
                if (mouseX > recZoom.x) {
                    recZoom.xScaleZoom = 1
                    recZoom.width = Math.min(mouseX, chartView.width) - recZoom.x
                } else {
                    recZoom.xScaleZoom = -1
                    recZoom.width = recZoom.x - Math.max(mouseX, 0)
                }
            }
            onMouseYChanged: {
                if (mouseY > recZoom.y) {
                    recZoom.yScaleZoom = 1
                    recZoom.height = Math.min(mouseY, chartView.height) - recZoom.y
                } else {
                    recZoom.yScaleZoom = -1
                    recZoom.height = recZoom.y - Math.max(mouseY, 0)
                }
            }
            onReleased: {
                const x = Math.min(recZoom.x, mouseX) - chartView.anchors.leftMargin
                const y = Math.min(recZoom.y, mouseY) - chartView.anchors.topMargin
                const width = recZoom.width
                const height = recZoom.height
                chartView.zoomIn(Qt.rect(x, y, width, height))
                recZoom.visible = false
            }
        }

        // Pan with left mouse button
        MouseArea {
            property real pressedX
            property real pressedY
            property int threshold: 1

            enabled: !zoomMouseArea.enabled
            anchors.fill: chartView
            acceptedButtons: Qt.LeftButton
            onPressed: {
                pressedX = mouseX
                pressedY = mouseY
            }
            onMouseXChanged: Qt.callLater(update)
            onMouseYChanged: Qt.callLater(update)

            function update() {
                const dx = mouseX - pressedX
                const dy = mouseY - pressedY
                pressedX = mouseX
                pressedY = mouseY

                if (dx > threshold)      chartView.scrollLeft(dx)
                else if (dx < -threshold) chartView.scrollRight(-dx)
                if (dy > threshold)      chartView.scrollUp(dy)
                else if (dy < -threshold) chartView.scrollDown(-dy)
            }
        }

        // Reset axes with right mouse button
        MouseArea {
            anchors.fill: chartView
            acceptedButtons: Qt.RightButton
            onClicked: chartView.resetAxes()
        }
    }

    // Multi-experiment mode flag
    property bool isMultiExperimentMode: {
        try { return Globals.BackendWrapper.plottingIsMultiExperimentMode || false }
        catch (e) { return false }
    }

    // Re-populate charts when backend signals a data/range refresh
    Connections {
        target: Globals.BackendWrapper.activeBackend?.plotting ?? null
        enabled: target !== null
        function onSampleChartRangesChanged() {
            refreshResidualChart()
        }
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

        if (isMultiExperimentMode) {
            _refreshMultiExperiment()
        } else {
            _refreshSingleExperiment()
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
