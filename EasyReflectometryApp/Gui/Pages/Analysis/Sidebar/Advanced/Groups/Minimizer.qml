// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Minimization method")
    icon: 'level-down-alt'

    EaElements.GroupRow{
            EaElements.ComboBox {
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 2
                topInset: minimizerLabel.height
                topPadding: topInset + padding
                model: Globals.BackendWrapper.analysisMinimizersAvailable
                EaElements.Label {
                    id: minimizerLabel
                    text: qsTr("Minimizer")
                    color: EaStyle.Colors.themeForegroundMinor
                }
                currentIndex: Globals.BackendWrapper.analysisMinimizerCurrentIndex
                onCurrentIndexChanged: Globals.BackendWrapper.analysisSetMinimizerCurrentIndex(currentIndex)
            }

        EaElements.TextField {
            width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 4
            topInset: toleranceLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            onAccepted: {
                onAccepted: Globals.BackendWrapper.analysisSetMinimizerTolerance(text)
                focus = false
            }
            text: Globals.BackendWrapper.analysisMinimizerTolerance === undefined ? 'Defaults' : Number(Globals.BackendWrapper.analysisMinimizerTolerance).toFixed(3)
            EaElements.Label {
                id: toleranceLabel
                text: qsTr("Tolerance")
                color: EaStyle.Colors.themeForegroundMinor
            }
        }

        EaElements.TextField {
            width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 4
            topInset: maxIterLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            onAccepted: {
                Globals.BackendWrapper.analysisSetMinimizerMaxIterations(text)
                focus = false
            }
            text: Globals.BackendWrapper.analysisMinimizerMaxIterations === undefined ? 'Defaults' : Number(Globals.BackendWrapper.analysisMinimizerMaxIterations)
            EaElements.Label {
                id: maxIterLabel
                text: qsTr("Max evaluations")
                color: EaStyle.Colors.themeForegroundMinor
            }
        }
    }
}
