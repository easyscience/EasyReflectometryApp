pragma Singleton

import QtQuick

QtObject {
    property bool experimentalData: true
    property double scaling: 1.
    property double background: 2.
    property string resolution: '3.00'
    property var resolutionTypes: ['PercentageFwhm', 'LinearSpline', 'Pointwise']
    property int resolutionTypeCurrentIndex: 0
    property string resolutionType: resolutionTypes[resolutionTypeCurrentIndex]

    // Setters
    function setScaling(value) {
        console.debug(`setScaling ${value}`)
    }
    function setBackground(value) {
        console.debug(`setBackgroun ${value}`)
    }
    function setResolution(value) {
        console.debug(`setResolution ${value}`)
    }
    function setResolutionType(value) {
        resolutionTypeCurrentIndex = value
        resolutionType = resolutionTypes[value]
        console.debug(`setResolutionType ${value}`)
    }

    function load(path) {
        console.debug(`Loading experiment from ${path}`)
    }
}
