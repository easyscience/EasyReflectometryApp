import QtQuick
import QtQuick.Controls
//import QtQuick.XmlListModel 2.15

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals
//import Gui.Components as Components


EaComponents.ContentPage {

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

    sideBar: EaComponents.SideBar {
        tabs: [
            EaElements.TabButton { text: qsTr("Basic controls") },
            EaElements.TabButton { text: qsTr("Extra controls") } //; enabled: Globals.Proxies.main.analysis.defined }
        ]

        items: [
            Loader { source: 'Sidebar/Basic/Layout.qml' },
            Loader { source: 'Sidebar/Advanced/Layout.qml' }
        ]

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
