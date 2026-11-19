// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

// z range of the SLD charts. One piece of state (Globals.Variables), embedded on
// both the Sample and Analysis pages, so the two SLD charts always agree.
// Display only: the profiles are still calculated on the engine's own z grid
// and extended flat to a wider range by SldChart.
EaElements.GroupBox {
    id: group

    title: qsTr("SLD z range")
    collapsed: true

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        EaElements.CheckBox {
            topPadding: 0
            checked: Globals.Variables.sldZAuto
            text: qsTr("Auto")
            ToolTip.text: qsTr("Fit the z axis to the calculated SLD profiles")
            onToggled: {
                if (!checked) {
                    group.seedManualRange()
                }
                Globals.Variables.sldZAuto = checked
            }
        }

        Row {
            spacing: EaStyle.Sizes.fontPixelSize * 0.5
            enabled: !Globals.Variables.sldZAuto

            EaComponents.TableViewLabel {
                text: qsTr("z-min:")
                horizontalAlignment: Text.AlignRight
                width: group.labelWidth()
            }
            EaElements.Parameter {
                id: zMinField
                width: group.textFieldWidth()
                units: "Å"
                text: group.zMinText()
                onEditingFinished: {
                    const value = parseFloat(text)
                    if (isFinite(value) && value < Globals.Variables.sldZMax) {
                        Globals.Variables.sldZMin = value
                    }
                    // Show the stored value again (also undoes invalid input)
                    text = Qt.binding(group.zMinText)
                }
            }

            EaComponents.TableViewLabel {
                text: qsTr("z-max:")
                horizontalAlignment: Text.AlignRight
                width: group.labelWidth()
            }
            EaElements.Parameter {
                id: zMaxField
                width: group.textFieldWidth()
                units: "Å"
                text: group.zMaxText()
                onEditingFinished: {
                    const value = parseFloat(text)
                    if (isFinite(value) && value > Globals.Variables.sldZMin) {
                        Globals.Variables.sldZMax = value
                    }
                    text = Qt.binding(group.zMaxText)
                }
            }
        }
    }

    // Logic

    // While Auto is on, the fields show the calculated range of all models.
    function zMinText() {
        return (Globals.Variables.sldZAuto ? Globals.BackendWrapper.plottingSldMinX
                                           : Globals.Variables.sldZMin).toFixed(1)
    }
    function zMaxText() {
        return (Globals.Variables.sldZAuto ? Globals.BackendWrapper.plottingSldMaxX
                                           : Globals.Variables.sldZMax).toFixed(1)
    }

    // Switching Auto off for the first time starts from the calculated range,
    // rounded to whole Å; afterwards the last manual range is kept.
    function seedManualRange() {
        const zMin = Globals.Variables.sldZMin
        const zMax = Globals.Variables.sldZMax
        if (isFinite(zMin) && isFinite(zMax) && zMin < zMax) {
            return
        }
        const autoMin = Math.floor(Globals.BackendWrapper.plottingSldMinX)
        const autoMax = Math.ceil(Globals.BackendWrapper.plottingSldMaxX)
        Globals.Variables.sldZMin = autoMin
        Globals.Variables.sldZMax = autoMax > autoMin ? autoMax : autoMin + 1
    }

    function labelWidth() {
        return EaStyle.Sizes.fontPixelSize * 3.5
    }
    function textFieldWidth() {
        return EaStyle.Sizes.fontPixelSize * 7.0
    }
}
