// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

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
            text: Globals.BackendWrapper.analysisFittingRunning ? qsTr('Cancel fitting') : (Globals.BackendWrapper.analysisIsBayesianSelected ? qsTr('Start sampling') : qsTr('Start fitting'))

            onClicked: {
                console.debug(`Clicking '${text}' button: ${this}`)
                Globals.BackendWrapper.analysisFittingStartStop()
            }

            Component.onCompleted: Globals.References.pages.analysis.sidebar.basic.popups.startFittingButton = this
        }

        // Inequality constraints that the selected engine cannot enforce, or that
        // the current values violate: the fit will be refused, say so up front.
        EaElements.Label {
            visible: Globals.BackendWrapper.sampleInequalityConstraintsCount > 0 &&
                     (!Globals.BackendWrapper.analysisMinimizerSupportsInequalities ||
                      Globals.BackendWrapper.sampleViolatedInequalityConstraints.length > 0)
            width: parent.width
            text: !Globals.BackendWrapper.analysisMinimizerSupportsInequalities
                  ? qsTr("⚠ Inequality constraints need a BUMPS minimizer.")
                  : qsTr("⚠ Current values violate an inequality constraint.")
            color: EaStyle.Colors.themeAccent
            wrapMode: Text.WordWrap
        }

        // The progress of a run is shown in the sidebar footer, under both tabs.
    }
}
