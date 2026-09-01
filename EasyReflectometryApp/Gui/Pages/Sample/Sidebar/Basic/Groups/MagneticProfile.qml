// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui as Gui
import Gui.Globals as Globals

// Display controls for the magnetic curves, directly below the Magnetism
// group: make a layer magnetic and the controls for showing it appear right
// underneath. Absent entirely while no model is magnetic.
EaElements.GroupBox {
    title: qsTr("Magnetic profile")
    collapsible: true
    visible: Globals.BackendWrapper.plottingAnyModelHasMagnetism

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        // The depth profiles on the SLD chart; shared with the Analysis page,
        // hence a component of its own.
        Gui.MagneticProfileControl {}

        // The spin cross-sections on the reflectivity chart. Sample page only:
        // the Analysis chart already draws one calculated curve per measured
        // spin channel when the experiment is polarized.
        EaElements.CheckBox {
            topPadding: 0
            checked: Globals.BackendWrapper.plottingShowModelChannels
            text: qsTr("Show R↑↑ and R↓↓")
            ToolTip.text: qsTr("Split the model's reflectivity into its non-spin-flip cross-sections")
            onToggled: Globals.BackendWrapper.plottingSetShowModelChannels(checked)
        }

        // Without this the coinciding R↑↑ curve reads as a drawing fault rather
        // than as what it is: the plain curve of a magnetic sample is not an
        // unpolarized average, it is that one cross-section.
        EaElements.Label {
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
            text: qsTr("The model curve already is the ↑↑ cross-section, so R↑↑ is drawn on top of it.")
        }
    }
}
