// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

import Gui as Gui
import Gui.Globals as Globals


Gui.SldChart {
    id: sldChart

    showLegend: Globals.Variables.showLegendOnSamplePage
    reverseZAxis: Globals.Variables.reverseSldZAxis

    onShowLegendChanged: Globals.Variables.showLegendOnSamplePage = showLegend

    Component.onCompleted: {
        Globals.References.pages.sample.mainContent.sldView = sldChart.chartView
    }
}

