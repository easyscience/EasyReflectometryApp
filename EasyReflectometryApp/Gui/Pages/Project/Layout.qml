import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals


EaComponents.ContentPage {

    defaultInfo: Globals.BackendWrapper.projectCreated ?
                     '' :
                     qsTr('No project defined\n')

    mainView: EaComponents.MainContent {
        tabs: [
            EaElements.TabButton { text: qsTr('Description') }
        ]

        items: [
            Loader { source: 'MainContent/Description.qml' }
        ]
    }

    sideBar: EaComponents.SideBar {
        tabs: [
            EaElements.TabButton { text: qsTr('Basic controls') }
        ]

        items: [
            Loader { source: 'Sidebar/Basic/Layout.qml' }
        ]

        continueButton.text: qsTr('Continue')

        continueButton.onClicked: {            
            console.debug(`Clicking '${continueButton.text}' button ::: ${this}`)
            Globals.References.resetActive = true
            Globals.References.applicationWindow.appBarCentralTabs.sampleButton.enabled = true
            Globals.References.applicationWindow.appBarCentralTabs.sampleButton.toggle()
        }
    }

    Component.onCompleted: console.debug(`Project page loaded ::: ${this}`)
    Component.onDestruction: console.debug(`Project page destroyed ::: ${this}`)

}
