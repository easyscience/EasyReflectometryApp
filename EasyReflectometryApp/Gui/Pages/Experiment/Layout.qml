 import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals


EaComponents.ContentPage {

    mainView: EaComponents.MainContent {
        items: [
            Loader {
                source: `MainContent/ExperimentView.qml`
                onStatusChanged: if (status === Loader.Ready) console.debug(`${source} loaded`)
            }
        ]
   }

    sideBar: EaComponents.SideBar {
        tabs: [
            EaElements.TabButton { text: qsTr('Basic controls') },
            EaElements.TabButton { text: qsTr('Advanced controls') }
        ]

        items: [
            Loader { source: 'Sidebar/Basic/Layout.qml' },
            Loader { source: 'Sidebar/Advanced/Layout.qml' }
        ]

        continueButton.text: qsTr('Continue') 
        continueButton.onClicked: {            
            console.debug(`Clicking '${continueButton.text}' button ::: ${this}`)
            Globals.References.applicationWindow.appBarCentralTabs.analysisButton.enabled = true
            Globals.References.applicationWindow.appBarCentralTabs.analysisButton.toggle()
        }
    }

    Component.onCompleted: console.debug(`Experiment page loaded ::: ${this}`)
    Component.onDestruction: console.debug(`Experiment page destroyed ::: ${this}`)

}
