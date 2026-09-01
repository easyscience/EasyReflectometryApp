// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

import EasyApplication.Gui.Elements as EaElements

import Gui as Gui

// The engine is a project-wide setting owned by the Analysis page, repeated
// here because magnetism depends on it: the Sample page is where a layer is
// made magnetic, and the Analysis page is not always reachable yet.
EaElements.GroupBox {
    title: qsTr("Calculation engine")
    icon: 'calculator'
    collapsible: true
    collapsed: true

    Gui.CalculationEngineControl {}
}
