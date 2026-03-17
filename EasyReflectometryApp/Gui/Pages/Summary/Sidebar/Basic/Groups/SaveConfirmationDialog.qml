// SPDX-FileCopyrightText: 2025 EasyApp contributors
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements


EaElements.Dialog {
    id: dialog
    property bool success: false
    property string filePath: ''
    visible: false
    title: qsTr('Save confirmation')
    standardButtons: Dialog.Ok

    function _fileNameFromPath(path) {
        if (!path) {
            return ''
        }
        return path.split(/[\\/]/).pop()
    }

    Row {
        padding: EaStyle.Sizes.fontPixelSize
        spacing: EaStyle.Sizes.fontPixelSize * 0.75

        EaElements.Label {
            anchors.verticalCenter: parent.verticalCenter
            font.family: EaStyle.Fonts.iconsFamily
            font.pixelSize: EaStyle.Sizes.fontPixelSize * 1.25
            text: dialog.success ? 'check-circle' : 'minus-circle'
        }

        EaElements.Label {
            anchors.verticalCenter: parent.verticalCenter
            text: dialog.success
                  ? qsTr('File "%1" is successfully saved').arg(dialog._fileNameFromPath(dialog.filePath))
                  : qsTr('Failed to save file "%1"').arg(dialog._fileNameFromPath(dialog.filePath))
        }
    }
}
