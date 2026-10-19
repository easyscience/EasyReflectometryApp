// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui as Gui
import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Plot control")
    collapsed: true

    EaElements.GroupColumn {
        Gui.PlotControlRefLines {}

        // Magnetic profile switches for the SLD tab, next to the other chart
        // controls. Absent while no model is magnetic.
        Gui.MagneticProfileControl {
            visible: Globals.BackendWrapper.plottingAnyModelHasMagnetism
        }
    }
}

