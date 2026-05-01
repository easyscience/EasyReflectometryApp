import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents
import EasyApplication.Gui.Logic as EaLogic

import Gui.Globals as Globals


Grid {

    columns: 2
    spacing: EaStyle.Sizes.fontPixelSize

    // button 1
    EaElements.SideBarButton {
        fontIcon: 'plus-circle'
        text: qsTr('Create a new project')

        onClicked: {
            console.debug(`Clicking '${text}' button ::: ${this}`)
            EaGlobals.Vars.showProjectDescriptionDialog = true
        }

        Loader {
            source: '../Popups/ProjectDescription.qml'
        }
    }
    // button 1
/*
    // button 2
    EaElements.SideBarButton {
        fontIcon: "arrow-circle-right"
        text: qsTr("Continue without a project")

        onClicked: {
            Globals.References.samplePageEnabled = true
            Globals.References.sampleTabButton.toggle()
        }
        Component.onCompleted: {
            Globals.References.continueWithoutProjectButton = this
            Globals.Constants.proxy.undoredo.resetUndoRedoStack()
        }
    }
    // button 2
*/
    // button 3
    EaElements.SideBarButton {
        fontIcon: 'upload'
        text: qsTr('Open an existing project')

        onClicked: {
            console.debug(`Clicking '${text}' button ::: ${this}`)
            Globals.References.pages.project.sidebar.basic.popups.openJsonFileDialog.open()
        }

        Loader {
            source: '../Popups/OpenJsonFile.qml'
        }
    }
    // button 3

}
