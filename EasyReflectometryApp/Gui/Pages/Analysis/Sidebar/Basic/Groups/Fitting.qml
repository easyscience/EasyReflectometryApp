// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

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
        }

        // Progress message shown during fitting or sampling
        EaElements.Label {
            visible: Globals.BackendWrapper.analysisFitProgressMessage !== ''
            text: Globals.BackendWrapper.analysisFitProgressMessage
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.WordWrap
        }

        // Indeterminate progress bar shown during fitting/sampling
        ProgressBar {
            visible: Globals.BackendWrapper.analysisFittingRunning
            indeterminate: Globals.BackendWrapper.analysisIsBayesianSelected
            from: 0
            to: 100
            value: Globals.BackendWrapper.analysisFitIteration > 0 ? 50 : 0
            width: parent.width
        }
    }
}
