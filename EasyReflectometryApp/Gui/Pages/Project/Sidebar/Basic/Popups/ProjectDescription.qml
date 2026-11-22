import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Components as EaComponents
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


EaComponents.ProjectDescriptionDialog {

    id: projectDescriptionDialog

    visible: EaGlobals.Vars.showProjectDescriptionDialog
    onClosed: {
        EaGlobals.Vars.showProjectDescriptionDialog = false
        // Needed because the location path is being formatted by the backend
        projectLocation = Globals.BackendWrapper.projectLocation
    }

    // Chosen in "Create a new project" when the session already holds work. The reset waits for
    // OK here, so cancelling this dialog leaves the current work alone.
    property bool startFromScratch: false

    onAccepted: {
        if (startFromScratch) {
            Globals.References.applicationWindow.resetToInitialState()
        }
        Globals.BackendWrapper.projectSetName(projectName)
        Globals.BackendWrapper.projectSetDescription(projectDescription)
        Globals.BackendWrapper.projectSetLocation(projectLocation)

        Globals.BackendWrapper.projectCreate()
        Globals.References.resetActive = true
        Globals.References.applicationWindow.appBarCentralTabs.sampleButton.enabled = true
    }

    // Cancel, as in the app's other confirmations (Reset state). EasyApp 0.9.1's dialog has OK
    // only; the next EasyApp release has this same footer, so drop it here once that is required.
    // OK calls accept(), not close(): EasyApp's own onAccepted takes the location from its field.
    // No standard buttons: Qt would add EasyApp's OK to this button box as well.
    standardButtons: Dialog.NoButton
    footer: EaElements.DialogButtonBox {
        EaElements.Button {
            text: qsTr("Cancel")
            onClicked: projectDescriptionDialog.reject()
        }

        EaElements.Button {
            text: qsTr("OK")
            onClicked: projectDescriptionDialog.accept()
        }
    }

    // Nothing is created: drop what was typed, so the next opening shows the project as it is.
    onRejected: loadFromBackend()
    // A load since the last opening (a project or an example) brings its own name and description.
    onAboutToShow: loadFromBackend()

    Component.onCompleted: {
        Globals.References.pages.project.sidebar.basic.popups.projectDescriptionDialog = projectDescriptionDialog
        loadFromBackend()
    }

    function loadFromBackend() {
        projectName = Globals.BackendWrapper.projectName
        projectDescription = Globals.BackendWrapper.projectDescription
        projectLocation = Globals.BackendWrapper.projectLocation
    }

}
