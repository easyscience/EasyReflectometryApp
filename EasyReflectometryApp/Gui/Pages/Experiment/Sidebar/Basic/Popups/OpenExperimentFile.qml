import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals


FileDialog{

    id: openExperimentFileDialog

    fileMode: FileDialog.OpenFiles
    nameFilters: [ 'Experiment files (*.dat *.txt *.ort)']

    onAccepted: {
        Globals.BackendWrapper.experimentLoad(selectedFiles)
    }

    Component.onCompleted: {
        Globals.References.pages.experiment.sidebar.basic.popups.loadExperimentFileDialog = openExperimentFileDialog
    }
}
