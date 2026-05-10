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

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: EaStyle.Sizes.fontPixelSize
        spacing: EaStyle.Sizes.fontPixelSize

        RowLayout {
            Layout.fillWidth: true
            visible: Globals.BackendWrapper.bayesianTracePlotUrl !== ''

            EaElements.Label {
                Layout.fillWidth: true
                text: qsTr("MCMC Chain Trace Plots")
                font: EaStyle.Fonts.headingFont
            }

            EaElements.Button {
                text: qsTr("Save")
                onClicked: Globals.BackendWrapper.bayesianSavePlot(
                    Globals.BackendWrapper.bayesianTracePlotUrl
                )
            }
        }

        Image {
            id: traceImage
            Layout.fillWidth: true
            Layout.fillHeight: true
            fillMode: Image.PreserveAspectFit
            source: Globals.BackendWrapper.bayesianTracePlotUrl || ''
            cache: false
            visible: source !== ''

            BusyIndicator {
                anchors.centerIn: parent
                running: traceImage.source === '' && Globals.BackendWrapper.bayesianResultAvailable
            }
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

        // Placeholder: results available but no plot rendered yet
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            visible: Globals.BackendWrapper.bayesianTracePlotUrl === ''
                     && Globals.BackendWrapper.bayesianResultAvailable

            ColumnLayout {
                anchors.centerIn: parent
                spacing: EaStyle.Sizes.fontPixelSize

                EaElements.Label {
                    Layout.fillWidth: true
                    text: qsTr("Trace plots are being rendered…")
                    color: EaStyle.Colors.themeForegroundMinor
                    horizontalAlignment: Text.AlignHCenter
                }

                EaElements.Label {
                    Layout.fillWidth: true
                    text: qsTr("Trace plots require the <tt>arviz</tt> library. Install it with:<br>"
                                + "<tt>pip install easyreflectometry[bayesian]</tt>")
                    color: EaStyle.Colors.themeForegroundMinor
                    wrapMode: Text.WordWrap
                    horizontalAlignment: Text.AlignHCenter
                    font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.9
                }
            }
        }
    }
}
