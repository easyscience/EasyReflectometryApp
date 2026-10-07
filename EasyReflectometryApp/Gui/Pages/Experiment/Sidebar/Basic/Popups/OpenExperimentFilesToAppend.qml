import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Components as EaComponents
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


// Adds more measured curves of the same contrast to the current experiment:
// one file per curve, merged into the experiment with each point keeping the
// resolution it was measured with.
FileDialog {

    id: appendExperimentFilesDialog

    fileMode: FileDialog.OpenFiles
    nameFilters: [ 'Experiment files (*.dat *.txt *.ort)']

    onAccepted: {
        const error = Globals.BackendWrapper.experimentAppendToCurrent(selectedFiles)
        if (error) {
            appendErrorDialog.message = error
            appendErrorDialog.open()
        }
    }

    Component.onCompleted: {
        Globals.References.pages.experiment.sidebar.basic.popups.appendExperimentFilesDialog = appendExperimentFilesDialog
    }

    // The backend refuses a polarized experiment and multi-dataset files;
    // say why instead of silently doing nothing.
    EaElements.Dialog {
        id: appendErrorDialog

        property string message: ''

        title: qsTr("Could not add the curve(s)")
        standardButtons: Dialog.Ok
        closePolicy: Popup.CloseOnEscape

        EaElements.Label {
            width: parent.width
            wrapMode: Text.WordWrap
            text: appendErrorDialog.message
        }
    }
}
