// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


// Editable file → spin-channel assignment for one polarized experiment.
// Rows come pre-filled from the backend detection (ORSO header or filename
// tokens); the user can adjust each channel or exclude a file ("not used").
EaElements.Dialog {
    id: dialog

    title: qsTr("Assign spin channels")
    standardButtons: Dialog.Ok | Dialog.Cancel
    closePolicy: Popup.CloseOnEscape

    // Rows: [{path, name, channel}] — channel is '' when the file is not used.
    property var assignmentRows: []
    // Incremented on every edit so we can re-evaluate validation bindings.
    property int editRevision: 0

    readonly property var channelValues: ['', 'pp', 'pm', 'mp', 'mm']
    readonly property var channelTexts: [qsTr('not used'), 'pp  ↑↑', 'pm  ↑↓', 'mp  ↓↑', 'mm  ↓↓']

    readonly property bool hasAssignment: {
        editRevision  // dependency
        for (let i = 0; i < assignmentRows.length; i++) {
            if (assignmentRows[i].channel !== '') return true
        }
        return false
    }

    readonly property bool hasDuplicates: {
        editRevision  // dependency
        const seen = {}
        for (let i = 0; i < assignmentRows.length; i++) {
            const channel = assignmentRows[i].channel
            if (channel === '') continue
            if (seen[channel]) return true
            seen[channel] = true
        }
        return false
    }

    readonly property bool isValid: hasAssignment && !hasDuplicates

    // Keep the OK button disabled while the assignment is invalid, so the
    // dialog can never be accepted into a no-op that just closes it.
    function updateOkEnabled() {
        const okButton = standardButton(Dialog.Ok)
        if (okButton) {
            okButton.enabled = isValid
        }
    }

    onIsValidChanged: updateOkEnabled()
    // The footer buttons only exist once the dialog is shown.
    onOpened: updateOkEnabled()

    // Message from a backend rejection.
    property string loadError: ''

    function openWith(rows) {
        assignmentRows = rows
        loadError = ''
        editRevision += 1
        updateOkEnabled()
        open()
    }

    onAccepted: {
        // OK is disabled while invalid. The backend
        // validates the rows again before loading anything.
        if (!isValid) {
            assignmentRows = []
            return
        }
        const error = Globals.BackendWrapper.experimentLoadPolarized(assignmentRows)
        if (error) {
            // Keep the rows and reopen with the reason, so the user can fix the
            // assignment instead of losing it to a dialog that just closed.
            loadError = error
            open()
            return
        }
        loadError = ''
        assignmentRows = []
    }

    onRejected: {
        assignmentRows = []
        loadError = ''
    }

    Component.onCompleted: {
        Globals.References.pages.experiment.sidebar.basic.popups.polarizedChannelAssignmentDialog = dialog
    }

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        EaElements.Label {
            text: qsTr("One file per spin channel. Channels were pre-assigned from the\nORSO header or the file name. Adjust them if needed.\nAny number of channels may be assigned (a single one is allowed);\nfiles set to 'not used' are ignored.")
        }

        EaElements.Label {
            // Polarized data loads and displays in any engine, but the
            // calculated cross-sections need magnetism: say so here rather
            // than leaving the user to wonder why only one channel is fitted.
            visible: !Globals.BackendWrapper.sampleMagnetismSupported
                     && Globals.BackendWrapper.sampleCalculationEnginesSupportingMagnetism.length > 0
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.fontPixelSize * 28
            text: qsTr("Note: the channels will be loaded and displayed, but modelling them needs a magnetic sample, which only %1 can calculate. Switch the calculation engine on the Sample page when you get there.")
                  .arg(Globals.BackendWrapper.sampleCalculationEnginesSupportingMagnetism.join(', '))
        }

        EaElements.Label {
            // Model.resolution_function is per experiment.
            color: EaStyle.Colors.themeForegroundMinor
            text: qsTr("Note: one resolution function is used for the whole experiment,\ntaken from the first assigned channel. Differing per-channel\nresolution metadata in the other files is ignored.")
        }

        Repeater {
            model: dialog.assignmentRows.length

            delegate: Row {
                id: rowDelegate

                property int rowIndex: index

                spacing: EaStyle.Sizes.fontPixelSize

                EaElements.Label {
                    width: EaStyle.Sizes.fontPixelSize * 18
                    anchors.verticalCenter: parent.verticalCenter
                    elide: Text.ElideLeft
                    text: dialog.assignmentRows[rowDelegate.rowIndex].name
                    ToolTip.text: dialog.assignmentRows[rowDelegate.rowIndex].path
                }

                EaElements.ComboBox {
                    width: EaStyle.Sizes.fontPixelSize * 8
                    model: dialog.channelTexts
                    currentIndex: dialog.channelValues.indexOf(dialog.assignmentRows[rowDelegate.rowIndex].channel)
                    onActivated: {
                        dialog.assignmentRows[rowDelegate.rowIndex].channel = dialog.channelValues[currentIndex]
                        dialog.editRevision += 1
                    }
                }
            }
        }

        EaElements.Label {
            visible: dialog.hasDuplicates
            color: EaStyle.Colors.red
            text: qsTr("Each spin channel may be assigned to only one file.")
        }

        EaElements.Label {
            visible: !dialog.hasAssignment
            color: EaStyle.Colors.red
            text: qsTr("Assign at least one file to a spin channel.")
        }

        EaElements.Label {
            visible: dialog.loadError !== ''
            color: EaStyle.Colors.red
            wrapMode: Text.WordWrap
            width: EaStyle.Sizes.fontPixelSize * 28
            text: dialog.loadError
        }
    }
}
