import QtQuick

import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

// Table cell choosing the model an experiment is fitted with. Shows the stored
// pairing (blank when the experiment has none) and changes only that experiment.
EaComponents.TableViewComboBox {
    // The experiment's row in the experiment tables
    required property int row

    horizontalAlignment: Text.AlignLeft
    model: Globals.BackendWrapper.sampleModelNames
    currentIndex: Globals.BackendWrapper.analysisExperimentsModelIndices[row] ?? -1
    onActivated: {
        Globals.BackendWrapper.analysisSetModelOnExperiment(row, currentIndex)
        // Choosing an entry replaces the binding; restore it so the combo keeps
        // showing the stored pairing.
        currentIndex = Qt.binding(() => Globals.BackendWrapper.analysisExperimentsModelIndices[row] ?? -1)
    }
}
