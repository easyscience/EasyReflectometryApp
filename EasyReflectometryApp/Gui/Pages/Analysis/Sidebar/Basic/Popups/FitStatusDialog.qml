// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements

import Gui.Globals as Globals


EaElements.Dialog {
    id: dialog

    visible: Globals.BackendWrapper.analysisShowFitResultsDialog
    title: Globals.BackendWrapper.analysisFitSuccess ? qsTr("Refinement Results") : qsTr("Refinement Failed")
    standardButtons: Dialog.Ok
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    onAccepted: {
        Globals.BackendWrapper.analysisSetShowFitResultsDialog(false)
    }

    onRejected: {
        Globals.BackendWrapper.analysisSetShowFitResultsDialog(false)
    }

    onClosed: {
        Globals.BackendWrapper.analysisSetShowFitResultsDialog(false)
    }

    Component.onCompleted: Globals.References.pages.analysis.sidebar.basic.popups.fitStatusDialogOkButton = okButtonRef()

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        EaElements.Label {
            text: "Success: " + Globals.BackendWrapper.analysisFitSuccess
        }

        EaElements.Label {
            visible: Globals.BackendWrapper.analysisFitSuccess
            text: "Num. refined parameters: " + Globals.BackendWrapper.analysisFitNumRefinedParams
        }

        EaElements.Label {
            visible: Globals.BackendWrapper.analysisFitSuccess
            text: "Reduced Chi2: " + Globals.BackendWrapper.analysisFitChi2.toFixed(4)
        }

        EaElements.Label {
            visible: !Globals.BackendWrapper.analysisFitSuccess && Globals.BackendWrapper.analysisFitErrorMessage !== ""
            text: "Error: " + Globals.BackendWrapper.analysisFitErrorMessage
            wrapMode: Text.WordWrap
            width: Math.min(implicitWidth, EaStyle.Sizes.sideBarContentWidth * 1.5)
            color: EaStyle.Colors.red
        }
    }

    // Logic

    function okButtonRef() {
        const buttons = dialog.footer.contentModel.children
        for (let i in buttons) {
            const button = buttons[i]
            if (button.text === 'OK') {
                return button
            }
        }
        return null
    }
}
