// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements

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
