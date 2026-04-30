// SPDX-FileCopyrightText: 2026 EasyApp contributors
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements


EaElements.Dialog {
    id: saveConfirmationDialog

    property bool success: false
    property string filePath: 'undefined'

    visible: false
    title: qsTr('Save confirmation')

    standardButtons: Dialog.Ok

    Row {
        padding: EaStyle.Sizes.fontPixelSize
        spacing: EaStyle.Sizes.fontPixelSize * 0.75

        EaElements.Label {
            anchors.verticalCenter: parent.verticalCenter
            font.family: EaStyle.Fonts.iconsFamily
            font.pixelSize: EaStyle.Sizes.fontPixelSize * 1.25
            text: saveConfirmationDialog.success ? 'check-circle' : 'minus-circle'
        }

        EaElements.Label {
            anchors.verticalCenter: parent.verticalCenter
            text: saveConfirmationDialog.success
                  ? qsTr('File "<a href="%1">%1</a>" is successfully saved'.arg(saveConfirmationDialog.filePath))
                  : qsTr('Failed to save file "%1"'.arg(saveConfirmationDialog.filePath))
        }
    }
}