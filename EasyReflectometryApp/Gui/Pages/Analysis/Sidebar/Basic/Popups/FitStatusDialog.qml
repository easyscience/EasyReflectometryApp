// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements

import Gui.Globals as Globals


EaElements.Dialog {
    id: dialog

    visible: Globals.BackendWrapper.analysisFittingStatus
    title: qsTr("Fit status")
    standardButtons: Dialog.Ok

    Component.onCompleted: Globals.References.pages.analysis.sidebar.basic.popups.fitStatusDialogOkButton = okButtonRef()

    EaElements.Label {
        text: {
            if ( Globals.BackendWrapper.analysisFittingStatus === 'Success') {
                return 'Optimization finished successfully.'
            } else if (Globals.BackendWrapper.analysisFittingStatus === 'Failure') {
                return 'Optimization failed.'
            } else if (Globals.BackendWrapper.analysisFittingStatus  === 'Aborted') {
                return 'Optimization aborted.'
            } else if (Globals.BackendWrapper.analysisFittingStatus  === 'No free params') {
                return 'Nothing to vary. Allow some parameters to be free.'
            } else {
                return ''
            }
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
