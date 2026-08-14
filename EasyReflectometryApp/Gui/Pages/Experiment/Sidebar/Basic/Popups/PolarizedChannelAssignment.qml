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
    // Bumped on every edit so validation bindings re-evaluate.
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

    function openWith(rows) {
        assignmentRows = rows
        editRevision += 1
        open()
    }

    onAccepted: {
        if (hasAssignment && !hasDuplicates) {
            Globals.BackendWrapper.experimentLoadPolarized(assignmentRows)
        }
        assignmentRows = []
    }

    onRejected: assignmentRows = []

    Component.onCompleted: {
        Globals.References.pages.experiment.sidebar.basic.popups.polarizedChannelAssignmentDialog = dialog
    }

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        EaElements.Label {
            text: qsTr("One file per spin channel. Channels were pre-assigned from the\nORSO header or the file name — adjust them if needed.")
        }

        Repeater {
            model: dialog.assignmentRows.length

            delegate: Row {
                spacing: EaStyle.Sizes.fontPixelSize

                EaElements.Label {
                    width: EaStyle.Sizes.fontPixelSize * 18
                    anchors.verticalCenter: parent.verticalCenter
                    elide: Text.ElideLeft
                    text: dialog.assignmentRows[index].name
                    ToolTip.text: dialog.assignmentRows[index].path
                }

                EaElements.ComboBox {
                    width: EaStyle.Sizes.fontPixelSize * 8
                    model: dialog.channelTexts
                    currentIndex: dialog.channelValues.indexOf(dialog.assignmentRows[index].channel)
                    onActivated: {
                        dialog.assignmentRows[index].channel = dialog.channelValues[currentIndex]
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
    }
}
