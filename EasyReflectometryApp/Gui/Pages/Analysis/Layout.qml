import QtQuick
import QtQuick.Controls
//import QtQuick.XmlListModel 2.15

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui as Gui
import Gui.Globals as Globals


EaComponents.ContentPage {

    Loader {
        source: 'Sidebar/Basic/Popups/FitStatusDialog.qml'
    }

    mainView: EaComponents.MainContent {
        tabs: [
            EaElements.TabButton { text: qsTr('Reflectivity') }
       ]

        items: [
            Loader {
                source: `MainContent/CombinedView.qml`
                onStatusChanged: if (status === Loader.Ready) console.debug(`${source} loaded`)
            }
        ]
    }

    sideBar: Gui.SideBarWithFooter {
        tabs: [
            EaElements.TabButton { text: qsTr("Basic controls") },
            EaElements.TabButton { text: qsTr("Extra controls") } //; enabled: Globals.Proxies.main.analysis.defined }
        ]

        items: [
            Loader { source: 'Sidebar/Basic/Layout.qml' },
            Loader { source: 'Sidebar/Advanced/Layout.qml' }
        ]

        footerComponent: Component {
            EaElements.SideBarButton {
                enabled: Globals.BackendWrapper.analysisExperimentsAvailable.length
                wide: true
                fontIcon: Globals.BackendWrapper.analysisFittingRunning ? 'stop-circle' : 'play-circle'
                text: Globals.BackendWrapper.analysisFittingRunning ? qsTr('Cancel fitting') : qsTr('Start fitting')

                onClicked: {
                    console.debug(`Clicking '${text}' button: ${this}`)
                    Globals.BackendWrapper.analysisFittingStartStop()
                }

                Component.onCompleted: Globals.References.pages.analysis.sidebar.basic.popups.startFittingButton = this
            }
        }

//        continueButton.enabled: Globals.Proxies.main.summary.isCreated

        continueButton.onClicked: {
            console.debug(`Clicking '${continueButton.text}' button: ${this}`)
            Globals.References.applicationWindow.appBarCentralTabs.summaryButton.enabled = true
            Globals.References.applicationWindow.appBarCentralTabs.summaryButton.toggle()
        }

//        Component.onCompleted: Globals.Refs.app.analysisPage.continueButton = continueButton
    }

    Component.onCompleted: console.debug(`Analysis page loaded: ${this}`)
    Component.onDestruction: console.debug(`Analysis page destroyed: ${this}`)
}
