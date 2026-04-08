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

    // Shared experiment color palette — used by Data Explorer table, Experiment chart, and Analysis charts
    readonly property var experimentColorPalette: [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
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
