// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

import EasyApplication.Gui.Elements as EaElements

import Gui as Gui
import Gui.Globals as Globals

// Display controls for the magnetic depth profiles, directly below the
// Magnetism group: make a layer magnetic and the control for showing it appears
// right underneath. Absent entirely while no model is magnetic.
EaElements.GroupBox {
    title: qsTr("Magnetic profile")
    collapsible: true
    visible: Globals.BackendWrapper.plottingAnyModelHasMagnetism

    Gui.MagneticProfileControl {}
}
