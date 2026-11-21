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
            if (Globals.BackendWrapper.projectHasCustomContent()) {
                newProjectChoiceDialog.open()
            } else {
                openProjectDescription(false)
            }
        }

        Loader {
            source: '../Popups/ProjectDescription.qml'
        }
    }
    // button 1

    function openProjectDescription(startFromScratch) {
        Globals.References.pages.project.sidebar.basic.popups.projectDescriptionDialog.startFromScratch = startFromScratch
        EaGlobals.Vars.showProjectDescriptionDialog = true
    }

    // A new project would otherwise silently take over whatever the session holds (a sample
    // built before any project existed, or another project's data), so ask first.
    EaElements.Dialog {
        id: newProjectChoiceDialog
        title: qsTr('Create a new project')
        modal: true
        closePolicy: Popup.CloseOnEscape

        Column {
            spacing: EaStyle.Sizes.fontPixelSize

            EaElements.Label {
                width: EaStyle.Sizes.fontPixelSize * 32
                wrapMode: Text.WordWrap
                text: qsTr('This session already contains your own sample model, measured data or fit settings.') + '\n\n' +
                      qsTr('Would you like the new project to start with them, or start from scratch with the default sample and no data?')
            }

            EaElements.Label {
                width: EaStyle.Sizes.fontPixelSize * 32
                wrapMode: Text.WordWrap
                font.italic: true
                text: {
                    if (!Globals.BackendWrapper.projectCreated) {
                        return qsTr('This work has not been saved to a project yet, so starting from scratch discards it.')
                    }
                    const name = Globals.BackendWrapper.projectName
                    if (Globals.BackendWrapper.projectHasUnsavedChanges) {
                        return qsTr('The current project "%1" has unsaved changes.').arg(name)
                    }
                    return qsTr('The current project "%1" has been saved.').arg(name)
                }
            }
        }

        footer: EaElements.DialogButtonBox {
            EaElements.Button {
                text: qsTr('Cancel')
                onClicked: newProjectChoiceDialog.close()
            }

            EaElements.Button {
                text: qsTr('Start from scratch')
                onClicked: {
                    newProjectChoiceDialog.close()
                    openProjectDescription(true)
                }
            }

            EaElements.Button {
                text: qsTr('Keep sample and data')
                onClicked: {
                    newProjectChoiceDialog.close()
                    openProjectDescription(false)
                }
            }
        }
    }
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

    // Error dialog for project load issues (e.g. outdated project file_format)
    EaElements.Dialog {
        id: projectLoadErrorDialog
        title: qsTr('Project Load Error')
        standardButtons: Dialog.Ok
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        property string errorMessage: ''

        EaElements.Label {
            text: projectLoadErrorDialog.errorMessage
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
        }
    }

    Connections {
        target: Globals.BackendWrapper
        function onProjectLoadError(message) {
            projectLoadErrorDialog.title = qsTr('Project Load Error')
            projectLoadErrorDialog.errorMessage = message
            projectLoadErrorDialog.open()
        }
        // The project loaded, but something could not be restored as saved.
        function onProjectLoadWarning(message) {
            projectLoadErrorDialog.title = qsTr('Project Loaded with Warnings')
            projectLoadErrorDialog.errorMessage = message
            projectLoadErrorDialog.open()
        }
    }

}
