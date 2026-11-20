import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui as Gui
import Gui.Globals as Globals

import "../../Logic/FitProgressText.js" as FitProgressText


EaComponents.ContentPage {

    Loader {
        source: 'Sidebar/Basic/Popups/FitStatusDialog.qml'
    }

    Loader {
        source: 'Sidebar/Basic/Popups/PrefitCheckDialog.qml'
    }

    Loader {
        source: 'Sidebar/Basic/Popups/FitCancelledDialog.qml'
    }

    mainView: EaComponents.MainContent {
        tabs: [
            EaElements.TabButton { text: qsTr('Reflectivity') },
            EaElements.TabButton {
                text: qsTr('Bayesian Posterior')
                enabled: Globals.BackendWrapper.bayesianResultAvailable
            }
       ]

        items: [
            Loader {
                source: `MainContent/CombinedView.qml`
                onStatusChanged: if (status === Loader.Ready) console.debug(`${source} loaded`)
            },
            Loader {
                // The Bayesian views are WebEngine (Chromium) based. Only start it once
                // there is a result to show; on software OpenGL (remote desktops) an idle
                // Chromium GPU thread is enough to freeze the window.
                active: Globals.BackendWrapper.bayesianResultAvailable
                source: `MainContent/BayesianPosteriorView.qml`
                onStatusChanged: if (status === Loader.Ready) console.debug(`${source} loaded`)
            }
        ]
    }

    sideBar: Gui.SideBarWithFooter {
        tabs: [
            EaElements.TabButton { text: qsTr("Basic controls") },
            EaElements.TabButton { text: qsTr("Extra controls") }
        ]

        items: [
            Loader { source: 'Sidebar/Basic/Layout.qml' },
            Loader { source: 'Sidebar/Advanced/Layout.qml' }
        ]

        // Start/Cancel, and while a run is active its progress: shown under both
        // sidebar tabs, unlike the Basic tab's Fitting group.
        footerComponent: Component {
            Column {
                id: fitFooter

                readonly property var progress: Globals.BackendWrapper.analysisFitProgress
                readonly property bool active: progress.phase !== ''
                // For the elapsed time, which advances between progress reports.
                property real now: Date.now()

                spacing: 0.5 * EaStyle.Sizes.fontPixelSize

                EaElements.SideBarButton {
                    enabled: Globals.BackendWrapper.analysisExperimentsAvailable.length
                    wide: true
                    fontIcon: Globals.BackendWrapper.analysisFittingRunning ? 'stop-circle' : 'play-circle'
                    text: Globals.BackendWrapper.analysisFittingRunning ? qsTr('Cancel fitting') : (Globals.BackendWrapper.analysisIsBayesianSelected ? qsTr('Start sampling') : qsTr('Start fitting'))

                    onClicked: {
                        console.debug(`Clicking '${text}' button: ${this}`)
                        Globals.BackendWrapper.analysisFittingStartStop()
                    }

                    Component.onCompleted: Globals.References.pages.analysis.sidebar.basic.popups.startFittingButton = this
                }

                Gui.FitProgressBar {
                    visible: fitFooter.active
                    width: parent.width
                    progress: fitFooter.progress
                }

                EaElements.Label {
                    visible: fitFooter.active
                    width: parent.width
                    wrapMode: Text.WordWrap
                    color: EaStyle.Colors.themeForegroundMinor
                    text: FitProgressText.detailText(fitFooter.progress, fitFooter.now)
                }

                Timer {
                    interval: 1000
                    repeat: true
                    triggeredOnStart: true
                    running: fitFooter.active
                    onTriggered: fitFooter.now = Date.now()
                }
            }
        }

        continueButton.onClicked: {
            console.debug(`Clicking '${continueButton.text}' button: ${this}`)
            Globals.References.applicationWindow.appBarCentralTabs.summaryButton.enabled = true
            Globals.References.applicationWindow.appBarCentralTabs.summaryButton.toggle()
        }
    }

    Component.onCompleted: console.debug(`Analysis page loaded: ${this}`)
    Component.onDestruction: console.debug(`Analysis page destroyed: ${this}`)
}
