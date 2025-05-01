// 5SPDX-FileCopyrightText: 2025 EasyApp contributors
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals


EaComponents.ContentPage {

    defaultInfo: Globals.BackendWrapper.summaryCreated ?
                     '' :
                     qsTr('No Summary Generated')

    mainView: EaComponents.MainContent {
        tabs: [
            EaElements.TabButton { text: qsTr('Summary') }
        ]

        items: [
            Loader { source: 'MainContent/Summary.qml' }
        ]
    }

    sideBar: EaComponents.SideBar {
        tabs: [
            EaElements.TabButton { text: qsTr('Basic controls') }
//            EaElements.TabButton { text: qsTr('Extra controls') }
        ]

        items: [
            Loader { source: 'Sidebar/Basic/Layout.qml' }
//            Loader { source: 'Sidebar/Extra/Layout.qml' }
        ]

        continueButton.visible: false
    }

    Component.onCompleted: console.debug(`Summary page loaded ::: ${this}`)
    Component.onDestruction: console.debug(`Summary page destroyed ::: ${this}`)

}
