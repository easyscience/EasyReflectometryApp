// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


EaElements.GroupBox {
    title: qsTr("Polarization")
    collapsible: false

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        EaElements.CheckBox {
            text: qsTr("Treat loaded datasets as polarized channels")
            checked: Globals.BackendWrapper.polarizationPolarized
            ToolTip.text: qsTr("Group the separately-loaded experiment files into spin channels")
            onClicked: Globals.BackendWrapper.polarizationSetPolarized(checked)
        }

        EaElements.Label {
            width: parent.width
            wrapMode: Text.WordWrap
            text: qsTr("Loaded files map to channels in order: R++, R--, R+-, R-+")
            font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.8
            color: EaStyle.Colors.themeForegroundMinor
        }
    }
}
