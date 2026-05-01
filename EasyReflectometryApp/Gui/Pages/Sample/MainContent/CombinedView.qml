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
import Gui.Globals as Globals


Rectangle {
    id: container

    color: EaStyle.Colors.chartBackground

    // Track model count changes to refresh charts
    property int modelCount: Globals.BackendWrapper.sampleModels.length

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

                // Tool buttons
                Row {
                    id: sampleToolButtons
                    z: 1  // Keep buttons above MouseAreas

                    x: sampleChartView.plotArea.x + sampleChartView.plotArea.width - width
                    y: sampleChartView.plotArea.y - height - EaStyle.Sizes.fontPixelSize

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
                        checked: sampleChartView.allowHover
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "comment-alt"
                        ToolTip.text: qsTr("Show coordinates tooltip on hover")
                        onClicked: sampleChartView.allowHover = checked
                    }

                    Item { height: 1; width: 0.5 * EaStyle.Sizes.fontPixelSize }  // spacer

                    EaElements.TabButton {
                        checked: !sampleChartView.allowZoom
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "arrows-alt"
                        ToolTip.text: qsTr("Enable pan")
                        onClicked: {
                            sampleChartView.allowZoom = !checked
                            sldChart.chartView.allowZoom = !checked
                        }
                    }

                    EaElements.TabButton {
                        checked: sampleChartView.allowZoom
                        autoExclusive: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "expand"
                        ToolTip.text: qsTr("Enable box zoom")
                        onClicked: {
                            sampleChartView.allowZoom = checked
                            sldChart.chartView.allowZoom = checked
                        }
                    }

                    EaElements.TabButton {
                        checkable: false
                        height: EaStyle.Sizes.toolButtonHeight
                        width: EaStyle.Sizes.toolButtonHeight
                        borderColor: EaStyle.Colors.chartAxis
                        fontIcon: "home"
                        ToolTip.text: qsTr("Reset axes")
                        onClicked: {
                            sampleChartView.resetAxes()
                            sldChart.chartView.resetAxes()
                        }
                    }
                }

                // Legend showing all models
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
                            model: container.modelCount
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

                // Zoom rectangle
                Rectangle {
                    id: sampleRecZoom

                    property int xScaleZoom: 0
                    property int yScaleZoom: 0

                    visible: false
                    transform: Scale {
                        origin.x: 0
                        origin.y: 0
                        xScale: sampleRecZoom.xScaleZoom
                        yScale: sampleRecZoom.yScaleZoom
                    }
                    border.color: EaStyle.Colors.appBorder
                    border.width: 1
                    opacity: 0.9
                    color: "transparent"

                    Rectangle {
                        anchors.fill: parent
                        opacity: 0.5
                        color: sampleRecZoom.border.color
                    }
                }

                // Zoom with left mouse button
                MouseArea {
                    id: sampleZoomMouseArea

                    enabled: sampleChartView.allowZoom
                    anchors.fill: sampleChartView
                    acceptedButtons: Qt.LeftButton
                    onPressed: {
                        sampleRecZoom.x = mouseX
                        sampleRecZoom.y = mouseY
                        sampleRecZoom.visible = true
                    }
                    onMouseXChanged: {
                        if (mouseX > sampleRecZoom.x) {
                            sampleRecZoom.xScaleZoom = 1
                            sampleRecZoom.width = Math.min(mouseX, sampleChartView.width) - sampleRecZoom.x
                        } else {
                            sampleRecZoom.xScaleZoom = -1
                            sampleRecZoom.width = sampleRecZoom.x - Math.max(mouseX, 0)
                        }
                    }
                    onMouseYChanged: {
                        if (mouseY > sampleRecZoom.y) {
                            sampleRecZoom.yScaleZoom = 1
                            sampleRecZoom.height = Math.min(mouseY, sampleChartView.height) - sampleRecZoom.y
                        } else {
                            sampleRecZoom.yScaleZoom = -1
                            sampleRecZoom.height = sampleRecZoom.y - Math.max(mouseY, 0)
                        }
                    }
                    onReleased: {
                        const x = Math.min(sampleRecZoom.x, mouseX) - sampleChartView.anchors.leftMargin
                        const y = Math.min(sampleRecZoom.y, mouseY) - sampleChartView.anchors.topMargin
                        const width = sampleRecZoom.width
                        const height = sampleRecZoom.height
                        sampleChartView.zoomIn(Qt.rect(x, y, width, height))
                        sampleRecZoom.visible = false
                    }
                }

                // Pan with left mouse button
                MouseArea {
                    property real pressedX
                    property real pressedY
                    property int threshold: 1

                    enabled: !sampleZoomMouseArea.enabled
                    anchors.fill: sampleChartView
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
                            sampleChartView.scrollLeft(dx)
                        else if (dx < -threshold)
                            sampleChartView.scrollRight(-dx)
                        if (dy > threshold)
                            sampleChartView.scrollUp(dy)
                        else if (dy < -threshold)
                            sampleChartView.scrollDown(-dy)
                    }
                }

                // Reset axes with right mouse button
                MouseArea {
                    anchors.fill: sampleChartView
                    acceptedButtons: Qt.RightButton
                    onClicked: sampleChartView.resetAxes()
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
            if (sampleSeries[i]) {
                sampleChartView.removeSeries(sampleSeries[i])
            }
        }
        sampleSeries = []

        // Determine which x-axis to use for sample chart based on log setting
        const sampleXAxisToUse = sampleChartView.useLogQAxis ? sampleAxisXLog : sampleAxisX

        // Create new series for each model
        const models = Globals.BackendWrapper.sampleModels
        for (let k = 0; k < models.length; k++) {
            // Create sample series
            const sampleLine = sampleChartView.createSeries(ChartView.SeriesTypeLine, models[k].label, sampleXAxisToUse, sampleAxisY)
            sampleLine.color = models[k].color
            sampleLine.width = 2
            sampleLine.useOpenGL = EaGlobals.Vars.useOpenGL
            // Connect hovered signal for tooltip
            sampleLine.hovered.connect((point, state) => showMainTooltip(sampleChartView, sampleDataToolTip, point, state))
            sampleSeries.push(sampleLine)
        }

        // Populate data
        refreshAllCharts()
    }

    // Refresh data in all series
    function refreshAllCharts() {
        const models = Globals.BackendWrapper.sampleModels

        // Refresh sample series
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
