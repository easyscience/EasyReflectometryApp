// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


// A cancelled fit leaves its best point in the parameters: keep it, or go back
// to where the fit started. Shown instead of the results dialog, and only
// closed by a choice.
EaElements.Dialog {
    id: dialog

    readonly property var cancelled: Globals.BackendWrapper.analysisFitCancelledAt

    visible: Globals.BackendWrapper.analysisFitCancelPending
    title: qsTr("Refinement Cancelled")
    modal: true
    closePolicy: Popup.NoAutoClose

    EaElements.Label {
        width: EaStyle.Sizes.sideBarContentWidth
        wrapMode: Text.WordWrap
        text: qsTr("The fit was cancelled at reduced χ² = %1 after %2 %3.")
                  .arg(Number(dialog.cancelled.reducedChi2 ?? 0).toFixed(4))
                  .arg(dialog.cancelled.count ?? 0)
                  .arg(dialog.cancelled.unit ?? '')
              + '\n\n'
              + qsTr("The parameters have the current best values. Their uncertainties are cleared.")
    }

    footer: EaElements.DialogButtonBox {
        EaElements.Button {
            text: qsTr("Revert to starting values")
            onClicked: Globals.BackendWrapper.analysisRevertCancelledFit()
        }

        EaElements.Button {
            text: qsTr("Keep current values")
            onClicked: Globals.BackendWrapper.analysisKeepCancelledFit()
        }
    }
}
