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

    // Track model count changes to refresh charts
    property int modelCount: Globals.BackendWrapper.sampleModels.length

    // Store dynamically created series
    property var sampleSeries: []

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

        property double xRange: Globals.BackendWrapper.plottingSampleMaxX - Globals.BackendWrapper.plottingSampleMinX

        // Logarithmic axis control
        property bool useLogQAxis: Globals.Variables.logarithmicQAxis

        ValueAxis {
            id: axisX
            visible: !chartView.useLogQAxis
            titleText: "q (Å⁻¹)"
            // min/max set imperatively to avoid binding reset during zoom
            property double minAfterReset: Globals.BackendWrapper.plottingSampleMinX - chartView.xRange * 0.01
            property double maxAfterReset: Globals.BackendWrapper.plottingSampleMaxX + chartView.xRange * 0.01
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
            id: axisY
            titleText: "Log10 R(q)"
            // min/max set imperatively to avoid binding reset during zoom
            property double minAfterReset: Globals.BackendWrapper.plottingSampleMinY - chartView.yRange * 0.01
            property double maxAfterReset: Globals.BackendWrapper.plottingSampleMaxY + chartView.yRange * 0.01
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
                axisXLog.min = axisXLog.minAfterReset
                axisXLog.max = axisXLog.maxAfterReset
            } else {
                axisX.min = axisX.minAfterReset
                axisX.max = axisX.maxAfterReset
            }
            axisY.min = axisY.minAfterReset
            axisY.max = axisY.maxAfterReset
        }

        // Handle logarithmic axis changes
        onUseLogQAxisChanged: {
            Qt.callLater(recreateAllSeries)
            Qt.callLater(resetAxes)
        }

        // Tool buttons
        Row {
            id: toolButtons
            z: 1  // Keep buttons above MouseAreas

            x: chartView.plotArea.x + chartView.plotArea.width - width
            y: chartView.plotArea.y - height - EaStyle.Sizes.fontPixelSize

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
                fontIcon: "backspace"
                ToolTip.text: qsTr("Reset axes")
                onClicked: chartView.resetAxes()
            }

        }

        // Legend showing all models
        Rectangle {
            visible: Globals.Variables.showLegendOnSamplePage

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
                    model: container.modelCount
                    EaElements.Label {
                        text: '━  ' + Globals.BackendWrapper.sampleModels[index].label
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
            color: "transparent"

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

                if (dx > threshold)
                    chartView.scrollLeft(dx)
                else if (dx < -threshold)
                    chartView.scrollRight(-dx)
                if (dy > threshold)
                    chartView.scrollUp(dy)
                else if (dy < -threshold)
                    chartView.scrollDown(-dy)
            }
        }

        // Reset axes with right mouse button
        MouseArea {
            anchors.fill: chartView
            acceptedButtons: Qt.RightButton
            onClicked: chartView.resetAxes()
        }

        Component.onCompleted: {
            Globals.References.pages.sample.mainContent.sampleView = chartView
        }
    }

    // Create series dynamically when model count changes
    onModelCountChanged: {
        Qt.callLater(recreateAllSeries)
    }

    // Refresh all chart series when data changes
    Connections {
        target: Globals.BackendWrapper
        function onSamplePageDataChanged() {
            refreshAllCharts()
        }
        function onPlotModeChanged() {
            refreshAllCharts()
            // Delay resetAxes to allow axis range properties to update first
            sampleResetAxesTimer.start()
        }
    }

    Timer {
        id: sampleResetAxesTimer
        interval: 50
        repeat: false
        onTriggered: chartView.resetAxes()
    }

    Component.onCompleted: {
        Qt.callLater(recreateAllSeries)
    }

    function recreateAllSeries() {
        // Remove old series
        for (let i = 0; i < sampleSeries.length; i++) {
            if (sampleSeries[i]) {
                chartView.removeSeries(sampleSeries[i])
            }
        }
        sampleSeries = []

        // Determine which x-axis to use based on log setting
        const xAxisToUse = chartView.useLogQAxis ? axisXLog : axisX

        // Create new series for each model
        const models = Globals.BackendWrapper.sampleModels
        for (let k = 0; k < models.length; k++) {
            const line = chartView.createSeries(ChartView.SeriesTypeLine, models[k].label, xAxisToUse, axisY)
            line.color = models[k].color
            line.width = 2
            line.useOpenGL = EaGlobals.Vars.useOpenGL
            // Connect hovered signal for tooltip
            line.hovered.connect((point, state) => showMainTooltip(chartView, point, state))
            sampleSeries.push(line)
        }

        refreshAllCharts()
    }

    function refreshAllCharts() {
        const models = Globals.BackendWrapper.sampleModels
        for (let i = 0; i < sampleSeries.length && i < models.length; i++) {
            const series = sampleSeries[i]
            if (series) {
                series.clear()
                const points = Globals.BackendWrapper.plottingGetSampleDataPointsForModel(i)
                for (let p = 0; p < points.length; p++) {
                    series.append(points[p].x, points[p].y)
                }
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

