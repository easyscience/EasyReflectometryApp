// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents
import EasyApp.Gui.Logic as EaLogic

import Gui.Globals as Globals


EaElements.GroupBox {
    collapsible: false
    last: true

    EaElements.ComboBox {
        id: comboBox

        topInset: 0
        bottomInset: 0

        width: EaStyle.Sizes.sideBarContentWidth
        anchors.bottomMargin: EaStyle.Sizes.fontPixelSize

        textRole: "name"

        model: Globals.BackendWrapper.analysisExperimentsAvailable.length
        currentIndex: Globals.BackendWrapper.analysisExperimentsCurrentIndex
        onActivated: Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(currentIndex)

        // ComboBox delegate (popup rows)
        delegate: ItemDelegate {
            id: itemDelegate

            width: parent.width
            height: EaStyle.Sizes.tableRowHeight

            highlighted: comboBox.highlightedIndex === index

            // ComboBox delegate (popup rows) contentItem
            contentItem: Item {
                width: parent.width
                height: parent.height

                Row {
                    height: parent.height
                    spacing: EaStyle.Sizes.tableColumnSpacing

                    EaComponents.TableViewLabel {
                        text: index + 1
                        color: EaStyle.Colors.themeForegroundMinor
                    }

                    EaComponents.TableViewButton {
                        anchors.verticalCenter: parent.verticalCenter
                        fontIcon: "microscope"
                        ToolTip.text: qsTr("Measured pattern color")
                        backgroundColor: "transparent"
                        borderColor: "transparent"
                        iconColor: EaStyle.Colors.chartForegroundsExtra[2]
                    }

                    EaComponents.TableViewParameter {
                        enabled: false
                        //text: comboBox.model[index]//.name.value
                        text: Globals.BackendWrapper.analysisExperimentsAvailable[index]

                    }
                }
            }
            // ComboBox delegate (popup rows) contentItem

            // ComboBox delegate (popup rows) background
            background: Rectangle {
                color: itemDelegate.highlighted ?
                        EaStyle.Colors.tableHighlight :
                        index % 2 ?
                            EaStyle.Colors.themeBackgroundHovered2 :
                            EaStyle.Colors.themeBackgroundHovered1
            }
            // ComboBox delegate (popup rows) background

        }
        // ComboBox delegate (popup rows)

        // ComboBox (selected item) contentItem
        contentItem: Item {
            width: parent.width
            height: parent.height

            Row {
                height: parent.height
                spacing: EaStyle.Sizes.tableColumnSpacing

                EaComponents.TableViewLabel {
                    text: comboBox.currentIndex + 1
                    color: EaStyle.Colors.themeForegroundMinor
                }

                EaComponents.TableViewButton {
                    anchors.verticalCenter: parent.verticalCenter
                    fontIcon: "microscope"
                    ToolTip.text: qsTr("Measured pattern color")
                    backgroundColor: "transparent"
                    borderColor: "transparent"
                    iconColor: EaStyle.Colors.chartForegroundsExtra[2]
                }

                EaComponents.TableViewParameter {
                    enabled: false
                    text: typeof comboBox.model[comboBox.currentIndex] !== 'undefined' ?
                        comboBox.model[comboBox.currentIndex].name.value :
                        ''
                }
            }
        }
        // ComboBox (selected item) contentItem
    }
}
