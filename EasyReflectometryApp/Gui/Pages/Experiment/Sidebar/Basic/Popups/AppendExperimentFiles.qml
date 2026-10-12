import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals


// More measured curves of the selected experiment's contrast (other angles or
// wavelength bands): their points are merged into it, each keeping its own resolution.
FileDialog{

    id: appendExperimentFilesDialog

    title: qsTr("Add file(s) to the selected experiment")
    fileMode: FileDialog.OpenFiles
    nameFilters: [ 'Experiment files (*.dat *.txt *.ort)']

    onAccepted: {
        Globals.BackendWrapper.experimentAppendToCurrent(selectedFiles)
    }

    Component.onCompleted: {
        Globals.References.pages.experiment.sidebar.basic.popups.appendExperimentFilesDialog = appendExperimentFilesDialog
    }
}
