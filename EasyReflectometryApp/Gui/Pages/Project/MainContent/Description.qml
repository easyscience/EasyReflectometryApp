// SPDX-FileCopyrightText: 2026 EasyApp contributors
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

import QtQuick
import QtQuick.Layouts

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


Rectangle {

    readonly property int commonSpacing: EaStyle.Sizes.fontPixelSize * 1.5

    color: EaStyle.Colors.mainContentBackground

    Column {

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        anchors.topMargin: commonSpacing
        anchors.leftMargin: commonSpacing * 1.5
        anchors.rightMargin: commonSpacing * 1.5

        spacing: commonSpacing

        // Project title
        // Wraps like the description below: at the minimum window size a long name (e.g. of an
        // example) is wider than the main area.
        EaElements.TextArea {
            width: parent.width
            padding: 0
            background: null
            wrapMode: TextEdit.Wrap
            font.family: EaStyle.Fonts.secondFontFamily
            font.pixelSize: EaStyle.Sizes.fontPixelSize * 3
            font.weight: Font.ExtraLight
            color: !enabled || readOnly ?
                       EaStyle.Colors.themeForegroundMinor :
                       activeFocus || titleHover.hovered ?
                           EaStyle.Colors.themeForegroundHovered :
                           EaStyle.Colors.themeForeground
            text: Globals.BackendWrapper.projectName
            // The name is one line of text: Enter finishes editing, as in TextInput.
            Keys.onReturnPressed: focus = false
            Keys.onEnterPressed: focus = false
            onEditingFinished: Globals.BackendWrapper.projectSetName(text)

            HoverHandler {
                id: titleHover
                cursorShape: Qt.IBeamCursor
            }
        }
        // Project title

        // Project info
        // A GridLayout bounded by the page width, so the value column wraps instead of running
        // past the edge of the main area (a Grid sizes each column to its widest item).
        GridLayout {
            width: parent.width
            columns: 2
            rowSpacing: 0
            columnSpacing: commonSpacing

            EaElements.Label {
                Layout.alignment: Qt.AlignTop
                font.bold: true
                text: qsTr('Description:')
            }
            // A TextArea, not EaElements.TextInput (a single-line TextField, which cannot wrap).
            // Styled as the inline TextInput: no box, no padding, same colours.
            EaElements.TextArea {
                id: descriptionField
                Layout.fillWidth: true
                padding: 0
                background: null
                wrapMode: TextEdit.Wrap
                color: !enabled || readOnly ?
                           EaStyle.Colors.themeForegroundMinor :
                           activeFocus || descriptionHover.hovered ?
                               EaStyle.Colors.themeForegroundHovered :
                               EaStyle.Colors.themeForeground
                text: Globals.BackendWrapper.projectDescription
                // The description is one paragraph: Enter finishes editing, as in TextInput.
                Keys.onReturnPressed: focus = false
                Keys.onEnterPressed: focus = false
                onEditingFinished: Globals.BackendWrapper.projectSetDescription(text)

                HoverHandler {
                    id: descriptionHover
                    cursorShape: Qt.IBeamCursor
                }
            }

            EaElements.Label {
                Layout.alignment: Qt.AlignTop
                font.bold: true
                text: qsTr('Location:')
            }
            EaElements.Label {
                Layout.fillWidth: true
                // Paths have no spaces to break at, so fall back to breaking anywhere.
                wrapMode: Text.WrapAtWordBoundaryOrAnywhere
                // An example is not on disk anywhere of the user's until it is created.
                text: Globals.BackendWrapper.projectIsExample ?
                          qsTr('Example, not saved. Use "Create a new project" to keep your work.') :
                          Globals.BackendWrapper.projectLocation
            }

            EaElements.Label {
                visible: !Globals.BackendWrapper.projectIsExample
                font.bold: true
                text: qsTr('Created:')
            }
            EaElements.Label {
                Layout.fillWidth: true
                visible: !Globals.BackendWrapper.projectIsExample
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
