// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui as Gui
import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Plot control")
    collapsed: true

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        Gui.PlotControlCommon {}

        EaElements.Label {
            text: qsTr("Marker style")
        }

        EaElements.ComboBox {
            model: ListModel {
                ListElement { text: qsTr("Dots"); value: 0 }
                ListElement { text: qsTr("Circles"); value: 1 }
                ListElement { text: qsTr("Line"); value: 2 }
            }
            currentIndex: {
                var val = Globals.Variables.experimentMarkerStyle
                for (var i = 0; i < model.count; ++i) {
                    if (model.get(i).value === val) {
                        return i
                    }
                }
                return 0  // default to dots
            }
            onCurrentIndexChanged: {
                if (currentIndex >= 0 && currentIndex < model.count) {
                    Globals.Variables.experimentMarkerStyle = model.get(currentIndex).value
                }
            }
            textRole: "text"
            valueRole: "value"
        }
    }
}

