// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

import Gui as Gui
import Gui.Globals as Globals


Gui.SldChart {
    id: sldChart

    showLegend: Globals.Variables.showLegendOnAnalysisPage

    onShowLegendChanged: Globals.Variables.showLegendOnAnalysisPage = showLegend

    Component.onCompleted: {
        Globals.References.pages.analysis.mainContent.sldView = sldChart.chartView
    }
}

