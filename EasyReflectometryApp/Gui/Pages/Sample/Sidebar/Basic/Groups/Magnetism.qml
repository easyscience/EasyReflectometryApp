// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

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
    property string errorMessage: ''

    EaElements.GroupColumn {

        EaElements.Label {
            visible: !magnetismGroup.supported
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
            text: qsTr("The current calculation engine cannot model magnetic layers.\nSelect refl1d on the Analysis page to enable magnetism.")
        }

        EaComponents.TableView {
            id: magnetismView
            enabled: magnetismGroup.supported
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
                    enabled: rowIsMagnetic
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
                    ToolTip.text: qsTr("Make this layer magnetic")
                    onToggled: {
                        magnetismGroup.errorMessage = ''
                        Globals.BackendWrapper.sampleSetLayerMagneticAtIndex(index, checked)
                    }
                }

                mouseArea.onPressed: {
                    if (Globals.BackendWrapper.sampleCurrentLayerIndex !== index) {
                        Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                    }
                }
            }
        }

        EaElements.Label {
            visible: magnetismGroup.supported
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
            text: qsTr("θM = 270° aligns the moment with the guide field, giving no spin-flip.\nρM and θM appear in the Analysis parameter table and can be fitted.")
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
    }
}
