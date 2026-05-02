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
    readonly property alias chartView: chartView

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
        property bool useLogQAxis: Globals.Variables.logarithmicQAxis

        ValueAxis {
            id: axisX
            visible: !chartView.useLogQAxis
            titleText: "q (Å⁻¹)"
            min: 0.0
            max: 1.0
            property double minAfterReset: 0.0
            property double maxAfterReset: 1.0
            color: EaStyle.Colors.chartAxis
            gridLineColor: EaStyle.Colors.chartGridLine
            minorGridLineColor: EaStyle.Colors.chartMinorGridLine
            labelsColor: EaStyle.Colors.chartLabels
            titleBrush: EaStyle.Colors.chartLabels
        }

        LogValueAxis {
            id: axisXLog
            visible: chartView.useLogQAxis
            titleText: "q (Å⁻¹)"
            min: 1e-6
            max: 1.0
            property double minAfterReset: 1e-6
            property double maxAfterReset: 1.0
            base: 10
            color: EaStyle.Colors.chartAxis
            gridLineColor: EaStyle.Colors.chartGridLine
            minorGridLineColor: EaStyle.Colors.chartMinorGridLine
            labelsColor: EaStyle.Colors.chartLabels
            titleBrush: EaStyle.Colors.chartLabels
        }

        ValueAxis {
            id: axisY
            titleText: qsTr("Spin asymmetry")
            min: -1.0
            max: 1.0
            property double minAfterReset: -1.0
            property double maxAfterReset: 1.0
            color: EaStyle.Colors.chartAxis
            gridLineColor: EaStyle.Colors.chartGridLine
            minorGridLineColor: EaStyle.Colors.chartMinorGridLine
            labelsColor: EaStyle.Colors.chartLabels
            titleBrush: EaStyle.Colors.chartLabels
        }

        LineSeries {
            id: calculatedSerie
            axisX: chartView.useLogQAxis ? axisXLog : axisX
            axisY: axisY
            useOpenGL: EaGlobals.Vars.useOpenGL
            width: 2
            color: EaStyle.Colors.themeAccent
            visible: false
            onHovered: (point, state) => showMainTooltip(point, state)
        }

        ScatterSeries {
            id: measuredSerie
            axisX: chartView.useLogQAxis ? axisXLog : axisX
            axisY: axisY
            useOpenGL: EaGlobals.Vars.useOpenGL
            markerSize: EaStyle.Sizes.fontPixelSize * 0.6
            color: EaStyle.Colors.themeForeground
            borderColor: color
            visible: false
            onHovered: (point, state) => showMainTooltip(point, state)
        }

        LineSeries {
            id: sigmaUpperSerie
            axisX: chartView.useLogQAxis ? axisXLog : axisX
            axisY: axisY
            useOpenGL: EaGlobals.Vars.useOpenGL
            width: 1
            style: Qt.DotLine
            color: measuredSerie.color
            visible: false
        }

        LineSeries {
            id: sigmaLowerSerie
            axisX: chartView.useLogQAxis ? axisXLog : axisX
            axisY: axisY
            useOpenGL: EaGlobals.Vars.useOpenGL
            width: 1
            style: Qt.DotLine
            color: measuredSerie.color
            visible: false
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

        onUseLogQAxisChanged: refreshSpinAsymmetry()

        GuiComponents.ChartToolbar {
            chartView: chartView
            showLegend: root.showLegend
            controlsVisible: Globals.BackendWrapper.polarizationAvailable
            onShowLegendChanged: root.showLegend = showLegend
        }

        Rectangle {
            visible: root.showLegend && Globals.BackendWrapper.polarizationAvailable

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

                EaElements.Label {
                    text: '━  ' + qsTr("Calculated")
                    color: calculatedSerie.color
                }
                EaElements.Label {
                    text: '•  ' + qsTr("Measured")
                    color: measuredSerie.color
                }
                EaElements.Label {
                    visible: sigmaUpperSerie.visible
                    text: '⋅ ⋅ ⋅  ' + qsTr("Measured ± σ")
                    color: measuredSerie.color
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

    function setAllowZoom(value) {
        chartView.allowZoom = value
    }

    function refreshSpinAsymmetry() {
        calculatedSerie.clear()
        measuredSerie.clear()
        sigmaUpperSerie.clear()
        sigmaLowerSerie.clear()

        var data = Globals.BackendWrapper.plottingGetSpinAsymmetryDataPoints(Globals.BackendWrapper.analysisExperimentsCurrentIndex)
        var x = data.x || []
        var calculated = data.calculated || []
        var measured = data.measured || []
        var sigma = data.sigma || []

        for (var i = 0; i < x.length && i < calculated.length; i++) {
            calculatedSerie.append(x[i], calculated[i])
        }
        for (var j = 0; j < x.length && j < measured.length; j++) {
            measuredSerie.append(x[j], measured[j])
            if (j < sigma.length && isFinite(sigma[j])) {
                sigmaUpperSerie.append(x[j], measured[j] + sigma[j])
                sigmaLowerSerie.append(x[j], measured[j] - sigma[j])
            }
        }

        calculatedSerie.visible = calculatedSerie.count > 0
        measuredSerie.visible = measuredSerie.count > 0
        sigmaUpperSerie.visible = sigmaUpperSerie.count > 0
        sigmaLowerSerie.visible = sigmaLowerSerie.count > 0
        updateAxesFromData(x, measured, sigma, calculated)
    }

    function updateAxesFromData(x, measured, sigma, calculated) {
        if (!x || x.length === 0) return

        var minX = Number.POSITIVE_INFINITY
        var maxX = Number.NEGATIVE_INFINITY
        var minY = -1.0
        var maxY = 1.0

        for (var i = 0; i < x.length; i++) {
            if (isFinite(x[i])) {
                minX = Math.min(minX, x[i])
                maxX = Math.max(maxX, x[i])
            }
        }
        for (var c = 0; c < calculated.length; c++) {
            if (isFinite(calculated[c])) {
                minY = Math.min(minY, calculated[c])
                maxY = Math.max(maxY, calculated[c])
            }
        }
        for (var m = 0; m < measured.length; m++) {
            if (isFinite(measured[m])) {
                var delta = m < sigma.length && isFinite(sigma[m]) ? sigma[m] : 0
                minY = Math.min(minY, measured[m] - delta)
                maxY = Math.max(maxY, measured[m] + delta)
            }
        }

        if (!isFinite(minX) || !isFinite(maxX) || minX === maxX) return

        var xMargin = (maxX - minX) * 0.03
        axisX.minAfterReset = minX - xMargin
        axisX.maxAfterReset = maxX + xMargin
        axisXLog.minAfterReset = Math.max(minX, 1e-6)
        axisXLog.maxAfterReset = maxX * 1.1
        axisY.minAfterReset = Math.max(-1.25, minY - 0.05)
        axisY.maxAfterReset = Math.min(1.25, maxY + 0.05)
        chartView.resetAxes()
    }

    function showMainTooltip(point, state) {
        if (!chartView.allowHover) return
        const pos = chartView.mapToPosition(Qt.point(point.x, point.y))
        dataToolTip.x = pos.x
        dataToolTip.y = pos.y
        dataToolTip.text = `<p align="left">q: ${point.x.toFixed(4)}<br/>SA: ${point.y.toFixed(3)}</p>`
        dataToolTip.parent = chartView
        dataToolTip.visible = state
    }

    Connections {
        target: Globals.BackendWrapper
        function onPolarizationDataChanged() { refreshSpinAsymmetry() }
    }

    Component.onCompleted: {
        Globals.References.pages.analysis.mainContent.spinAsymmetryView = chartView
        refreshSpinAsymmetry()
    }
}
