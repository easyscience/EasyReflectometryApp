// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

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
    title: qsTr("Refinement Results")
    standardButtons: Dialog.Ok
    closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

    onAccepted: {
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
            text: "Num. refined parameters: " + Globals.BackendWrapper.analysisFitNumRefinedParams
        }

        EaElements.Label {
            text: "Chi2: " + Globals.BackendWrapper.analysisFitChi2.toFixed(4)
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
