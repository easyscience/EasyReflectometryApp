// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui as Gui
import Gui.Globals as Globals


// Per-layer magnetism of the current assembly: a magnetic layer carries a
// magnetic SLD (ρM) and an in-plane moment angle (θM), both fittable and
// visible in the Analysis parameter table once the layer is magnetic.
// Only refl1d can model magnetism, so the whole group is disabled otherwise.
EaElements.GroupBox {
    id: magnetismGroup

    title: qsTr("Magnetism: " + Globals.BackendWrapper.sampleCurrentAssemblyName)
    collapsible: true
    collapsed: true

    readonly property bool supported: Globals.BackendWrapper.sampleMagnetismSupported
    readonly property string magneticEngine: {
        const engines = Globals.BackendWrapper.sampleCalculationEnginesSupportingMagnetism
        return engines.length > 0 ? engines[0] : ''
    }
    property string errorMessage: ''

    // The row the table has selected; null while the selection outruns the list.
    readonly property var currentRow:
        Globals.BackendWrapper.sampleLayersMagnetism[Globals.BackendWrapper.sampleCurrentLayerIndex] ?? null

    EaElements.GroupColumn {

        EaElements.Label {
            visible: !magnetismGroup.supported && magnetismGroup.magneticEngine !== ''
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
            text: qsTr("Magnetic layers are modelled by %1. Ticking 'Magn.' offers to switch this project to it.")
                  .arg(magnetismGroup.magneticEngine)
        }

        EaElements.Label {
            visible: !magnetismGroup.supported && magnetismGroup.magneticEngine === ''
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
            text: qsTr("None of the available calculation engines can model magnetic layers.")
        }

        EaComponents.TableView {
            id: magnetismView
            // Not disabled when the engine cannot model magnetism: ticking
            // 'Magn.' is how the user asks for the engine that can.
            enabled: magnetismGroup.supported || magnetismGroup.magneticEngine !== ''
            tallRows: false
            defaultInfoText: qsTr("No Layers Added")
            model: Globals.BackendWrapper.sampleLayersMagnetism.length

            header: EaComponents.TableViewHeader {
                EaComponents.TableViewLabel {
                    id: noLabel
                    text: qsTr('No.')
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                }

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.sideBarContentWidth - (noLabel.width + rhoLabel.width + thetaLabel.width + magneticLabel.width + 5 * EaStyle.Sizes.tableColumnSpacing)
                    horizontalAlignment: Text.AlignLeft
                    text: qsTr('Layer')
                }

                EaComponents.TableViewLabel {
                    id: rhoLabel
                    text: qsTr('ρM/10⁻⁶Å⁻²')
                    width: EaStyle.Sizes.fontPixelSize * 9.0
                }

                EaComponents.TableViewLabel {
                    id: thetaLabel
                    text: qsTr('θM/°')
                    width: EaStyle.Sizes.fontPixelSize * 7.0
                }

                EaComponents.TableViewLabel {
                    id: magneticLabel
                    text: qsTr('Magn.')
                    width: EaStyle.Sizes.fontPixelSize * 4.0
                }
            }

            delegate: EaComponents.TableViewDelegate {
                // Guard every access: the row model length and the backing list
                // are refreshed by separate signals, so a delegate can outlive
                // its row for one frame after a layer is removed.
                readonly property var rowData: Globals.BackendWrapper.sampleLayersMagnetism[index] ?? null
                readonly property bool rowIsMagnetic: rowData !== null && rowData.magnetic === "True"

                EaComponents.TableViewLabel {
                    color: EaStyle.Colors.themeForegroundMinor
                    text: index + 1
                }

                EaComponents.TableViewLabel {
                    horizontalAlignment: Text.AlignLeft
                    text: rowData ? rowData.label : ''
                }

                EaComponents.TableViewTextInput {
                    horizontalAlignment: Text.AlignHCenter
                    // A layer coupled to its material shows the material's ρM.
                    enabled: rowIsMagnetic && rowData.rho_m_coupled !== "True"
                    ToolTip.text: rowData && rowData.rho_m_coupled === "True" ?
                                      qsTr("Taken from the material's moment — untick 'ρM from material' below to edit") : ''
                    text: rowData ? Number(rowData.rho_m).toFixed(3) : '--'
                    onEditingFinished: Globals.BackendWrapper.sampleSetLayerRhoMAtIndex(index, text)
                }

                EaComponents.TableViewTextInput {
                    horizontalAlignment: Text.AlignHCenter
                    enabled: rowIsMagnetic
                    text: rowData ? Number(rowData.theta_m).toFixed(2) : '--'
                    onEditingFinished: Globals.BackendWrapper.sampleSetLayerThetaMAtIndex(index, text)
                }

                EaComponents.TableViewCheckBox {
                    checked: rowIsMagnetic
                    ToolTip.text: magnetismGroup.supported ?
                                      qsTr("Make this layer magnetic") :
                                      qsTr("Make this layer magnetic (asks to switch the calculation engine)")
                    onToggled: {
                        magnetismGroup.errorMessage = ''
                        Globals.BackendWrapper.sampleSetLayerMagneticAtIndex(index, checked)
                        // The click already moved the box; the backend may ask
                        // first (engine switch) or refuse, so follow its state.
                        checked = Qt.binding(function () { return rowIsMagnetic })
                    }
                }

                mouseArea.onPressed: {
                    if (Globals.BackendWrapper.sampleCurrentLayerIndex !== index) {
                        Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                    }
                }
            }
        }

        // The selected row's angle as a slider: the same number the θM column
        // holds, and the arrow the Structure view draws, side by side. Follows
        // the selection the table already writes - no second "focused row".
        Gui.MagnetizationAngleSlider {
            visible: magnetismGroup.currentRow !== null && magnetismGroup.currentRow.magnetic === "True"
            height: visible ? implicitHeight : 0
            phi: visible ? Number(magnetismGroup.currentRow.phi) : 0
            thetaM: visible ? Number(magnetismGroup.currentRow.theta_m) : 0
            hasMoment: visible && Number(magnetismGroup.currentRow.rho_m) !== 0
            // A constrained θM follows its expression, and a running fit owns
            // every parameter: in both cases the slider is read-only.
            editable: visible && magnetismGroup.currentRow.editable === "True"
                      && !Globals.BackendWrapper.analysisFittingRunning
            onThetaMRequested: (thetaM) => Globals.BackendWrapper.sampleSetLayerThetaMAtIndex(
                                               Globals.BackendWrapper.sampleCurrentLayerIndex, thetaM)
        }

        // The selected row's ρM from its material's moment (a magnetic
        // material, see the Materials group); the layer keeps its own θM.
        EaElements.CheckBox {
            readonly property bool coupled: magnetismGroup.currentRow !== null
                                            && magnetismGroup.currentRow.rho_m_coupled === "True"
            visible: magnetismGroup.currentRow !== null
                     && magnetismGroup.currentRow.magnetic === "True"
                     && magnetismGroup.currentRow.material_magnetic === "True"
            topPadding: 0
            text: qsTr("ρM from material")
            ToolTip.text: qsTr("Take ρM from the moment of this layer's magnetic material. Unticking keeps the current value.")
            checked: coupled
            onToggled: {
                Globals.BackendWrapper.sampleSetLayerRhoMCoupledAtIndex(
                            Globals.BackendWrapper.sampleCurrentLayerIndex, checked)
                checked = Qt.binding(function () { return coupled })
            }
        }

        // The current model's field (refl1d's Aguide and H); both can be fitted.
        // Shown only while the field acts: on a magnetic model under an engine
        // that models magnetism, as in the Analysis parameter table.
        Row {
            visible: magnetismGroup.supported && Globals.BackendWrapper.sampleMagneticField.model_magnetic === true
            spacing: EaStyle.Sizes.fontPixelSize

            EaElements.TextField {
                id: guideFieldAngleField
                width: (EaStyle.Sizes.sideBarContentWidth - parent.spacing) / 2
                topInset: guideFieldAngleLabel.height
                topPadding: topInset + padding
                horizontalAlignment: TextInput.AlignLeft
                ToolTip.text: qsTr("Angle of the field about the beam axis: 270° (or −90°) in the sample plane, 90° in the plane but reversed, 0° or 180° along the surface normal.")
                text: Number(Globals.BackendWrapper.sampleMagneticField.guide_field_angle).toFixed(1)
                onEditingFinished: {
                    Globals.BackendWrapper.sampleSetGuideFieldAngle(text)
                    text = Qt.binding(function () {
                        return Number(Globals.BackendWrapper.sampleMagneticField.guide_field_angle).toFixed(1)
                    })
                }
                EaElements.Label {
                    id: guideFieldAngleLabel
                    text: qsTr('Guide field angle (°)')
                }
            }

            EaElements.TextField {
                width: guideFieldAngleField.width
                topInset: appliedFieldLabel.height
                topPadding: topInset + padding
                horizontalAlignment: TextInput.AlignLeft
                ToolTip.text: qsTr("Applied field in tesla. It adds a Zeeman term along the field, so its effect depends on the field and its direction relative to the moments.")
                text: Number(Globals.BackendWrapper.sampleMagneticField.applied_field).toFixed(3)
                onEditingFinished: {
                    Globals.BackendWrapper.sampleSetAppliedField(text)
                    text = Qt.binding(function () {
                        return Number(Globals.BackendWrapper.sampleMagneticField.applied_field).toFixed(3)
                    })
                }
                EaElements.Label {
                    id: appliedFieldLabel
                    text: qsTr('Applied field (T)')
                }
            }
        }

        EaElements.Label {
            visible: magnetismGroup.supported
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
            text: qsTr("With the in-plane guide field at 270°, θM = 270° aligns the moment with the field, giving no spin-flip.\nρM, θM and the field appear in the Analysis parameter table and can be fitted.")
        }

        EaElements.Label {
            visible: magnetismGroup.errorMessage !== ''
            color: EaStyle.Colors.red
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
            text: magnetismGroup.errorMessage
        }
    }

    // The backend refuses to attach magnetism on a calculator that cannot model
    // it; show the reason rather than leaving the checkbox silently unchanged.
    Connections {
        target: Globals.BackendWrapper.activeBackend ? Globals.BackendWrapper.activeBackend.sample : null
        enabled: target !== null
        ignoreUnknownSignals: true
        function onMagnetismFailed(message) {
            magnetismGroup.errorMessage = message
        }
        // Magnetism needs another engine: ask before changing a project-wide
        // setting that also invalidates the current fit.
        function onMagnetismNeedsEngine(index, engine) {
            engineSwitchDialog.layerIndex = index
            engineSwitchDialog.engine = engine
            engineSwitchDialog.open()
        }
    }

    EaElements.Dialog {
        id: engineSwitchDialog

        property int layerIndex: -1
        property string engine: ''

        title: qsTr("Switch calculation engine?")
        standardButtons: Dialog.Ok | Dialog.Cancel
        closePolicy: Popup.CloseOnEscape

        onAccepted: {
            Globals.BackendWrapper.sampleEnableMagnetismWithEngineAtIndex(layerIndex, engine)
            layerIndex = -1
        }
        onRejected: layerIndex = -1

        Column {
            spacing: EaStyle.Sizes.fontPixelSize * 0.5

            EaElements.Label {
                wrapMode: Text.WordWrap
                width: EaStyle.Sizes.fontPixelSize * 26
                text: qsTr("Magnetic layers can only be modelled by %1, and this project uses %2.")
                      .arg(engineSwitchDialog.engine)
                      .arg(Globals.BackendWrapper.sampleCalculationEngines[
                               Globals.BackendWrapper.sampleCalculationEngineIndex] ?? '')
            }

            EaElements.Label {
                wrapMode: Text.WordWrap
                width: EaStyle.Sizes.fontPixelSize * 26
                text: qsTr("Switching changes the calculation engine: reflectivity is recalculated and any fit results become stale. The sample and the data are unaffected, and the engine can be changed back once no layer is magnetic.")
            }
        }
    }
}
