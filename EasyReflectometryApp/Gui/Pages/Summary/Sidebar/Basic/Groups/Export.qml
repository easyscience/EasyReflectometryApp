// 5SPDX-FileCopyrightText: 2025 EasyApp contributors
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs
import QtCore

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Logic as EaLogic

import Gui.Globals as Globals


Column {
    spacing: EaStyle.Sizes.fontPixelSize

    // Name field + format selector
    Row {
        spacing: EaStyle.Sizes.fontPixelSize

        // Name field
        EaElements.TextField {
            id: nameField
            width: saveButton.width - formatField.width - parent.spacing
            topInset: nameLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            placeholderText: qsTr('Enter summary file name here')
            Component.onCompleted: text = Globals.BackendWrapper.summaryFileName
            onEditingFinished: Globals.BackendWrapper.summarySetFileName(text)
            EaElements.Label {
                id: nameLabel
                text: qsTr('Name')
            }
        }

        EaElements.ComboBox {
            id: formatField
            topInset: formatLabel.height
            topPadding: topInset + padding
            width: EaStyle.Sizes.fontPixelSize * 10
            model: Globals.BackendWrapper.summaryExportFormats
            EaElements.Label {
                id: formatLabel
                text: qsTr('Format')
            }
        }
        // Format selector
    }
    // Name field + format selector

    // Location field
    EaElements.TextField {
        id: reportLocationField
        width: saveButton.width
        topInset: locationLabel.height
        topPadding: topInset + padding
        rightPadding: chooseButton.width
        horizontalAlignment: TextInput.AlignLeft
        Component.onCompleted: text = Globals.BackendWrapper.summaryFilePath
        EaElements.Label {
            id: locationLabel
            text: qsTr('Location')
        }

        EaElements.ToolButton {
            id: chooseButton
            anchors.right: parent.right
            topPadding: parent.topPadding
            showBackground: false
            fontIcon: 'folder-open'
            ToolTip.text: qsTr('Choose summary parent directory')
            onClicked: summaryParentDirDialog.open()
        }
    }

    // Save button
    EaElements.SideBarButton {
        id: saveButton
        wide: true
        fontIcon: 'download'
        text: qsTr('Save')
        onClicked: {
           if (formatField.currentValue === 'HTML') {
               Globals.BackendWrapper.summarySaveAsHtml()
           } else if (formatField.currentValue === 'PDF') {
               Globals.BackendWrapper.summarySaveAsPdf()
           }
       }
    }

    // Save directory dialog
    FolderDialog {
        id: summaryParentDirDialog
        title: qsTr("Choose report parent directory")
        currentFolder: Globals.BackendWrapper.summaryFileUrl
    }

}
