// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


Rectangle {
    id: container

    color: EaStyle.Colors.chartBackground

    Flickable {
        anchors.fill: parent
        anchors.margins: EaStyle.Sizes.fontPixelSize
        contentHeight: diagColumn.implicitHeight + EaStyle.Sizes.fontPixelSize * 2
        clip: true

        ColumnLayout {
            id: diagColumn
            width: parent.width
            spacing: EaStyle.Sizes.fontPixelSize

            EaElements.Label {
                Layout.fillWidth: true
                text: qsTr("MCMC Convergence Diagnostics")
                font: EaStyle.Fonts.headingFont
                visible: Globals.BackendWrapper.bayesianResultAvailable
            }

            // Placeholder: no results available
            Item {
                Layout.fillWidth: true
                Layout.fillHeight: true
                visible: !Globals.BackendWrapper.bayesianResultAvailable

                EaElements.Label {
                    anchors.centerIn: parent
                    text: qsTr("No Bayesian results available.")
                    color: EaStyle.Colors.themeForegroundMinor
                }
            }

            // Sampling configuration
            EaElements.GroupBox {
                title: qsTr("Sampling Configuration")
                visible: Globals.BackendWrapper.bayesianResultAvailable
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Repeater {
                        model: [
                            { label: qsTr("Requested samples"), key: "samples" },
                            { label: qsTr("Burn-in steps"), key: "burnIn" },
                            { label: qsTr("Thinning"), key: "thin" },
                            { label: qsTr("Population (chains)"), key: "population" },
                            { label: qsTr("Retained draws"), key: "nDraws" },
                            { label: qsTr("Parameters"), key: "nParams" },
                        ]

                        delegate: RowLayout {
                            Layout.fillWidth: true
                            EaElements.Label {
                                text: modelData.label
                                Layout.fillWidth: true
                                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                            }
                            EaElements.Label {
                                text: {
                                    var diag = Globals.BackendWrapper.bayesianDiagnostics
                                    return diag && diag[modelData.key] !== undefined
                                        ? diag[modelData.key] : '—'
                                }
                                font.bold: true
                                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                            }
                        }
                    }
                }
            }

            // Acceptance rate
            EaElements.GroupBox {
                title: qsTr("Acceptance Rate")
                visible: Globals.BackendWrapper.bayesianResultAvailable
                         && Globals.BackendWrapper.bayesianDiagnostics.acceptanceRate !== undefined
                Layout.fillWidth: true

                EaElements.Label {
                    text: {
                        var rate = Globals.BackendWrapper.bayesianDiagnostics.acceptanceRate
                        return rate !== undefined ? (rate * 100).toFixed(1) + '%' : '—'
                    }
                    font.bold: true
                }
            }

            // Gelman-Rubin R-hat
            EaElements.GroupBox {
                title: qsTr("Gelman-Rubin R̂ (Convergence)")
                visible: Globals.BackendWrapper.bayesianResultAvailable
                         && Globals.BackendWrapper.bayesianDiagnostics.rhat !== undefined
                Layout.fillWidth: true

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2

                    Repeater {
                        model: {
                            var diag = Globals.BackendWrapper.bayesianDiagnostics
                            return diag && diag.rhat ? Object.keys(diag.rhat) : []
                        }

                        delegate: RowLayout {
                            Layout.fillWidth: true
                            EaElements.Label {
                                text: modelData
                                Layout.fillWidth: true
                                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                            }
                            EaElements.Label {
                                text: {
                                    var diag = Globals.BackendWrapper.bayesianDiagnostics
                                    return diag && diag.rhat && diag.rhat[modelData] !== undefined
                                        ? diag.rhat[modelData].toFixed(4) : '—'
                                }
                                font.bold: true
                                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                                color: {
                                    var diag = Globals.BackendWrapper.bayesianDiagnostics
                                    if (diag && diag.rhat && diag.rhat[modelData] !== undefined) {
                                        return diag.rhat[modelData] < 1.1
                                            ? (EaStyle.Colors.themeAccent || "#27ae60")
                                            : (EaStyle.Colors.warning || "#e67e22")
                                    }
                                    return EaStyle.Colors.themeForegroundMinor
                                }
                            }
                        }
                    }
                }
            }

            EaElements.GroupBox {
                title: qsTr("Gelman-Rubin R̂ (Convergence)")
                visible: Globals.BackendWrapper.bayesianResultAvailable
                         && Globals.BackendWrapper.bayesianDiagnostics.rhat === undefined
                         && Globals.BackendWrapper.bayesianDiagnostics.rhatStatus !== undefined
                Layout.fillWidth: true

                EaElements.Label {
                    text: {
                        var diag = Globals.BackendWrapper.bayesianDiagnostics
                        return diag && diag.rhatStatus !== undefined ? String(diag.rhatStatus) : ''
                    }
                    color: EaStyle.Colors.themeForegroundMinor
                    wrapMode: Text.WordWrap
                }
            }
        }
    }
}
