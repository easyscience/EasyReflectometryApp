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

    property int modelCount: 1

    signal samplePageDataChanged()

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

}
