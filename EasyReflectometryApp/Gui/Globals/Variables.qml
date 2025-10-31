pragma Singleton

import QtQuick


// Initialisation of the reference dictionary. It is filled in later, when the required object is
// created and its unique id is assigned and added here instead of 'null'. After that, any object
// whose id is stored here can be accessed from any other qml file.

QtObject {
    property bool showLegendOnSamplePage: false
    property bool showLegendOnExperimentPage: false
    property bool showLegendOnAnalysisPage: false
    property bool useStaggeredPlotting: false
}
