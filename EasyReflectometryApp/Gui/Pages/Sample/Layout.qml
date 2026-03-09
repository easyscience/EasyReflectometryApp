import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals


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
            Globals.References.applicationWindow.appBarCentralTabs.experimentButton.enabled = true
            Globals.References.applicationWindow.appBarCentralTabs.experimentButton.toggle()
        }
    }

    Component.onCompleted: console.debug(`Sample page loaded ::: ${this}`)
    Component.onDestruction: console.debug(`Sample page destroyed ::: ${this}`)
}
