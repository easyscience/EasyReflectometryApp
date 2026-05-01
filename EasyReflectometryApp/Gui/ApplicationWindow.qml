import QtQuick
import QtQuick.Controls

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
            enabled: Globals.BackendWrapper.projectCreated
            highlighted: true
            fontIcon: "save"
            ToolTip.text: qsTr("Save current state of the project")
            onClicked: Globals.BackendWrapper.projectSave()
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

    onClosing: Qt.quit()

    EaElements.Dialog {
        id: resetStateDialog

        title: qsTr("Reset state")

        EaElements.Label {
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("Are you sure you want to reset the application to its\noriginal state without project, sample and data?\n\nThis operation cannot be undone.")
        }

        footer: EaElements.DialogButtonBox {
            EaElements.Button {
                text: qsTr("Cancel")
                onClicked: resetStateDialog.close()
            }

            EaElements.Button {
                text: qsTr("OK")
                onClicked: {
                    if (Globals.References.applicationWindow.appBarCentralTabs.sampleButton !== null) {
                        Globals.References.applicationWindow.appBarCentralTabs.sampleButton.enabled = false
                    }
                    if (Globals.References.applicationWindow.appBarCentralTabs.experimentButton !== null) {
                        Globals.References.applicationWindow.appBarCentralTabs.experimentButton.enabled = false
                    }
                    if (Globals.References.applicationWindow.appBarCentralTabs.analysisButton !== null) {
                        Globals.References.applicationWindow.appBarCentralTabs.analysisButton.enabled = false
                    }
                    if (Globals.References.applicationWindow.appBarCentralTabs.summaryButton !== null) {
                        Globals.References.applicationWindow.appBarCentralTabs.summaryButton.enabled = false
                    }

                    Globals.BackendWrapper.projectReset()
                    Globals.References.applicationWindow.appBarCentralTabs.projectButton.toggle()
                    Globals.References.resetActive = false
                    resetStateDialog.close()
                }
            }
        }
    }

    Component.onCompleted: {
        console.debug(`Application window loaded ::: ${this}`)
        if (Globals.BackendWrapper.testMode) {

            // To ensure that Qt starts up there is a delay before the it is shut down again.
            // When testing the application it should stay alive longer than the delay.
            console.debug('*** TEST MODE START ***')
            delay(30000, function() {
                console.debug('*** TEST MODE 30 s DELAYED END ***')
                Qt.quit()
            })
        }
    }
    Component.onDestruction: console.debug(`Application window destroyed ::: ${this}`)
}

