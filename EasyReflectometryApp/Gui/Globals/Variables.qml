pragma Singleton

import QtQuick


// Initialisation of the reference dictionary. It is filled in later, when the required object is
// created and its unique id is assigned and added here instead of 'null'. After that, any object
// whose id is stored here can be accessed from any other qml file.

QtObject {
    // Hover delay (ms) before a tooltip appears, so it doesn't pop up over the
    // control the moment the cursor crosses it. Matches Qt's desktop default
    // (QStyleHints::toolTipWakeUpDelay). Chart data readouts stay instant.
    readonly property int toolTipDelay: 700

    // Legends start shown on the reflectivity plots (and the SLD/spin asymmetry charts that share
    // their toggle): with several contrasts on one plot the curves cannot be told apart without
    // one (#400). The chart toolbar still switches them off.
    property bool showLegendOnSamplePage: true
    property bool showLegendOnExperimentPage: true
    property bool showLegendOnAnalysisPage: true
    property bool showLegendOnAnalysisResidualsTab: false
    property bool useStaggeredPlotting: false
    property double staggeringFactor: 0.5
    // Analysis chart: each further shown experiment is drawn this many decades lower
    property bool staggerAnalysis: false
    property double analysisStaggerDecades: 1.0

    // Sample page plot control settings
    // Draw every model, or only the one picked in the Models selector
    property bool showAllSampleModels: true
    property bool reverseSldZAxis: false
    property bool logarithmicQAxis: false
    property int experimentMarkerStyle: 0  // 0: dots, 1: circles, 2: line
    // Factor on the measured-data marker size (line width for the line style)
    property double experimentMarkerSize: 1.0

    // SLD chart z range, shared by the Sample and Analysis SLD charts.
    // Auto: fit the calculated profiles. Otherwise [sldZMin, sldZMax]; NaN until
    // first set (seeded from the auto range when Auto is switched off).
    property bool sldZAuto: true
    property real sldZMin: NaN
    property real sldZMax: NaN

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

    // Legend symbol for the measured-data series, matching experimentMarkerStyle
    function markerStyleSymbol(markerStyle) {
        switch (markerStyle) {
        case 0:  return '\u2022'   // dots: small bullet
        case 1:  return '\u25cf'   // circles: large filled circle
        default: return '\u2501'   // line
        }
    }
}
