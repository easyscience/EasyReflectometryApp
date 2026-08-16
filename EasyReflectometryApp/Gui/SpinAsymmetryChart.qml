// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtCharts

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

// Spin asymmetry SA(q) = (R↑↑ − R↓↓) / (R↑↑ + R↓↓) of the current experiment.
// Shared by the Experiment page (measured only — "do I have a magnetic
// signal?") and the Analysis page (measured plus the model curve — "does the
// magnetic part of the fit match?"). Both pages only show it when the current
// experiment measured both non-spin-flip channels.
Rectangle {
    id: root

    color: EaStyle.Colors.chartBackground

    // Draw the model SA on top of the data (Analysis page).
    property bool showCalculated: false
    property bool showLegend: false

    readonly property alias chartView: chartView

    readonly property int experimentIndex: Globals.BackendWrapper.analysisExperimentsCurrentIndex
    readonly property int maskedPoints: Globals.BackendWrapper.plottingSpinAsymmetryMaskedPoints
    readonly property int outOfOverlapPoints: Globals.BackendWrapper.plottingSpinAsymmetryOutOfOverlapPoints
    readonly property bool calculatedAvailable: root.showCalculated
                                                && Globals.BackendWrapper.plottingSpinAsymmetryCalculatedAvailable

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

        property double xRange: Globals.BackendWrapper.plottingSpinAsymmetryMaxX
                                - Globals.BackendWrapper.plottingSpinAsymmetryMinX

        ValueAxis {
            id: axisX
            titleText: "q (1/Å)"
            property double minAfterReset: Globals.BackendWrapper.plottingSpinAsymmetryMinX - chartView.xRange * 0.02
            property double maxAfterReset: Globals.BackendWrapper.plottingSpinAsymmetryMaxX + chartView.xRange * 0.02
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

        property double yRange: Globals.BackendWrapper.plottingSpinAsymmetryMaxY
                                - Globals.BackendWrapper.plottingSpinAsymmetryMinY

        ValueAxis {
            id: axisY
            titleText: "Spin asymmetry"
            property double minAfterReset: Globals.BackendWrapper.plottingSpinAsymmetryMinY - chartView.yRange * 0.05
            property double maxAfterReset: Globals.BackendWrapper.plottingSpinAsymmetryMaxY + chartView.yRange * 0.05
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

        // SA = 0 is the "no magnetism" reference line.
        LineSeries {
            id: zeroLine
            axisX: axisX
            axisY: axisY
            color: EaStyle.Colors.chartGridLine
            width: 1
            style: Qt.DashLine
            useOpenGL: false
        }

        ScatterSeries {
            id: measuredSerie
            axisX: axisX
            axisY: axisY
            markerSize: 6
            borderWidth: 0
            color: EaStyle.Colors.chartForegrounds[1]
            useOpenGL: EaGlobals.Vars.useOpenGL
            onHovered: (point, state) => root.showMainTooltip(point, state)
        }

        LineSeries {
            id: errorUpperSerie
            axisX: axisX
            axisY: axisY
            color: measuredSerie.color
            width: 1
            style: Qt.DotLine
            useOpenGL: EaGlobals.Vars.useOpenGL
        }

        LineSeries {
            id: errorLowerSerie
            axisX: axisX
            axisY: axisY
            color: measuredSerie.color
            width: 1
            style: Qt.DotLine
            useOpenGL: EaGlobals.Vars.useOpenGL
        }

        LineSeries {
            id: calculatedSerie
            axisX: axisX
            axisY: axisY
            color: "#E67E22"
            width: 2
            visible: root.calculatedAvailable
            useOpenGL: EaGlobals.Vars.useOpenGL
        }

        // Tool buttons
        Row {
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

                EaElements.Label {
                    text: '●  ' + qsTr("Measured SA")
                    color: measuredSerie.color
                }
                EaElements.Label {
                    // Connected upper/lower curves, the convention this app
                    // already uses for the reflectivity charts - not per-point
                    // error bars.
                    text: '┈  ' + qsTr("Uncertainty envelope (1σ)")
                    color: errorUpperSerie.color
                }
                EaElements.Label {
                    visible: root.calculatedAvailable
                    text: '━  ' + qsTr("Calculated SA")
                    color: calculatedSerie.color
                }
            }
        }

        EaElements.ToolTip {
            id: dataToolTip
            arrowLength: 0
            textFormat: Text.RichText
        }
    }

    // Points the backend could not turn into a meaningful SA — say so rather
    // than truncating silently.
    Column {
        x: chartView.plotArea.x + EaStyle.Sizes.fontPixelSize
        y: chartView.plotArea.y + EaStyle.Sizes.fontPixelSize
        spacing: EaStyle.Sizes.fontPixelSize * 0.2

        EaElements.Label {
            visible: root.maskedPoints > 0
            color: EaStyle.Colors.themeForegroundMinor
            text: qsTr("%1 point(s) hidden: R↑↑ + R↓↓ is not significantly above zero there").arg(root.maskedPoints)
        }

        EaElements.Label {
            visible: root.outOfOverlapPoints > 0
            color: EaStyle.Colors.themeForegroundMinor
            text: qsTr("%1 point(s) hidden: the ↑↑ and ↓↓ channels do not cover the same q there")
                  .arg(root.outOfOverlapPoints)
        }
    }

    Component.onCompleted: Qt.callLater(refresh)

    onExperimentIndexChanged: Qt.callLater(refresh)
    onShowCalculatedChanged: Qt.callLater(refresh)

    Connections {
        target: Globals.BackendWrapper
        function onSpinAsymmetryChanged() {
            root.refresh()
        }
    }

    function refresh() {
        measuredSerie.clear()
        errorUpperSerie.clear()
        errorLowerSerie.clear()
        calculatedSerie.clear()
        zeroLine.clear()

        const points = Globals.BackendWrapper.plottingGetSpinAsymmetryPoints(root.experimentIndex)
        for (let i = 0; i < points.length; i++) {
            measuredSerie.append(points[i].x, points[i].y)
            errorUpperSerie.append(points[i].x, points[i].errorUpper)
            errorLowerSerie.append(points[i].x, points[i].errorLower)
        }

        if (points.length > 0) {
            zeroLine.append(points[0].x, 0)
            zeroLine.append(points[points.length - 1].x, 0)
        }

        if (root.showCalculated) {
            const calculated = Globals.BackendWrapper.plottingGetSpinAsymmetryCalculatedPoints(root.experimentIndex)
            for (let c = 0; c < calculated.length; c++) {
                calculatedSerie.append(calculated[c].x, calculated[c].y)
            }
        }

        Qt.callLater(chartView.resetAxes)
    }

    function showMainTooltip(point, state) {
        if (!chartView.allowHover) {
            return
        }
        const pos = chartView.mapToPosition(Qt.point(point.x, point.y))
        dataToolTip.x = pos.x
        dataToolTip.y = pos.y
        dataToolTip.text = `<p align="left">q: ${point.x.toFixed(4)}<br\>SA: ${point.y.toFixed(4)}</p>`
        dataToolTip.parent = chartView
        dataToolTip.visible = state
    }
}
