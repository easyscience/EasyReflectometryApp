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
    EaCharts.QtCharts1dMeasVsCalc {
        id: chartView

        property alias calculated: chartView.calcSerie
        property alias measured: chartView.measSerie
        bkgSerie.color: measSerie.color
        measSerie.width: 1
        bkgSerie.width: 1

        anchors.topMargin: EaStyle.Sizes.toolButtonHeight - EaStyle.Sizes.fontPixelSize - 1

        useOpenGL: EaGlobals.Vars.useOpenGL

        // Multi-experiment support
        property var multiExperimentSeries: []
        property bool isMultiExperimentMode: {
            try {
                return Globals.BackendWrapper.plottingIsMultiExperimentMode || false
            } catch (e) {
                return false
            }
        }

        // Watch for changes in multi-experiment mode property
        onIsMultiExperimentModeChanged: {
            console.log("Analysis: isMultiExperimentMode changed to: " + isMultiExperimentMode)
            updateMultiExperimentSeries()
        }

        // Watch for changes in multi-experiment selection
        Connections {
            target: Globals.BackendWrapper.activeBackend
            function onMultiExperimentSelectionChanged() {
                console.log("Analysis: Multi-experiment selection changed - updating series")
                chartView.updateMultiExperimentSeries()
            }
        }
        
        property double xRange: Globals.BackendWrapper.plottingAnalysisMaxX - Globals.BackendWrapper.plottingAnalysisMinX
        axisX.title: "q (Å⁻¹)"
        axisX.min: Globals.BackendWrapper.plottingAnalysisMinX - xRange * 0.01
        axisX.max: Globals.BackendWrapper.plottingAnalysisMaxX + xRange * 0.01
        axisX.minAfterReset: Globals.BackendWrapper.plottingAnalysisMinX - xRange * 0.01
        axisX.maxAfterReset: Globals.BackendWrapper.plottingAnalysisMaxX + xRange * 0.01

        property double yRange: Globals.BackendWrapper.plottingAnalysisMaxY - Globals.BackendWrapper.plottingAnalysisMinY
        axisY.title: "Log10 R(q)"
        axisY.min: Globals.BackendWrapper.plottingAnalysisMinY - yRange * 0.01
        axisY.max: Globals.BackendWrapper.plottingAnalysisMaxY + yRange * 0.01
        axisY.minAfterReset: Globals.BackendWrapper.plottingAnalysisMinY - yRange * 0.01
        axisY.maxAfterReset: Globals.BackendWrapper.plottingAnalysisMaxY + yRange * 0.01

        calcSerie.onHovered: (point, state) => showMainTooltip(chartView, point, state)
        calcSerie.color: {
            const models = Globals.BackendWrapper.sampleModels
            const idx = Globals.BackendWrapper.sampleCurrentModelIndex

            if (models && idx >= 0 && idx < models.length) {
                return models[idx].color
            }

            return undefined
        }

        // Multi-experiment series management
        function updateMultiExperimentSeries() {
            console.log("Analysis: updateMultiExperimentSeries called, isMultiExperimentMode=" + isMultiExperimentMode)

            // Clear existing multi-experiment series
            clearMultiExperimentSeries()

            if (!isMultiExperimentMode) {
                // Show default series for single experiment
                console.log("Analysis: Single experiment mode - showing default series")
                measured.visible = true
                calculated.visible = true
                return
            }

            // Get experiment data list
            var experimentDataList = Globals.BackendWrapper.plottingIndividualExperimentDataList
            console.log("Analysis: experimentDataList length=" + experimentDataList.length)

            // If no data available yet, keep default series visible as fallback
            if (experimentDataList.length === 0) {
                console.log("Analysis: No experiment data available - keeping default series visible")
                measured.visible = true
                calculated.visible = true
                return
            }

            // Hide default series in multi-experiment mode (only after we have data)
            measured.visible = false
            calculated.visible = false
            console.log("Analysis: Hidden default series, creating " + experimentDataList.length + " experiment series")

            // Create series for each experiment
            for (var i = 0; i < experimentDataList.length; i++) {
                var expData = experimentDataList[i]
                console.log("Analysis: Creating series for experiment " + expData.index + " (" + expData.name + ") with color " + expData.color)
                if (expData.hasData) {
                    createExperimentSeries(expData.index, expData.name, expData.color)
                }
            }
        }

        function clearMultiExperimentSeries() {
            // Remove all dynamically created series
            for (var i = 0; i < multiExperimentSeries.length; i++) {
                var seriesSet = multiExperimentSeries[i]
                if (seriesSet.measuredSerie) {
                    chartView.removeSeries(seriesSet.measuredSerie)
                }
                if (seriesSet.calculatedSerie) {
                    chartView.removeSeries(seriesSet.calculatedSerie)
                }
            }
            multiExperimentSeries = []
        }

        function createExperimentSeries(expIndex, expName, color) {
            // Create measured data series
            var measuredSerie = chartView.createSeries(ChartView.SeriesTypeLine, 
                                                     `${expName} - Measured`, 
                                                     chartView.axisX, chartView.axisY)
            measuredSerie.color = color
            measuredSerie.width = 1
            measuredSerie.capStyle = Qt.RoundCap
            measuredSerie.useOpenGL = chartView.useOpenGL

            // Create calculated data series (slightly different style)
            var calculatedSerie = chartView.createSeries(ChartView.SeriesTypeLine,
                                                        `${expName} - Calculated`,
                                                        chartView.axisX, chartView.axisY)
            calculatedSerie.color = color
            calculatedSerie.width = 2
            calculatedSerie.capStyle = Qt.RoundCap
            calculatedSerie.useOpenGL = chartView.useOpenGL

            // Store references
            var seriesSet = {
                measuredSerie: measuredSerie,
                calculatedSerie: calculatedSerie,
                expIndex: expIndex,
                expName: expName,
                color: color
            }
            multiExperimentSeries.push(seriesSet)

            // Populate with data
            populateExperimentSeries(seriesSet)
        }

        function populateExperimentSeries(seriesSet) {
            // Get data points from backend (includes both measured and calculated)
            var dataPoints = Globals.BackendWrapper.plottingGetAnalysisDataPoints(seriesSet.expIndex)
            console.log("Analysis: populateExperimentSeries for exp " + seriesSet.expIndex + " got " + dataPoints.length + " points")

            // Clear existing points
            seriesSet.measuredSerie.clear()
            seriesSet.calculatedSerie.clear()

            // Add data points
            for (var i = 0; i < dataPoints.length; i++) {
                var point = dataPoints[i]
                seriesSet.measuredSerie.append(point.x, point.measured)
                seriesSet.calculatedSerie.append(point.x, point.calculated)
            }

            console.log("Analysis: Added " + dataPoints.length + " points to series for " + seriesSet.expName)
        }

        // Tool buttons
        Row {
            id: toolButtons

            x: chartView.plotArea.x + chartView.plotArea.width - width
            y: chartView.plotArea.y - height - EaStyle.Sizes.fontPixelSize

            spacing: 0.25 * EaStyle.Sizes.fontPixelSize

            EaElements.TabButton {
                checked: Globals.Variables.showLegendOnAnalysisPage
                autoExclusive: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "align-left"
                ToolTip.text: Globals.Variables.showLegendOnAnalysisPage ?
                                  qsTr("Hide legend") :
                                  qsTr("Show legend")
                onClicked: Globals.Variables.showLegendOnAnalysisPage = checked
            }

            EaElements.TabButton {
                checked: chartView.allowHover
                autoExclusive: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "comment-alt"
                ToolTip.text: qsTr("Show coordinates tooltip on hover")
                onClicked: chartView.allowHover = !chartView.allowHover
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
                onClicked: chartView.allowZoom = !chartView.allowZoom
            }

            EaElements.TabButton {
                checked: chartView.allowZoom
                autoExclusive: false
                height: EaStyle.Sizes.toolButtonHeight
                width: EaStyle.Sizes.toolButtonHeight
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "expand"
                ToolTip.text: qsTr("Enable box zoom")
                onClicked: chartView.allowZoom = !chartView.allowZoom
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
        // Tool buttons

        // Legend
        Rectangle {
            visible: Globals.Variables.showLegendOnAnalysisPage

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

                // Single experiment legend
                EaElements.Label {
                    visible: !chartView.isMultiExperimentMode
                    text: '━  I (Measured)'
                    color: chartView.measSerie.color
                }
                EaElements.Label {
                    visible: !chartView.isMultiExperimentMode
                    text: '━ (Calculated)'
                    color: chartView.calcSerie.color
                }

                // Multi-experiment legend
                Column {
                    visible: chartView.isMultiExperimentMode
                    spacing: EaStyle.Sizes.fontPixelSize * 0.2

                    EaElements.Label {
                        text: qsTr("Multi-experiment view:")
                        font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                        font.bold: true
                        color: EaStyle.Colors.themeForeground
                    }

                    Repeater {
                        model: chartView.isMultiExperimentMode ? Globals.BackendWrapper.plottingIndividualExperimentDataList : []
                        delegate: Row {
                            spacing: EaStyle.Sizes.fontPixelSize * 0.3

                            Rectangle {
                                width: EaStyle.Sizes.fontPixelSize * 0.8
                                height: 3
                                color: modelData.color || "#1f77b4"
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

                    Rectangle {
                        width: parent.width - 2 * EaStyle.Sizes.fontPixelSize
                        height: 1
                        color: EaStyle.Colors.chartGridLine
                    }

                    EaElements.Label {
                        text: qsTr("━ Measured (thin)")
                        font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.7
                        color: EaStyle.Colors.themeForegroundMinor
                    }
                    EaElements.Label {
                        text: qsTr("━ Calculated (thick)")
                        font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.7
                        color: EaStyle.Colors.themeForegroundMinor
                    }
                }
            }
        }
        // Legend

        EaElements.ToolTip {
            id: dataToolTip

            arrowLength: 0
            textFormat: Text.RichText
        }

        // Data is set in python backend (plotting_1d.py)
        Component.onCompleted: {
            Globals.References.pages.analysis.mainContent.analysisView = chartView
            Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage',
                                                               'measuredSerie',
                                                               measured)
            Globals.BackendWrapper.plottingSetQtChartsSerieRef('analysisPage',
                                                               'calculatedSerie',
                                                               calculated)

            // Initialize multi-experiment support
            updateMultiExperimentSeries()
        }

        // Update series when chart becomes visible
        onVisibleChanged: {
            if (visible && isMultiExperimentMode) {
                updateMultiExperimentSeries()
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
