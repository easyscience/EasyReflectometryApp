import QtQuick
import QtQuick.Controls
import QtCore

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui as Gui
import Gui.Globals as Globals

EaComponents.ApplicationWindow {

    // Timer for Creating delay
    Timer {
        id: timer
    }
    function delay(delayTime, cb) {
        timer.interval = delayTime;
        timer.repeat = false;
        timer.triggered.connect(cb);
        timer.start();
    }
    id: applicationWindow
    ///////////////////
    // APPLICATION BAR
    ///////////////////

    // Left group of application bar tool buttons
    appBarLeftButtons: [

        EaElements.ToolButton {
            id: saveButton
            // Disabled when the project is already on disk unchanged, so that an enabled button
            // is itself the signal that there is something to save. Saving also serializes the
            // same model state the fitter thread is writing to, so it is blocked during a fit
            // rather than silently storing half-updated parameters. The success flash keeps the
            // enabled style, otherwise the check mark is drawn greyed out because the save that
            // triggered it has just disabled the button.
            enabled: applicationWindow.canSaveProject || saveFlashTimer.running
            highlighted: true
            fontIcon: saveFlashTimer.running ? "check-circle" : "save"
            ToolTip.text: {
                if (saveFlashTimer.running) {
                    return qsTr("Project saved")
                }
                if (Globals.BackendWrapper.analysisFittingRunning) {
                    return qsTr("Saving is disabled while a fit is running")
                }
                if (Globals.BackendWrapper.projectCreated && !Globals.BackendWrapper.projectHasUnsavedChanges) {
                    return qsTr("No changes to save")
                }
                return qsTr("Save current state of the project")
            }
            onClicked: {
                if (applicationWindow.canSaveProject) {
                    Globals.BackendWrapper.projectSave()
                }
            }

            // Success feedback in place, where the user just clicked. A save during the flash
            // restarts it rather than cutting it short.
            Timer {
                id: saveFlashTimer
                interval: 2000
                repeat: false
            }
        },

        EaElements.ToolButton {
            enabled: Globals.References.resetActive
            fontIcon: "undo"
            ToolTip.text: qsTr("Reset to initial state without project, models and data")
            onClicked: resetStateDialog.open()
        }
    ]

    // Right group of application bar tool buttons
    appBarRightButtons: [

        EaElements.ToolButton {
            fontIcon: "cog"
            ToolTip.text: qsTr("Application preferences")
            onClicked: EaGlobals.Vars.showAppPreferencesDialog = true
        },
        EaElements.ToolButton {
            fontIcon: 'question-circle'
            ToolTip.text: qsTr('Get online help')
            onClicked: Qt.openUrlExternally(Globals.ApplicationInfo.about.docsUrl)
        },

        EaElements.ToolButton {
            fontIcon: 'bug'
            ToolTip.text: qsTr('Report a bug or issue')
            onClicked: Qt.openUrlExternally(Globals.ApplicationInfo.about.issuesUrl)
        }

    ]

    // Central group of application bar page buttons (workflow tabs)
    // Page buttons for the pages described below
    appBarCentralTabs.contentData: [

        // Home page
        EaElements.AppBarTabButton {
            id: homeButton
            fontIcon: "home"
            text: qsTr("Home")
            ToolTip.text: qsTr("Home")
            Component.onCompleted: {
                Globals.References.applicationWindow.appBarCentralTabs.homeButton = homeButton
            }
        },

        // Project page
        EaElements.AppBarTabButton {
            id: projectButton
            enabled: false
            fontIcon: "archive"
            text: qsTr("Project")
            ToolTip.text: qsTr("Project description page")
            Component.onCompleted: {
                Globals.References.applicationWindow.appBarCentralTabs.projectButton = projectButton
            }
        },

        // Sample page
        EaElements.AppBarTabButton {
            id: sampleButton
            enabled: false
            fontIcon: "layer-group"
            text: qsTr("Sample")
            ToolTip.text: qsTr("Sample description page")
            Component.onCompleted: {
                Globals.References.applicationWindow.appBarCentralTabs.sampleButton = sampleButton
            }
        },

        // Experiment tab
        EaElements.AppBarTabButton {
            id: experimentTabButton
            enabled: false
            fontIcon: "microscope"
            text: qsTr("Experiment")
            ToolTip.text: qsTr("Experimental settings and data page")
            Component.onCompleted:Globals.References.applicationWindow.appBarCentralTabs.experimentButton = experimentTabButton
        },


        // Analysis tab
        EaElements.AppBarTabButton {
            id: analysisTabButton
            enabled: false
            fontIcon: "calculator"
            text: qsTr("Analysis")
            ToolTip.text: qsTr("Simulation and fitting page")
            Component.onCompleted: Globals.References.applicationWindow.appBarCentralTabs.analysisButton = analysisTabButton
        },

        // Summary page
        EaElements.AppBarTabButton {
            id: summaryButton
            enabled: false
            fontIcon: "clipboard-list"
            text: qsTr("Summary")
            ToolTip.text: qsTr("Summary of the work done")
            Component.onCompleted: {
                Globals.References.applicationWindow.appBarCentralTabs.summaryButton = summaryButton
            }
        }
    ]

    //////////////////////////////////
    // APP PAGES (MAIN AREA + SIDEBAR)
    //////////////////////////////////

    // Pages for the tab buttons described above
    contentArea: [
        Loader { source: 'Pages/Home/Layout.qml' },
        Loader { source: 'Pages/Project/Layout.qml' },
        Loader { source: 'Pages/Sample/Layout.qml' },
        Loader { source: 'Pages/Experiment/Layout.qml' },
        Loader { source: 'Pages/Analysis/Layout.qml' },
        Loader { source: 'Pages/Summary/Layout.qml' }
    ]

    /////////////
    // STATUS BAR
    /////////////

    statusBar: Gui.StatusBar {}

    ///////
    // MISC
    ///////

    // Whether there is a project on disk that differs from what is in memory and can be written
    // right now. Shared by the Save button, the Ctrl+S shortcut and the close prompt.
    readonly property bool canSaveProject: Globals.BackendWrapper.projectCreated
                                           && Globals.BackendWrapper.projectHasUnsavedChanges
                                           && !Globals.BackendWrapper.analysisFittingRunning

    // Closing with unsaved work asks first. Qt5 had this (Components/CloseDialog.qml); the Qt6
    // migration replaced it with `onClosing: Qt.quit()`, which exited unconditionally without
    // asking. This restores the prompt, with the Cancel button the Qt5 dialog was missing.
    //
    // The prompt is gated on a created project as well as on the flag: before a create there is
    // nothing on disk that the edits could be "unsaved" relative to, and "Save and exit" would
    // otherwise write the defaults over whatever project sits at the chosen path.
    onClosing: function(close) {
        if (Globals.BackendWrapper.projectCreated
                && Globals.BackendWrapper.projectHasUnsavedChanges
                && !applicationWindow.discardChangesOnClose) {
            close.accepted = false
            closeDialog.open()
        }
    }

    // Set by "Exit without saving" (and test mode) before the window is closed. In Qt 6,
    // Qt.quit() does not stop the event loop directly: it asks every top-level window to close
    // first, which runs onClosing again, so a handler that rejects the close while the project
    // is dirty would swallow the quit and reopen the prompt forever. Recording the decision here
    // lets onClosing honour it.
    property bool discardChangesOnClose: false

    // Set while the close dialog's "Save and exit" is in flight. Unlike Qt5, which quit
    // unconditionally, the app only exits once the save has actually reported success — a failed
    // save leaves the window open with its error dialog rather than discarding the work.
    property bool quitAfterSave: false

    EaElements.Dialog {
        id: closeDialog
        title: qsTr('Unsaved Changes')
        // Modal, so the user cannot keep editing, start a fit or hit the window's close button
        // again behind the question. (EaElements.Dialog is modeless by default.)
        modal: true
        closePolicy: Popup.CloseOnEscape

        EaElements.Label {
            text: qsTr('The project has unsaved changes.\nDo you want to save them before exiting?')
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
        }

        footer: EaElements.DialogButtonBox {
            EaElements.Button {
                text: qsTr('Cancel')
                onClicked: closeDialog.close()
            }

            EaElements.Button {
                text: qsTr('Exit without saving')
                onClicked: {
                    closeDialog.close()
                    applicationWindow.discardChangesOnClose = true
                    applicationWindow.close()
                }
            }

            EaElements.Button {
                text: qsTr('Save and exit')
                enabled: applicationWindow.canSaveProject
                onClicked: {
                    closeDialog.close()
                    applicationWindow.quitAfterSave = true
                    Globals.BackendWrapper.projectSave()
                }
            }
        }
    }

    Shortcut {
        sequences: [StandardKey.Save]
        enabled: applicationWindow.canSaveProject
        onActivated: Globals.BackendWrapper.projectSave()
    }

    // Save feedback is asymmetric: a failure must not be missable, so it is modal, while a
    // successful save flashes the tool button and updates the status bar instead of interrupting.
    Connections {
        target: Globals.BackendWrapper
        ignoreUnknownSignals: true

        function onProjectSaved(path) {
            saveFlashTimer.restart()
            if (applicationWindow.quitAfterSave) {
                applicationWindow.quitAfterSave = false
                Qt.quit()
            }
        }

        function onProjectSaveError(message) {
            // A failed "Save and exit" must not exit: the work is still only in memory.
            applicationWindow.quitAfterSave = false
            projectSaveErrorDialog.title = qsTr('Project Save Error')
            projectSaveErrorDialog.errorMessage = message
            projectSaveErrorDialog.open()
        }

        // Once per streak of failed automatic saves; the status bar keeps showing the failure
        // until a save succeeds, so that a broken destination does not reopen this on every tab.
        function onProjectAutosaveError(message) {
            projectSaveErrorDialog.title = qsTr('Automatic Save Failed')
            projectSaveErrorDialog.errorMessage = message + '\n\n'
                    + qsTr('Your work is still in memory. Automatic saving will keep trying; '
                           + 'use Save to retry now, or turn automatic saving off in the Project page\'s Advanced controls.')
            projectSaveErrorDialog.open()
        }

        // Mirror the backend's choice into the persisted preference (the Project page toggles it).
        function onProjectAutosaveEnabledChanged() {
            projectPreferences.autosave = Globals.BackendWrapper.projectAutosaveEnabled
        }
    }

    // Automatic save checkpoint: leaving a page. The backend saves only when autosave is on, a
    // project has been created and changed, and no fit is running. The other checkpoints (a
    // successful fit, and just before a fit, an engine switch or an ORSO sample replacement)
    // are raised by the backend itself.
    Connections {
        target: applicationWindow.appBarCentralTabs
        function onCurrentIndexChanged() {
            Globals.BackendWrapper.projectAutosave('leaving a page')
        }
    }

    // Application preference, not project content: kept in the shared settings file next to the
    // Preferences dialog's own, and pushed to the backend once it has been read.
    Settings {
        id: projectPreferences
        location: EaGlobals.Vars.settingsFile
        category: 'Preferences.Project'
        property bool autosave: true
        Component.onCompleted: Globals.BackendWrapper.projectSetAutosaveEnabled(autosave)
    }

    EaElements.Dialog {
        id: projectSaveErrorDialog
        title: qsTr('Project Save Error')
        standardButtons: Dialog.Ok
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        property string errorMessage: ''

        EaElements.Label {
            text: projectSaveErrorDialog.errorMessage
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
        }
    }

    EaElements.Dialog {
        id: resetStateDialog

        title: qsTr("Reset state")
        modal: true

        EaElements.Label {
            horizontalAlignment: Text.AlignHCenter
            // Now that unsaved changes are tracked, the dialog can say what is actually at risk
            // instead of warning about loss that may not exist.
            text: {
                const question = qsTr("Are you sure you want to reset the application to its\noriginal state without project, sample and data?")
                if (Globals.BackendWrapper.projectHasUnsavedChanges) {
                    return question + '\n\n' + qsTr("The project has unsaved changes that will be lost.")
                }
                return question + '\n\n' + qsTr("This operation cannot be undone.")
            }
        }

        footer: EaElements.DialogButtonBox {
            EaElements.Button {
                text: qsTr("Cancel")
                onClicked: resetStateDialog.close()
            }

            EaElements.Button {
                text: qsTr("OK")
                onClicked: {
                    applicationWindow.resetToInitialState()
                    resetStateDialog.close()
                }
            }
        }
    }

    // Back to the state the application starts in: default sample, no data, no project, and only
    // the Home and Project tabs enabled. Shared by the reset button and "Start from scratch"
    // when creating a new project.
    function resetToInitialState() {
        const tabs = Globals.References.applicationWindow.appBarCentralTabs
        for (const button of [tabs.sampleButton, tabs.experimentButton, tabs.analysisButton, tabs.summaryButton]) {
            if (button !== null) {
                button.enabled = false
            }
        }
        Globals.BackendWrapper.projectReset()
        tabs.projectButton.toggle()
        Globals.References.resetActive = false
    }

    // A refused calculation engine switch only reaches the log otherwise,
    // which the GUI user cannot see. One dialog here rather than one per
    // engine selector (Sample and Analysis pages), so it cannot stack.
    Connections {
        target: Globals.BackendWrapper.activeBackend ? Globals.BackendWrapper.activeBackend.sample : null
        enabled: target !== null
        ignoreUnknownSignals: true
        function onCalculationEngineRejected(message) {
            engineRejectionDialog.title = qsTr("Cannot change the calculation engine")
            engineRejectionDialog.message = message
            engineRejectionDialog.open()
        }
    }

    // A data file that cannot be imported: the same message dialog.
    Connections {
        target: Globals.BackendWrapper.activeBackend ? Globals.BackendWrapper.activeBackend.experiment : null
        enabled: target !== null
        ignoreUnknownSignals: true
        function onLoadFailed(message) {
            showLoadMessage(qsTr("Cannot import the data"), message)
        }
        // Imported, but with an assumption the user should know about (e.g. a
        // file without a resolution column merged with files that have one).
        function onLoadWarning(message) {
            showLoadMessage(qsTr("Data imported with a warning"), message)
        }
        // An import of several files reports file by file: add to a dialog
        // that is still open rather than replacing what it shows, and keep
        // its first title (a refusal outranks a later warning).
        function showLoadMessage(title, message) {
            if (engineRejectionDialog.visible) {
                engineRejectionDialog.message += '\n\n' + message
                return
            }
            engineRejectionDialog.title = title
            engineRejectionDialog.message = message
            engineRejectionDialog.open()
        }
    }

    EaElements.Dialog {
        id: engineRejectionDialog

        property string message: ''

        standardButtons: Dialog.Ok
        closePolicy: Popup.CloseOnEscape

        // The Column caps the dialog at the label's wrapped width; a bare
        // label would size the dialog to the unwrapped text instead.
        Column {
            EaElements.Label {
                wrapMode: Text.WordWrap
                width: EaStyle.Sizes.fontPixelSize * 26
                text: engineRejectionDialog.message
            }
        }
    }

    Component.onCompleted: {
        console.debug(`Application window loaded ::: ${this}`)
        Globals.References.applicationWindow.resetToInitialState = resetToInitialState
        if (Globals.BackendWrapper.testMode) {

            // To ensure that Qt starts up there is a delay before the it is shut down again.
            // When testing the application it should stay alive longer than the delay.
            console.debug('*** TEST MODE START ***')
            delay(30000, function() {
                console.debug('*** TEST MODE 30 s DELAYED END ***')
                // The harness must never hang on the unsaved-changes prompt.
                applicationWindow.discardChangesOnClose = true
                Qt.quit()
            })
        }
    }
    Component.onDestruction: console.debug(`Application window destroyed ::: ${this}`)
}

