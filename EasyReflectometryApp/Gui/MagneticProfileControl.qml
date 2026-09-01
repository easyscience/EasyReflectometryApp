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
        ToolTip.text: qsTr("ρ ± ρM·cos(θM − A) — the effective SLD each spin state sees")
        onToggled: Globals.BackendWrapper.plottingSetSldCurveVisible('spin_up', checked)
    }

    EaElements.CheckBox {
        topPadding: 0
        checked: Globals.BackendWrapper.plottingVisibleSldCurves.indexOf('rho_m') !== -1
        text: qsTr("Show ρM")
        ToolTip.text: qsTr("Magnetic SLD profile")
        onToggled: Globals.BackendWrapper.plottingSetSldCurveVisible('rho_m', checked)
    }

    EaElements.CheckBox {
        topPadding: 0
        checked: Globals.BackendWrapper.plottingVisibleSldCurves.indexOf('theta_m') !== -1
        text: qsTr("Show θM")
        ToolTip.text: qsTr("In-plane moment angle, plotted on the right-hand axis")
        onToggled: Globals.BackendWrapper.plottingSetSldCurveVisible('theta_m', checked)
    }

    EaElements.Label {
        color: EaStyle.Colors.themeForegroundMinor
        wrapMode: Text.WordWrap
        width: EaStyle.Sizes.sideBarContentWidth
        text: qsTr("For non-magnetic layers, ρ↑ and ρ↓ collapse onto the nuclear SLD.")
    }

    // The magnetic profiles failed to compute (e.g. the calculator lost its
    // magnetism binding): without this, the curves silently vanish and the
    // reason is only in a log the GUI user cannot see.
    EaElements.Label {
        visible: Globals.BackendWrapper.plottingMagneticProfileError !== ''
        color: EaStyle.Colors.red
        wrapMode: Text.WordWrap
        width: EaStyle.Sizes.sideBarContentWidth
        text: qsTr("The magnetic profiles could not be computed: %1")
              .arg(Globals.BackendWrapper.plottingMagneticProfileError)
    }
}
