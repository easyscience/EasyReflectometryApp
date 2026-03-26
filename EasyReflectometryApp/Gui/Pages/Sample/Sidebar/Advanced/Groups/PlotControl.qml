// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Plot control")
    collapsed: true

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        EaElements.CheckBox {
            topPadding: 0
            checked: Globals.BackendWrapper.plottingPlotRQ4
            text: qsTr("Plot R(q)×q⁴")
            ToolTip.text: qsTr("Checking this box will plot R(q) multiplied by q⁴")
            onToggled: {
                Globals.BackendWrapper.plottingTogglePlotRQ4()
            }
        }

        EaElements.CheckBox {
            topPadding: 0
            checked: Globals.Variables.reverseSldZAxis
            text: qsTr("Reverse SLD z-axis")
            ToolTip.text: qsTr("Checking this box will reverse the z-axis of the SLD plot")
            onToggled: {
                Globals.Variables.reverseSldZAxis = checked
            }
        }

        EaElements.CheckBox {
            topPadding: 0
            checked: Globals.Variables.logarithmicQAxis
            text: qsTr("Logarithmic q-axis")
            ToolTip.text: qsTr("Checking this box will make the q-axis logarithmic on the sample plot")
            onToggled: {
                Globals.Variables.logarithmicQAxis = checked
            }
        }
    }
}
