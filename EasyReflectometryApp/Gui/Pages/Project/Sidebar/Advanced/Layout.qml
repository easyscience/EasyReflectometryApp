import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals


EaComponents.SideBarColumn {

    EaElements.GroupBox {
        title: qsTr('Saving')
        icon: 'save'
        collapsed: false

        Loader { source: 'Groups/Autosave.qml' }
    }

}
