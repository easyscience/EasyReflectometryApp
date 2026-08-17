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


Rectangle {
    id: root

    color: EaStyle.Colors.chartBackground

    // Whether to show the legend (caller binds to the right page variable)
    property bool showLegend: false

    // Whether to show the z-axis reversed
    property bool reverseZAxis: false

    // Expose the ChartView so callers can store a reference / call resetAxes
    readonly property alias chartView: chartView
    readonly property alias chartAxisX: axisX
    readonly property alias chartAxisY: axisY

    // Track model count changes to refresh charts
    property int modelCount: Globals.BackendWrapper.sampleModels.length

    // Store dynamically created series
    property var sldSeries: []

    // Magnetic profile series: one entry {series, modelIndex, curve} per drawn
    // magnetic curve. Empty unless a model carries magnetism, so a non-magnetic
    // project draws exactly the nuclear curves it always did.
    property var magneticSeries: []
    property var visibleMagneticCurves: Globals.BackendWrapper.plottingVisibleSldCurves
    property bool anyModelMagnetic: Globals.BackendWrapper.plottingAnyModelHasMagnetism

    // Which series *should* exist: model, curve, and how many pieces the curve
    // comes in. Making a second model magnetic does not change
    // `anyModelMagnetic`, and a moment going to zero changes only the number of
    // theta_m pieces — neither would rebuild the series without comparing this.
    function magneticSeriesSignature() {
        const models = Globals.BackendWrapper.sampleModels
        const curves = Globals.BackendWrapper.plottingVisibleSldCurves
        let parts = []
        for (let i = 0; i < models.length; i++) {
            if (!Globals.BackendWrapper.plottingModelHasMagnetism(i)) {
                continue
            }
            for (let c = 0; c < curves.length; c++) {
                const pieces = Globals.BackendWrapper.plottingGetMagneticSldSegmentsForModel(i, curves[c]).length
                parts.push(i + ':' + curves[c] + ':' + pieces)
            }
        }
        return parts.join('|')
    }

    property string drawnMagneticSignature: ''

    // Line style per magnetic curve; the model colour carries the identity.
    function magneticCurveStyle(curve) {
        switch (curve) {
        case 'spin_up':   return {dash: Qt.DashLine,    width: 1.5, label: qsTr("ρ↑ (spin-up potential)")}
        case 'spin_down': return {dash: Qt.DashLine,    width: 1.5, label: qsTr("ρ↓ (spin-down potential)")}
        case 'rho_m':     return {dash: Qt.DotLine,     width: 1.5, label: qsTr("ρM (magnetic SLD)")}
        case 'theta_m':   return {dash: Qt.DashDotLine, width: 1.0, label: qsTr("θM (moment angle)")}
        }
        return {dash: Qt.SolidLine, width: 1.0, label: curve}
    }

    // Slight shade variations of the model colour, one per magnetic curve: the
    // hue still says "which model", the shade helps tell the curves apart.
    function magneticCurveColor(curve, baseColor) {
        switch (curve) {
        case 'spin_up':   return Qt.lighter(baseColor, 1.15)
        case 'spin_down': return Qt.darker(baseColor, 1.2)
        case 'rho_m':     return Qt.lighter(baseColor, 1.35)
        case 'theta_m':   return Qt.darker(baseColor, 1.4)
        }
        return baseColor
    }

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

        // Right-hand axis for the moment angle, which shares neither the units
        // nor the range of the SLD curves. Only shown while θM is drawn.
        ValueAxis {
            id: axisThetaM
            titleText: "θM (°)"
            visible: root.visibleMagneticCurves.indexOf('theta_m') !== -1 && root.anyModelMagnetic
            min: Globals.BackendWrapper.plottingSldThetaMinY - 5
            max: Globals.BackendWrapper.plottingSldThetaMaxY + 5
            color: EaStyle.Colors.chartAxis
            // The SLD axis already draws the grid; a second one would clutter.
            gridVisible: false
            labelsColor: EaStyle.Colors.chartLabels
            titleBrush: EaStyle.Colors.chartLabels
        }

        function resetAxes() {
            axisX.min = axisX.minAfterReset
            axisX.max = axisX.maxAfterReset
            axisY.min = axisY.minAfterReset
            axisY.max = axisY.maxAfterReset
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
                ToolTip.text: root.showLegend ?
                                  qsTr("Hide legend") :
                                  qsTr("Show legend")
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
                    model: root.modelCount
                    EaElements.Label {
                        text: '━  SLD ' + Globals.BackendWrapper.sampleModels[index].label
                        color: Globals.BackendWrapper.sampleModels[index].color
                    }
                }

                // One row per drawn magnetic curve; absent for a non-magnetic
                // project, where this Repeater has an empty model.
                Repeater {
                    model: root.magneticSeries.length
                    EaElements.Label {
                        readonly property var entry: root.magneticSeries[index]
                        visible: entry.inLegend
                        height: visible ? implicitHeight : 0
                        text: '┄  ' + root.magneticCurveStyle(entry.curve).label + ' '
                              + (Globals.BackendWrapper.sampleModels[entry.modelIndex]
                                 ? Globals.BackendWrapper.sampleModels[entry.modelIndex].label : '')
                        color: entry.series ? entry.series.color : EaStyle.Colors.chartLabels
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

        // Phase 2: Posterior predictive SLD overlay (Bayesian)
        LineSeries {
            id: ppSldMedianSerie
            name: qsTr("Posterior median SLD")
            axisX: root.chartAxisX
            axisY: root.chartAxisY
            color: "#E67E22"
            width: 2
            visible: Globals.BackendWrapper.bayesianResultAvailable
        }

        AreaSeries {
            id: ppSldBandSerie
            name: qsTr("95% credible interval")
            axisX: root.chartAxisX
            axisY: root.chartAxisY
            color: Qt.rgba(0.902, 0.494, 0.133, 0.25)
            borderWidth: 0
            upperSeries: LineSeries {
                id: ppSldUpperSerie
                axisX: root.chartAxisX
                axisY: root.chartAxisY
                visible: Globals.BackendWrapper.bayesianResultAvailable
            }
            lowerSeries: LineSeries {
                id: ppSldLowerSerie
                axisX: root.chartAxisX
                axisY: root.chartAxisY
                visible: Globals.BackendWrapper.bayesianResultAvailable
            }
            visible: Globals.BackendWrapper.bayesianResultAvailable
        }
    }

    // Create series dynamically when model count changes
    onModelCountChanged: {
        Qt.callLater(recreateAllSeries)
    }

    // A curve was switched on/off, or a layer became (non-)magnetic: the set of
    // series changes, so they are rebuilt rather than just refilled.
    onVisibleMagneticCurvesChanged: Qt.callLater(rebuildAndFitAxis)
    onAnyModelMagneticChanged: Qt.callLater(rebuildAndFitAxis)

    // Adding a curve changes the range bindings, but the live axis keeps the
    // values it was last given — a taller curve would simply be drawn outside
    // it. Rebuild, then grow the axis to cover the new range; a zoom that still
    // contains everything is left alone.
    function rebuildAndFitAxis() {
        recreateAllSeries()
        Qt.callLater(growAxisToVisibleRange)
    }

    function growAxisToVisibleRange() {
        const low = axisY.minAfterReset
        const high = axisY.maxAfterReset
        if (low < axisY.min) {
            axisY.min = low
        }
        if (high > axisY.max) {
            axisY.max = high
        }
    }

    // Refresh all chart series when data changes
    Connections {
        target: Globals.BackendWrapper
        function onSamplePageDataChanged() {
            refreshAllCharts()
        }
        function onMagneticProfileChanged() {
            // A model may have become (non-)magnetic without changing whether
            // *any* model is: then the series set itself has to be rebuilt.
            if (root.magneticSeriesSignature() !== root.drawnMagneticSignature) {
                root.recreateAllSeries()
            } else {
                root.refreshAllCharts()
            }
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
    }

    Timer {
        id: resetAxesTimer
        interval: 75
        repeat: false
        onTriggered: chartView.resetAxes()
    }

    Component.onCompleted: {
        Qt.callLater(recreateAllSeries)
        Qt.callLater(refreshPosteriorPredictiveSldOverlay)
    }

    function recreateAllSeries() {
        // Remove old series
        for (let i = 0; i < sldSeries.length; i++) {
            if (sldSeries[i]) {
                chartView.removeSeries(sldSeries[i])
            }
        }
        sldSeries = []
        clearMagneticSeries()

        // Build into local arrays and assign once: mutating an array held by a
        // `property var` does not notify its bindings, so a push()ed legend row
        // would never appear.
        let newSldSeries = []
        let newMagneticSeries = []

        const models = Globals.BackendWrapper.sampleModels
        for (let k = 0; k < models.length; k++) {
            const line = chartView.createSeries(ChartView.SeriesTypeLine, models[k].label, axisX, axisY)
            line.color = models[k].color
            line.width = 2
            line.useOpenGL = EaGlobals.Vars.useOpenGL
            line.hovered.connect((point, state) => showMainTooltip(point, state))
            newSldSeries.push(line)

            newMagneticSeries = newMagneticSeries.concat(magneticSeriesForModel(k, models[k]))
        }

        sldSeries = newSldSeries
        magneticSeries = newMagneticSeries
        drawnMagneticSignature = magneticSeriesSignature()
        refreshAllCharts()
    }

    function clearMagneticSeries() {
        for (let i = 0; i < magneticSeries.length; i++) {
            if (magneticSeries[i].series) {
                chartView.removeSeries(magneticSeries[i].series)
            }
        }
        magneticSeries = []
    }

    // Magnetic curves of one model. Nothing is created for a non-magnetic
    // model, so the chart of an ordinary sample is unchanged. A curve that comes
    // in several pieces (theta_m exists only where there is a moment) gets one
    // series per piece, so no line is drawn across the gap between two magnetic
    // regions; only the first piece carries a legend row.
    function magneticSeriesForModel(modelIndex, model) {
        let created = []
        if (!Globals.BackendWrapper.plottingModelHasMagnetism(modelIndex)) {
            return created
        }
        const curves = Globals.BackendWrapper.plottingVisibleSldCurves
        for (let c = 0; c < curves.length; c++) {
            const curve = curves[c]
            const style = magneticCurveStyle(curve)
            const yAxis = curve === 'theta_m' ? axisThetaM : axisY
            const segments = Globals.BackendWrapper.plottingGetMagneticSldSegmentsForModel(modelIndex, curve)
            for (let s = 0; s < segments.length; s++) {
                const line = chartView.createSeries(ChartView.SeriesTypeLine,
                                                    model.label + ' ' + curve + ' ' + s,
                                                    axisX, yAxis)
                // Same hue as the model, different dash and shade: colour stays
                // "which model", the pattern and shade say "which curve".
                line.color = magneticCurveColor(curve, model.color)
                line.width = style.width
                line.style = style.dash
                line.useOpenGL = EaGlobals.Vars.useOpenGL
                line.hovered.connect((point, state) => showMainTooltip(point, state))
                created.push({series: line, modelIndex: modelIndex, curve: curve, segment: s, inLegend: s === 0})
            }
        }
        return created
    }

    function refreshAllCharts() {
        const models = Globals.BackendWrapper.sampleModels
        for (let i = 0; i < sldSeries.length && i < models.length; i++) {
            const series = sldSeries[i]
            if (series) {
                series.clear()
                const points = Globals.BackendWrapper.plottingGetSldDataPointsForModel(i)
                for (let p = 0; p < points.length; p++) {
                    series.append(points[p].x, points[p].y)
                }
            }
        }

        for (let m = 0; m < magneticSeries.length; m++) {
            const entry = magneticSeries[m]
            if (!entry.series) {
                continue
            }
            entry.series.clear()
            const magneticPoints = Globals.BackendWrapper.plottingGetMagneticSldSegment(entry.modelIndex,
                                                                                        entry.curve,
                                                                                        entry.segment)
            for (let q = 0; q < magneticPoints.length; q++) {
                entry.series.append(magneticPoints[q].x, magneticPoints[q].y)
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

    function refreshPosteriorPredictiveSldOverlay() {
        ppSldMedianSerie.clear()
        ppSldUpperSerie.clear()
        ppSldLowerSerie.clear()
        const z  = Globals.BackendWrapper.posteriorPredictiveSldZ
        const m  = Globals.BackendWrapper.posteriorPredictiveSldMedian
        const lo = Globals.BackendWrapper.posteriorPredictiveSldLower
        const hi = Globals.BackendWrapper.posteriorPredictiveSldUpper
        if (!z || !m || !lo || !hi) return
        for (let i = 0; i < z.length; ++i) {
            ppSldMedianSerie.append(z[i], m[i])
            ppSldLowerSerie.append(z[i], lo[i])
            ppSldUpperSerie.append(z[i], hi[i])
        }
    }

    Connections {
        target: Globals.BackendWrapper
        function onPosteriorPredictiveSldDataChanged() {
            refreshPosteriorPredictiveSldOverlay()
        }
    }
}
