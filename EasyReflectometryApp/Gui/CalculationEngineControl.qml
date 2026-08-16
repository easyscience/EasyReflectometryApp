// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

// The project's calculation engine. Shown on the Analysis page (where fitting
// happens) and on the Sample page (where magnetism is edited, which only some
// engines can model). One backend property, so the two cannot disagree.
Column {
    spacing: EaStyle.Sizes.fontPixelSize * 0.5

    EaElements.ComboBox {
        id: engineBox

        width: EaStyle.Sizes.sideBarContentWidth
        model: Globals.BackendWrapper.sampleCalculationEngines
        currentIndex: Globals.BackendWrapper.sampleCalculationEngineIndex
        onActivated: {
            Globals.BackendWrapper.sampleSetCalculationEngineIndex(currentIndex)
            // The backend refuses an engine that cannot carry the sample's
            // magnetism; follow its state rather than the click.
            currentIndex = Qt.binding(function () { return Globals.BackendWrapper.sampleCalculationEngineIndex })
        }
    }

    EaElements.Label {
        color: EaStyle.Colors.themeForegroundMinor
        wrapMode: Text.WordWrap
        width: EaStyle.Sizes.sideBarContentWidth
        text: qsTr("Magnetic layers can only be modelled by %1.")
              .arg(Globals.BackendWrapper.sampleCalculationEnginesSupportingMagnetism.join(', '))
    }
}
