import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals


EaComponents.ContentPage {
    mainView: EaComponents.MainContent {
        // Named for the tutorials, which also read the open one as `ui.sample_view`
        tabs: [
            EaElements.TabButton {
                objectName: 'sample.reflectivityTab'
                text: qsTr('Reflectivity')
                onCheckedChanged: if (checked) Globals.BackendWrapper.tutorialReportUi('sample_view', 'reflectivity')
            },
            EaElements.TabButton {
                objectName: 'sample.structureTab'
                text: qsTr('Structure')
                onCheckedChanged: if (checked) Globals.BackendWrapper.tutorialReportUi('sample_view', 'structure')
            }
       ]

        items: [
            Loader {
                source: `MainContent/CombinedView.qml`
                onStatusChanged: if (status === Loader.Ready) console.debug(`${source} loaded`)
            },
            Loader {
                source: `MainContent/StructureView.qml`
                onStatusChanged: if (status === Loader.Ready) console.debug(`${source} loaded`)
            }
        ]
   }

    sideBar: EaComponents.SideBar {
        tabs: [
            // Named for the tutorials: `<page>.<sidebar-tab>Tab`
            EaElements.TabButton { objectName: 'sample.basicTab'; text: qsTr('Basic controls') },
            EaElements.TabButton { objectName: 'sample.advancedTab'; text: qsTr('Advanced controls') }
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
