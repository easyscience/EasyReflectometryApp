// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


// Spin-channel selector for polarized experiments: one checkbox per measured
// channel of the current experiment. Only shown when the current experiment is
// polarized.
EaElements.GroupBox {
    title: qsTr("Polarization channels")
    collapsible: false
    visible: Globals.BackendWrapper.plottingCurrentExperimentIsPolarized

    Row {
        spacing: EaStyle.Sizes.fontPixelSize

        Repeater {
            model: Globals.BackendWrapper.plottingExperimentChannelList

            delegate: EaElements.CheckBox {
                text: `${modelData.label} ${modelData.channel}`
                checked: modelData.visible
                ToolTip.text: qsTr("Show the %1 channel on the charts").arg(modelData.channel)
                onToggled: Globals.BackendWrapper.plottingSetChannelVisible(modelData.channel, checked)
            }
        }
    }
}
