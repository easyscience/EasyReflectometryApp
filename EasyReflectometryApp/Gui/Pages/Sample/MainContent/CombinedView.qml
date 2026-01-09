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

    // Track model count changes to refresh charts
    property int modelCount: Globals.BackendWrapper.sampleModels.length

    // Store dynamically created series
    property var sampleSeries: []
    property var sldSeries: []

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

                ValueAxis {
                    id: sampleAxisX
                    titleText: "q (Å⁻¹)"
                    min: Globals.BackendWrapper.plottingSampleMinX - sampleChartView.xRange * 0.01
                    max: Globals.BackendWrapper.plottingSampleMaxX + sampleChartView.xRange * 0.01
                    property double minAfterReset: Globals.BackendWrapper.plottingSampleMinX - sampleChartView.xRange * 0.01
                    property double maxAfterReset: Globals.BackendWrapper.plottingSampleMaxX + sampleChartView.xRange * 0.01
                    color: EaStyle.Colors.chartAxis
                    gridLineColor: EaStyle.Colors.chartGridLine
                    minorGridLineColor: EaStyle.Colors.chartMinorGridLine
                    labelsColor: EaStyle.Colors.chartLabels
                    titleBrush: EaStyle.Colors.chartLabels
                }

                property double yRange: Globals.BackendWrapper.plottingSampleMaxY - Globals.BackendWrapper.plottingSampleMinY

                ValueAxis {
                    id: sampleAxisY
                    titleText: "Log10 R(q)"
                    min: Globals.BackendWrapper.plottingSampleMinY - sampleChartView.yRange * 0.01
                    max: Globals.BackendWrapper.plottingSampleMaxY + sampleChartView.yRange * 0.01
                    property double minAfterReset: Globals.BackendWrapper.plottingSampleMinY - sampleChartView.yRange * 0.01
                    property double maxAfterReset: Globals.BackendWrapper.plottingSampleMaxY + sampleChartView.yRange * 0.01
                    color: EaStyle.Colors.chartAxis
                    gridLineColor: EaStyle.Colors.chartGridLine
                    minorGridLineColor: EaStyle.Colors.chartMinorGridLine
                    labelsColor: EaStyle.Colors.chartLabels
                    titleBrush: EaStyle.Colors.chartLabels
                }

                function resetAxes() {
                    sampleAxisX.min = sampleAxisX.minAfterReset
                    sampleAxisX.max = sampleAxisX.maxAfterReset
                    sampleAxisY.min = sampleAxisY.minAfterReset
                    sampleAxisY.max = sampleAxisY.maxAfterReset
                }

                // Tool buttons
                Row {
                    id: sampleToolButtons

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
                        onClicked: sampleChartView.allowHover = !sampleChartView.allowHover
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
                            sampleChartView.allowZoom = !sampleChartView.allowZoom
                            sldChartView.allowZoom = sampleChartView.allowZoom
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
                            sampleChartView.allowZoom = !sampleChartView.allowZoom
                            sldChartView.allowZoom = sampleChartView.allowZoom
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
                            sampleChartView.resetAxes()
                            sldChartView.resetAxes()
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

                Component.onCompleted: {
                    Globals.References.pages.sample.mainContent.sampleView = sampleChartView
                }

                // Sync X-axis with SLD chart
                Connections {
                    target: sampleAxisX
                    function onMinChanged() { syncXAxes() }
                    function onMaxChanged() { syncXAxes() }
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

            ChartView {
                id: sldChartView

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
                    id: sldAxisX
                    titleText: "z (Å)"
                    min: Globals.BackendWrapper.plottingSldMinX - sldChartView.xRange * 0.01
                    max: Globals.BackendWrapper.plottingSldMaxX + sldChartView.xRange * 0.01
                    property double minAfterReset: Globals.BackendWrapper.plottingSldMinX - sldChartView.xRange * 0.01
                    property double maxAfterReset: Globals.BackendWrapper.plottingSldMaxX + sldChartView.xRange * 0.01
                    color: EaStyle.Colors.chartAxis
                    gridLineColor: EaStyle.Colors.chartGridLine
                    minorGridLineColor: EaStyle.Colors.chartMinorGridLine
                    labelsColor: EaStyle.Colors.chartLabels
                    titleBrush: EaStyle.Colors.chartLabels
                }

                property double yRange: Globals.BackendWrapper.plottingSldMaxY - Globals.BackendWrapper.plottingSldMinY

                ValueAxis {
                    id: sldAxisY
                    titleText: "SLD (10⁻⁶Å⁻²)"
                    min: Globals.BackendWrapper.plottingSldMinY - sldChartView.yRange * 0.01
                    max: Globals.BackendWrapper.plottingSldMaxY + sldChartView.yRange * 0.01
                    property double minAfterReset: Globals.BackendWrapper.plottingSldMinY - sldChartView.yRange * 0.01
                    property double maxAfterReset: Globals.BackendWrapper.plottingSldMaxY + sldChartView.yRange * 0.01
                    color: EaStyle.Colors.chartAxis
                    gridLineColor: EaStyle.Colors.chartGridLine
                    minorGridLineColor: EaStyle.Colors.chartMinorGridLine
                    labelsColor: EaStyle.Colors.chartLabels
                    titleBrush: EaStyle.Colors.chartLabels
                }

                function resetAxes() {
                    sldAxisX.min = sldAxisX.minAfterReset
                    sldAxisX.max = sldAxisX.maxAfterReset
                    sldAxisY.min = sldAxisY.minAfterReset
                    sldAxisY.max = sldAxisY.maxAfterReset
                }

                // Legend showing all models
                Rectangle {
                    visible: Globals.Variables.showLegendOnSamplePage

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

                        Repeater {
                            model: container.modelCount
                            EaElements.Label {
                                text: '━  SLD ' + Globals.BackendWrapper.sampleModels[index].label
                                color: Globals.BackendWrapper.sampleModels[index].color
                            }
                        }
                    }
                }

                EaElements.ToolTip {
                    id: sldDataToolTip

                    arrowLength: 0
                    textFormat: Text.RichText
                }

                Component.onCompleted: {
                    Globals.References.pages.sample.mainContent.sldView = sldChartView
                }
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

        // Remove old SLD series
        for (let j = 0; j < sldSeries.length; j++) {
            if (sldSeries[j]) {
                sldChartView.removeSeries(sldSeries[j])
            }
        }
        sldSeries = []

        // Create new series for each model
        const models = Globals.BackendWrapper.sampleModels
        for (let k = 0; k < models.length; k++) {
            // Create sample series
            const sampleLine = sampleChartView.createSeries(ChartView.SeriesTypeLine, models[k].label, sampleAxisX, sampleAxisY)
            sampleLine.color = models[k].color
            sampleLine.width = 2
            sampleLine.useOpenGL = EaGlobals.Vars.useOpenGL
            // Connect hovered signal for tooltip
            sampleLine.hovered.connect((point, state) => showMainTooltip(sampleChartView, sampleDataToolTip, point, state))
            sampleSeries.push(sampleLine)

            // Create SLD series
            const sldLine = sldChartView.createSeries(ChartView.SeriesTypeLine, "SLD " + models[k].label, sldAxisX, sldAxisY)
            sldLine.color = models[k].color
            sldLine.width = 2
            sldLine.useOpenGL = EaGlobals.Vars.useOpenGL
            // Connect hovered signal for tooltip
            sldLine.hovered.connect((point, state) => showMainTooltip(sldChartView, sldDataToolTip, point, state))
            sldSeries.push(sldLine)
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

        // Refresh SLD series
        for (let j = 0; j < sldSeries.length && j < models.length; j++) {
            const series = sldSeries[j]
            if (series) {
                series.clear()
                const points = Globals.BackendWrapper.plottingGetSldDataPointsForModel(j)
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

    function syncXAxes() {
        // Keep both charts' X axes synchronized
        if (sampleAxisX.min !== sldAxisX.min ||
            sampleAxisX.max !== sldAxisX.max) {
            sldAxisX.min = sampleAxisX.min
            sldAxisX.max = sampleAxisX.max
        }
    }
}
