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

    // The text of an editable field is submitted back, so it must be exact:
    // shortening it (e.g. to 4 significant digits) would rewrite a seed or a
    // budget on an unedited submit. String() keeps every digit, and the
    // exponent form of small values (1e-7).
    function formatNumber(value) {
        if (value === undefined || value === null)
            return ''
        return String(Number(value))
    }

    // Called on Enter and on focus loss; unchanged text is not resubmitted
    // (Enter followed by focus loss fires twice). Empty text: back to the
    // engine default. Unparsable text: rejected, the field shows the stored
    // value again (the backend re-notifies after every submission).
    function submitNumber(field, setter, reset, binding) {
        const trimmed = field.text.trim()
        if (trimmed !== binding()) {
            if (trimmed === '')
                reset()
            else if (!isNaN(Number(trimmed)))
                setter(Number(trimmed))
        }
        field.text = Qt.binding(binding)
        field.focus = false
    }

    Column {
        width: parent.width
        spacing: 0

        // Inequality constraints are BUMPS penalties: tell the user when the
        // selected engine cannot (or only weakly can) enforce the ones defined.
        EaElements.Label {
            width: EaStyle.Sizes.sideBarContentWidth
            visible: Globals.BackendWrapper.sampleInequalityConstraintsCount > 0 &&
                     Globals.BackendWrapper.analysisInequalityConstraintsWarning.length > 0
            text: qsTr("⚠ %1").arg(Globals.BackendWrapper.analysisInequalityConstraintsWarning)
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeAccent
        }

        // Some minimizers (differential evolution) need finite bounds on every free parameter.
        EaElements.Label {
            width: EaStyle.Sizes.sideBarContentWidth
            visible: Globals.BackendWrapper.analysisMinimizerRequiresFiniteBounds &&
                     Globals.BackendWrapper.analysisUnboundedFreeParametersCount > 0
            text: qsTr("⚠ This minimizer requires finite bounds on all free parameters (%1 missing).")
                  .arg(Globals.BackendWrapper.analysisUnboundedFreeParametersCount)
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeAccent
        }

        EaElements.GroupRow{
            EaElements.ComboBox {
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 2
                topInset: minimizerLabel.height
                topPadding: topInset + padding
                model: Globals.BackendWrapper.analysisMinimizersAvailable
                // The selection lives in the project's fit settings: a loaded
                // project shows its own minimizer.
                currentIndex: Globals.BackendWrapper.analysisMinimizerCurrentIndex
                // onActivated fires on user choice only, so a programmatic
                // update (e.g. after a load) is not written back.
                onActivated: Globals.BackendWrapper.analysisSetMinimizerCurrentIndex(currentIndex)
                EaElements.Label {
                    id: minimizerLabel
                    text: qsTr("Minimizer")
                    color: EaStyle.Colors.themeForegroundMinor
                }
            }

            // Classical tolerance / max evaluations fields — hidden in Bayesian mode.
            // Empty means the engine's own default.
            EaElements.TextField {
                id: toleranceField
                visible: !Globals.BackendWrapper.analysisIsBayesianSelected
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 4
                topInset: toleranceLabel.height
                topPadding: topInset + padding
                horizontalAlignment: TextInput.AlignLeft
                placeholderText: qsTr("Engine default")
                text: formatNumber(Globals.BackendWrapper.analysisMinimizerTolerance)
                onEditingFinished: submitNumber(toleranceField,
                                                Globals.BackendWrapper.analysisSetMinimizerTolerance,
                                                Globals.BackendWrapper.analysisResetMinimizerTolerance,
                                                function() { return formatNumber(Globals.BackendWrapper.analysisMinimizerTolerance) })
                EaElements.Label {
                    id: toleranceLabel
                    text: qsTr("Tolerance")
                    color: EaStyle.Colors.themeForegroundMinor
                }
            }

            EaElements.TextField {
                id: maxIterField
                visible: !Globals.BackendWrapper.analysisIsBayesianSelected
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 4
                topInset: maxIterLabel.height
                topPadding: topInset + padding
                horizontalAlignment: TextInput.AlignLeft
                placeholderText: qsTr("Engine default")
                text: formatNumber(Globals.BackendWrapper.analysisMinimizerMaxIterations)
                onEditingFinished: submitNumber(maxIterField,
                                                Globals.BackendWrapper.analysisSetMinimizerMaxIterations,
                                                Globals.BackendWrapper.analysisResetMinimizerMaxIterations,
                                                function() { return formatNumber(Globals.BackendWrapper.analysisMinimizerMaxIterations) })
                EaElements.Label {
                    id: maxIterLabel
                    // BUMPS counts optimizer steps, the other engines function evaluations.
                    text: qsTr("Max evaluations")
                    color: EaStyle.Colors.themeForegroundMinor
                }
            }
        }

        // Zero-variance handling and the method-specific options — classical fits only
        EaElements.GroupRow {
            visible: !Globals.BackendWrapper.analysisIsBayesianSelected
            height: visible ? implicitHeight : 0

            EaElements.ComboBox {
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 2
                topInset: objectiveLabel.height
                topPadding: topInset + padding
                model: Globals.BackendWrapper.analysisFitObjectives
                currentIndex: model.indexOf(Globals.BackendWrapper.analysisFitObjective)
                onActivated: Globals.BackendWrapper.analysisSetFitObjective(model[currentIndex])
                ToolTip.visible: hovered
                ToolTip.text: qsTr("hybrid: Mighell substitution for zero-variance points, weighted least squares elsewhere.\n" +
                                   "mighell: Mighell transform for all points.\n" +
                                   "legacy_mask: drop zero-variance points.")
                EaElements.Label {
                    id: objectiveLabel
                    text: qsTr("Zero-variance points")
                    color: EaStyle.Colors.themeForegroundMinor
                }
            }
        }

        // One field per option the selected minimizer declares; empty means the engine default.
        Flow {
            visible: !Globals.BackendWrapper.analysisIsBayesianSelected &&
                     Globals.BackendWrapper.analysisMinimizerOptions.length > 0
            width: EaStyle.Sizes.sideBarContentWidth
            spacing: EaStyle.Sizes.fontPixelSize

            Repeater {
                model: Globals.BackendWrapper.analysisMinimizerOptions

                Loader {
                    id: optionLoader
                    required property var modelData
                    sourceComponent: modelData.kind === 'enum' ? enumOption : numberOption

                    Component {
                        id: numberOption
                        EaElements.TextField {
                            id: optionField
                            width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 4
                            topInset: numberLabel.height
                            topPadding: topInset + padding
                            placeholderText: qsTr("Engine default")
                            text: optionLoader.modelData.isSet ? formatNumber(optionLoader.modelData.value) : ''
                            // On Enter and on focus loss. The backend parses the text, so
                            // unparsable input is reported rather than silently dropped.
                            // Any submission re-notifies the options, which rebuilds these
                            // delegates with the stored values.
                            onEditingFinished: {
                                const shown = optionLoader.modelData.isSet ? formatNumber(optionLoader.modelData.value) : ''
                                if (text.trim() !== shown)
                                    Globals.BackendWrapper.analysisSetMinimizerOption(optionLoader.modelData.name, text)
                                focus = false
                            }
                            ToolTip.visible: hovered
                            ToolTip.text: optionLoader.modelData.doc
                            EaElements.Label {
                                id: numberLabel
                                text: optionLoader.modelData.name
                                color: EaStyle.Colors.themeForegroundMinor
                            }
                        }
                    }

                    Component {
                        id: enumOption
                        EaElements.ComboBox {
                            width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 2
                            topInset: enumLabel.height
                            topPadding: topInset + padding
                            model: [qsTr("Engine default")].concat(optionLoader.modelData.choices)
                            currentIndex: optionLoader.modelData.isSet ? optionLoader.modelData.choices.indexOf(optionLoader.modelData.value) + 1 : 0
                            onActivated: Globals.BackendWrapper.analysisSetMinimizerOption(
                                             optionLoader.modelData.name, currentIndex === 0 ? '' : optionLoader.modelData.choices[currentIndex - 1])
                            ToolTip.visible: hovered
                            ToolTip.text: optionLoader.modelData.doc
                            EaElements.Label {
                                id: enumLabel
                                text: optionLoader.modelData.name
                                color: EaStyle.Colors.themeForegroundMinor
                            }
                        }
                    }
                }
            }
        }

        // Bayesian DREAM controls — only visible when Bayesian is selected
        EaElements.GroupRow {
            visible: Globals.BackendWrapper.analysisIsBayesianSelected
            height: visible ? implicitHeight : 0

            EaElements.TextField {
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 5.5
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
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 5.5
                topInset: burninLabel.height
                topPadding: topInset + padding
                horizontalAlignment: TextInput.AlignLeft
                onEditingFinished: Globals.BackendWrapper.bayesianSetBurnIn(Number(text))
                text: Globals.BackendWrapper.bayesianBurnIn
                EaElements.Label {
                    id: burninLabel
                    text: qsTr("Burn-in steps")
                    color: EaStyle.Colors.themeForegroundMinor
                }
            }

            EaElements.TextField {
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 5.5
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
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 5.5
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

            EaElements.ComboBox {
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 5
                topInset: initLabel.height
                topPadding: topInset + padding
                model: Globals.BackendWrapper.bayesianInitializerOptions
                currentIndex: {
                    const options = Globals.BackendWrapper.bayesianInitializerOptions
                    const current = Globals.BackendWrapper.bayesianInitializer
                    for (let i = 0; i < options.length; i++) {
                        if (options[i] === current) return i
                    }
                    return 0
                }
                onCurrentIndexChanged: {
                    const options = Globals.BackendWrapper.bayesianInitializerOptions
                    if (currentIndex >= 0 && currentIndex < options.length) {
                        Globals.BackendWrapper.setBayesianInitializer(options[currentIndex])
                    }
                }
                EaElements.Label {
                    id: initLabel
                    text: qsTr("Initializer")
                    color: EaStyle.Colors.themeForegroundMinor
                }
            }
        }
    }
}
