pragma Singleton

import QtQuick


// Initialisation of the reference dictionary. It is filled in later, when the required object is
// created and its unique id is assigned and added here instead of 'null'. After that, any object
// whose id is stored here can be accessed from any other qml file.

QtObject {
    property bool showLegendOnSamplePage: false
    property bool showLegendOnExperimentPage: false
    property bool showLegendOnAnalysisPage: false
    property bool showLegendOnAnalysisResidualsTab: false
    property bool useStaggeredPlotting: false
    property double staggeringFactor: 0.5

    // Sample page plot control settings
    property bool reverseSldZAxis: false
    property bool logarithmicQAxis: false
    property int experimentMarkerStyle: 0  // 0: dots, 1: circles, 2: line

    // Shared experiment color palette — used by Data Explorer table, Experiment chart, and Analysis charts
    // Muted/pastel palette to match the application's professional aesthetic
    readonly property var experimentColorPalette: [
        '#7BA6C4', '#E8B889', '#8DBF8D', '#D48787', '#B296B8',
        '#A68F7F', '#D4A8BC', '#A5A5A5', '#B8B87D', '#7BB8B8'
    ]
    function experimentColor(index) {
        return experimentColorPalette[index % experimentColorPalette.length]
    }

    function lineStyleSymbol(style) {
        switch (style) {
        case Qt.DotLine:        return '\u22c5 \u22c5 \u22c5'
        case Qt.DashLine:       return '\u2504\u2504'
        case Qt.DashDotLine:    return '\u2504\u22c5\u2504'
        case Qt.DashDotDotLine: return '\u2504\u22c5\u22c5\u2504'
        default:                return '\u2501'
        }
    }
}
