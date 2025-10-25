import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Dialogs

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Load a sample")
    collapsible: true
    collapsed: false

    EaElements.GroupColumn {
        EaElements.SideBarButton {
            width: EaStyle.Sizes.sideBarContentWidth
            fontIcon: "folder-open"
            text: qsTr("Load file")
            onClicked: fileDialog.open()
        }

        FileDialog {
            id: fileDialog
            title: qsTr("Select a sample file")
            onAccepted: Globals.BackendWrapper.sampleFileLoad(fileDialog.fileUrl)
        }
    }
}