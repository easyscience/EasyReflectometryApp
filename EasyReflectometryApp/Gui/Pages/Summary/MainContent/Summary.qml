// 5SPDX-FileCopyrightText: 2026 EasyApp contributors
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Animations as EaAnimations
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


Rectangle {

    color: EaStyle.Colors.textViewBackground
    Behavior on color { EaAnimations.ThemeChange {} }

    // Flickable
    Flickable {
        id: flick

        anchors.fill: parent

        contentWidth: textArea.contentWidth
        contentHeight: textArea.contentHeight

        clip: true
        flickableDirection: Flickable.VerticalFlick

        ScrollBar.vertical: EaElements.ScrollBar {
            policy: ScrollBar.AsNeeded
            interactive: false
        }

        // Main text area
        EaElements.TextArea {
            id: textArea

            readOnly: true

            width: flick.width
            topPadding: 0
            bottomPadding: 0
            padding: 2.5 * EaStyle.Sizes.fontPixelSize

            textFormat: TextEdit.RichText
            text: Globals.BackendWrapper.summaryAsHtml
        }
        // Main text area

    }
    // Flickable

}
