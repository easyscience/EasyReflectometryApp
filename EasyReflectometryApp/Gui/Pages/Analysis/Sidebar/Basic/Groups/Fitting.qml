// SPDX-FileCopyrightText: 2025 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2025 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements

import Gui.Globals as Globals

EaElements.GroupBox {
    collapsible: false

    Column {
        spacing: EaStyle.Sizes.fontPixelSize

        EaElements.SideBarButton {
            enabled: Globals.BackendWrapper.analysisExperimentsAvailable.length
            wide: true
            fontIcon: Globals.BackendWrapper.analysisFittingRunning ? 'stop-circle' : 'play-circle'
            text: Globals.BackendWrapper.analysisFittingRunning  ? qsTr('Cancel fitting') : qsTr('Start fitting')

            onClicked: {
                console.debug(`Clicking '${text}' button: ${this}`)
                Globals.BackendWrapper.analysisFittingStartStop()
            }

            Component.onCompleted: Globals.References.pages.analysis.sidebar.basic.popups.startFittingButton = this
            Loader { source: "../Popups/FitStatusDialog.qml" }
        }

    }
}
