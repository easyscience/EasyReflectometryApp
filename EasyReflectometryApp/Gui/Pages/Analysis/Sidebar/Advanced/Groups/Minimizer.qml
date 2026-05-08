// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Minimization method")
    icon: 'level-down-alt'

    Column {
        width: parent.width
        spacing: 0

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

                // Use a Component.onCompleted handler to set the initial selection to "Bumps_simplex"
                Component.onCompleted: {
                    // Find the index of "Bumps_simplex" in the model
                    for (let i = 0; i < model.length; i++) {
                        if (model[i] === "Bumps_simplex") {
                            currentIndex = i;
                            Globals.BackendWrapper.analysisSetMinimizerCurrentIndex(i);
                            break;
                        }
                    }
                }

                // Keep this binding for subsequent changes
                onCurrentIndexChanged: Globals.BackendWrapper.analysisSetMinimizerCurrentIndex(currentIndex)
            }

        // Classical tolerance / max evaluations fields — hidden in Bayesian mode
        EaElements.TextField {
            visible: !Globals.BackendWrapper.analysisIsBayesianSelected
            width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 4
            topInset: toleranceLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            onAccepted: {
                Globals.BackendWrapper.analysisSetMinimizerTolerance(text)
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
            visible: !Globals.BackendWrapper.analysisIsBayesianSelected
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

    // Bayesian DREAM controls — only visible when Bayesian is selected
    EaElements.GroupRow {
        visible: Globals.BackendWrapper.analysisIsBayesianSelected
        height: visible ? implicitHeight : 0

        EaElements.TextField {
            width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 4
            topInset: samplesLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            onEditingFinished: Globals.BackendWrapper.bayesianSetSamples(Number(text))
            text: Globals.BackendWrapper.bayesianSamples
            EaElements.Label {
                id: samplesLabel
                text: qsTr("Samples")
                color: EaStyle.Colors.themeForegroundMinor
            }
        }

        EaElements.TextField {
            width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 4
            topInset: burninLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            onEditingFinished: Globals.BackendWrapper.bayesianSetBurnIn(Number(text))
            text: Globals.BackendWrapper.bayesianBurnIn
            EaElements.Label {
                id: burninLabel
                text: qsTr("Burn-in")
                color: EaStyle.Colors.themeForegroundMinor
            }
        }

        EaElements.TextField {
            width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 4
            topInset: populationLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            onEditingFinished: Globals.BackendWrapper.bayesianSetPopulation(Number(text))
            text: Globals.BackendWrapper.bayesianPopulation
            EaElements.Label {
                id: populationLabel
                text: qsTr("Population")
                color: EaStyle.Colors.themeForegroundMinor
            }
        }

        EaElements.TextField {
            width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 4
            topInset: thinningLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            onEditingFinished: Globals.BackendWrapper.bayesianSetThinning(Number(text))
            text: Globals.BackendWrapper.bayesianThinning
            EaElements.Label {
                id: thinningLabel
                text: qsTr("Thinning")
                color: EaStyle.Colors.themeForegroundMinor
            }
        }
    }
    }
}
