// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import Gui.Globals as Globals


// Multi-selects the per-channel data files of one polarized experiment, asks the
// backend for a suggested spin-channel assignment (ORSO header or filename), and
// hands the editable rows to the channel-assignment dialog.
FileDialog {

    id: openPolarizedExperimentFilesDialog

    title: qsTr("Select one data file per spin channel")
    fileMode: FileDialog.OpenFiles
    nameFilters: [ 'Experiment files (*.dat *.txt *.ort)']

    onAccepted: {
        const paths = []
        for (let i = 0; i < selectedFiles.length; i++) {
            paths.push(selectedFiles[i].toString())
        }
        const rows = Globals.BackendWrapper.experimentSuggestPolarizedChannels(paths)
        Globals.References.pages.experiment.sidebar.basic.popups.polarizedChannelAssignmentDialog.openWith(rows)
    }

    Component.onCompleted: {
        Globals.References.pages.experiment.sidebar.basic.popups.loadPolarizedExperimentFilesDialog = openPolarizedExperimentFilesDialog
    }
}
