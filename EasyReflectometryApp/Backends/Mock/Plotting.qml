pragma Singleton

import QtQuick

QtObject {

    property double sampleMinX: -1.
    property double sampleMaxX: 1.
    property double sampleMinY: -10.
    property double sampleMaxY: 10.
    property double sldMinX: -2.
    property double sldMaxX: 2.
    property double sldMinY: -20.
    property double sldMaxY: 20.
    property double experimentMinX: -3.
    property double experimentMaxX: 3.
    property double experimentMinY: -30.
    property double experimentMaxY: 30.
    property double analysisMinX: -4.
    property double analysisMaxX: 4.
    property double analysisMinY: -40.
    property double analysisMaxY: 40.

    property double residualMinX: 0.01
    property double residualMaxX: 0.30
    property double residualMinY: -0.1
    property double residualMaxY: 0.1

    property int modelCount: 1

    // Plot mode properties
    property bool plotRQ4: false
    property string yMainAxisTitle: 'R(q)'
    property bool xAxisLog: false
    property string xAxisType: 'linear'
    property bool sldXDataReversed: false
    property bool scaleShown: false
    property bool bkgShown: false

    // Signals for plot mode changes
    signal plotModeChanged()
    signal axisTypeChanged()
    signal sldAxisReversedChanged()
    signal referenceLineVisibilityChanged()
    signal samplePageDataChanged()
    signal samplePageResetAxes()

    function setQtChartsSerieRef(value1, value2, value3) {
        console.debug(`setQtChartsSerieRef ${value1}, ${value2}, ${value3}`)
    }

    function drawCalculatedOnSampleChart(){
        console.debug(`drawCalculatedOnSampleChart`)
    }

    function drawCalculatedOnSldChart(){
        console.debug(`drawCalculatedOnSldChart`)
    }

    function getSampleDataPointsForModel(index) {
        console.debug(`getSampleDataPointsForModel ${index}`)
        return []
    }

    function getSldDataPointsForModel(index) {
        console.debug(`getSldDataPointsForModel ${index}`)
        return []
    }

    function getModelColor(index) {
        console.debug(`getModelColor ${index}`)
        return '#0000FF'
    }

    // Plot mode toggle functions
    function togglePlotRQ4() {
        plotRQ4 = !plotRQ4
        yMainAxisTitle = plotRQ4 ? 'R(q)×q⁴' : 'R(q)'
        plotModeChanged()
    }

    function toggleXAxisType() {
        xAxisLog = !xAxisLog
        xAxisType = xAxisLog ? 'log' : 'linear'
        axisTypeChanged()
    }

    function reverseSldXData() {
        sldXDataReversed = !sldXDataReversed
        sldAxisReversedChanged()
    }

    function flipScaleShown() {
        scaleShown = !scaleShown
        referenceLineVisibilityChanged()
    }

    function flipBkgShown() {
        bkgShown = !bkgShown
        referenceLineVisibilityChanged()
    }

    // Reference line data accessors (mock implementation)
    function getBackgroundData() {
        if (!bkgShown) return []
        // Return mock horizontal line at background level
        return [
            { 'x': 0.01, 'y': -7.0 },
            { 'x': 0.30, 'y': -7.0 }
        ]
    }

    function getScaleData() {
        if (!scaleShown) return []
        // Return mock horizontal line at scale level (log10(1.0) = 0)
        return [
            { 'x': 0.01, 'y': 0.0 },
            { 'x': 0.30, 'y': 0.0 }
        ]
    }

    // Analysis-specific reference line data accessors (use sample/calculated x-range)
    function getBackgroundDataForAnalysis() {
        if (!bkgShown) return []
        // Return mock horizontal line at background level using sample x-range
        return [
            { 'x': sampleMinX, 'y': -7.0 },
            { 'x': sampleMaxX, 'y': -7.0 }
        ]
    }

    function getScaleDataForAnalysis() {
        if (!scaleShown) return []
        // Return mock horizontal line at scale level using sample x-range
        return [
            { 'x': sampleMinX, 'y': 0.0 },
            { 'x': sampleMaxX, 'y': 0.0 }
        ]
    }

    function getResidualDataPoints(index) {
        console.debug(`getResidualDataPoints ${index}`)
        return [
            { 'x': 0.01, 'y':  0.002 },
            { 'x': 0.15, 'y': -0.001 },
            { 'x': 0.30, 'y':  0.003 }
        ]
    }

}
