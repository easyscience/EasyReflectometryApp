// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


// "Save" button for a rendered Bayesian plot: asks for a destination, then
// lets the backend copy the plot file there.
EaElements.Button {
    id: saveButton

    // file:// URL of the rendered plot (may carry a ?t=<timestamp> query)
    property string sourceUrl: ''

    text: qsTr('Save')

    onClicked: {
        const isHtml = sourceUrl.split('?')[0].toLowerCase().endsWith('.html')
        saveFileDialog.nameFilters = isHtml ? [qsTr('HTML Files (*.html)')] : [qsTr('PNG Images (*.png)')]
        saveFileDialog.defaultSuffix = isHtml ? 'html' : 'png'
        const suggested = Globals.BackendWrapper.bayesianPlotSuggestedFileUrl(sourceUrl)
        if (suggested)
            saveFileDialog.selectedFile = suggested
        saveFileDialog.open()
    }

    FileDialog {
        id: saveFileDialog
        title: qsTr('Save Bayesian plot')
        fileMode: FileDialog.SaveFile
        onAccepted: {
            if (!Globals.BackendWrapper.bayesianSavePlot(saveButton.sourceUrl, selectedFile.toString()))
                saveErrorDialog.open()
        }
    }

    EaElements.Dialog {
        id: saveErrorDialog
        title: qsTr('Save Error')
        standardButtons: Dialog.Ok
        modal: true
        closePolicy: Popup.CloseOnEscape | Popup.CloseOnPressOutside

        EaElements.Label {
            text: qsTr('The plot could not be saved. See the log for details.')
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.sideBarContentWidth
        }
    }
}
