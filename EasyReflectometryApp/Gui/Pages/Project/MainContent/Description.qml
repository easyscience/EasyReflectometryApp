// 5SPDX-FileCopyrightText: 2025 EasyApp contributors
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

import QtQuick

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements

import Gui.Globals as Globals


Rectangle {

    readonly property int commonSpacing: EaStyle.Sizes.fontPixelSize * 1.5

    color: EaStyle.Colors.mainContentBackground

    Column {

        anchors.top: parent.top
        anchors.left: parent.left

        anchors.topMargin: commonSpacing
        anchors.leftMargin: commonSpacing * 1.5

        spacing: commonSpacing

        // Project title
        EaElements.TextInput {
            font.family: EaStyle.Fonts.secondFontFamily
            font.pixelSize: EaStyle.Sizes.fontPixelSize * 3
            font.weight: Font.ExtraLight
            text: Globals.BackendWrapper.projectName
            onEditingFinished: Globals.BackendWrapper.projectSetName(text)
        }
        // Project title

        // Project info
        Grid {
            columns: 2
            rowSpacing: 0
            columnSpacing: commonSpacing

            EaElements.Label {
                font.bold: true
                text: qsTr('Description:')
            }
            EaElements.TextInput {
                text: Globals.BackendWrapper.projectDescription
                onEditingFinished: Globals.BackendWrapper.projectSetDescription(text)
            }

            EaElements.Label {
                font.bold: true
                text: qsTr('Location:')
            }
            EaElements.Label {
                text: Globals.BackendWrapper.projectLocation
            }

            EaElements.Label {
                font.bold: true
                text: qsTr('Created:')
            }
            EaElements.Label {
                text: Globals.BackendWrapper.projectCreationDate
            }
        }
        // Project info

        // Project image
        Image {
            width: EaStyle.Sizes.fontPixelSize * 25
            fillMode: Image.PreserveAspectFit
        }
        // Project image

    }

}
