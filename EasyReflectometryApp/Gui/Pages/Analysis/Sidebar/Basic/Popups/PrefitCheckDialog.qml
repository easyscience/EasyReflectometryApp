// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


// Shown when the backend refuses to start a fit (e.g. invalid parameter bounds).
EaElements.Dialog {
    id: dialog

    title: qsTr('Invalid Parameter Bounds')
    standardButtons: Dialog.Ok
    modal: true
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    property string message: ''

    EaElements.Label {
        text: dialog.message
        wrapMode: Text.WordWrap
        width: EaStyle.Sizes.sideBarContentWidth * 1.5
    }

    Connections {
        target: Globals.BackendWrapper

        function onAnalysisPrefitCheckFailed(title, message) {
            dialog.title = title
            dialog.message = message
            dialog.open()
        }
    }
}
