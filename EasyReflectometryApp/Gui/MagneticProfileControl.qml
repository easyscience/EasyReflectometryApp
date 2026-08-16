// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

// Which magnetic depth profiles the shared SLD chart draws. One control, one
// piece of state in the backend, so the Sample and Analysis SLD tabs always
// agree. Only meaningful once a layer is magnetic; the groups embedding this
// component hide themselves otherwise.
Column {
    spacing: EaStyle.Sizes.fontPixelSize * 0.5

    EaElements.CheckBox {
        topPadding: 0
        checked: Globals.BackendWrapper.plottingVisibleSldCurves.indexOf('spin_up') !== -1
        text: qsTr("Show ρ↑ and ρ↓")
        ToolTip.text: qsTr("The potentials each spin state sees: ρ ± ρM·cos(θM − A)")
        onToggled: Globals.BackendWrapper.plottingSetSldCurveVisible('spin_up', checked)
    }

    EaElements.CheckBox {
        topPadding: 0
        checked: Globals.BackendWrapper.plottingVisibleSldCurves.indexOf('rho_m') !== -1
        text: qsTr("Show ρM")
        ToolTip.text: qsTr("The magnetic scattering length density profile")
        onToggled: Globals.BackendWrapper.plottingSetSldCurveVisible('rho_m', checked)
    }

    EaElements.CheckBox {
        topPadding: 0
        checked: Globals.BackendWrapper.plottingVisibleSldCurves.indexOf('theta_m') !== -1
        text: qsTr("Show θM")
        ToolTip.text: qsTr("The in-plane moment angle, on its own right-hand axis")
        onToggled: Globals.BackendWrapper.plottingSetSldCurveVisible('theta_m', checked)
    }

    EaElements.Label {
        color: EaStyle.Colors.themeForegroundMinor
        wrapMode: Text.WordWrap
        width: EaStyle.Sizes.sideBarContentWidth
        text: qsTr("ρ↑/ρ↓ are what each spin state sees; where a layer is non-magnetic they fall onto the nuclear SLD.")
    }
}
