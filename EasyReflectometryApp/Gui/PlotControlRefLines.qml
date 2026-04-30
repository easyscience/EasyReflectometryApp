// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

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
        checked: Globals.Variables.logarithmicQAxis
        text: qsTr("Logarithmic q-axis")
        ToolTip.text: qsTr("Checking this box will make the q-axis logarithmic")
        onToggled: {
            Globals.Variables.logarithmicQAxis = checked
        }
    }

    EaElements.CheckBox {
        topPadding: 0
        checked: Globals.BackendWrapper.plottingScaleShown
        text: qsTr("Show scale line")
        ToolTip.text: qsTr("Checking this box will show the scale reference line on the plot")
        onToggled: {
            Globals.BackendWrapper.plottingFlipScaleShown()
        }
    }

    EaElements.CheckBox {
        topPadding: 0
        checked: Globals.BackendWrapper.plottingBkgShown
        text: qsTr("Show background line")
        ToolTip.text: qsTr("Checking this box will show the background reference line on the plot")
        onToggled: {
            Globals.BackendWrapper.plottingFlipBkgShown()
        }
    }
}
