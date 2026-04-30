// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Calculation engine")
    icon: 'calculator'
    EaElements.GroupRow {

        EaElements.ComboBox {
            width: EaStyle.Sizes.sideBarContentWidth
            model: Globals.BackendWrapper.analysisCalculatorsAvailable
            currentIndex: Globals.BackendWrapper.analysisCalculatorCurrentIndex
            onCurrentIndexChanged: Globals.BackendWrapper.analysisSetCalculatorCurrentIndex(currentIndex)
        }
    }
}
