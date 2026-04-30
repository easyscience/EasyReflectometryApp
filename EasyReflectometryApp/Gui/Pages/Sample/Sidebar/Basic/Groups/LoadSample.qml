import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Load a sample")
    collapsible: true
    collapsed: false

    EaElements.GroupColumn {
        EaElements.CheckBox {
            id: appendCheckBox
            text: qsTr("Append to existing models")
            checked: true
            width: EaStyle.Sizes.sideBarContentWidth
        }

        EaElements.SideBarButton {
            width: EaStyle.Sizes.sideBarContentWidth
            fontIcon: "folder-open"
            text: qsTr("Load sample from file")
            onClicked: fileDialog.open()
        }

        FileDialog {
            id: fileDialog
            title: qsTr("Select a sample file")
            nameFilters: [ "ORT files (*.ort)", "ORSO files (*.orso)", "All files (*.*)" ]
            onAccepted: Globals.BackendWrapper.sampleFileLoad(selectedFiles[0], appendCheckBox.checked)
        }
    }

    // Warning dialog for sample load issues
    EaElements.Dialog {
        id: sampleLoadWarningDialog
        title: qsTr("Sample Load Warning")
        standardButtons: Dialog.Ok
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        property string warningMessage: ""

        EaElements.Label {
            text: sampleLoadWarningDialog.warningMessage
            wrapMode: Text.WordWrap
            width: Math.min(implicitWidth, EaStyle.Sizes.sideBarContentWidth * 1.5)
        }
    }

    Connections {
        target: Globals.BackendWrapper
        function onSampleLoadWarning(message) {
            sampleLoadWarningDialog.warningMessage = message
            sampleLoadWarningDialog.open()
        }
    }
}