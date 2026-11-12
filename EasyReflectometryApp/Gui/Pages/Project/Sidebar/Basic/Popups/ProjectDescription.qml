import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Components as EaComponents

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

    Component.onCompleted: {
        Globals.References.pages.project.sidebar.basic.popups.projectDescriptionDialog = projectDescriptionDialog

        projectName = Globals.BackendWrapper.projectName
        projectDescription = Globals.BackendWrapper.projectDescription
        projectLocation = Globals.BackendWrapper.projectLocation
    }

}
