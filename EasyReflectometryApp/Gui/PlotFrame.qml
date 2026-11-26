// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Animations as EaAnimations

// A border on all four sides of a ChartView's plot area, as in a publication
// figure. The axes hide their own lines (EasyApp's value axis, LogQAxis), so
// this is the only frame. Declare it as a child of the ChartView:
//
//     Gui.PlotFrame { chart: chartView }
//
// It follows plotArea, so it tracks resizes and axis label width changes.
Rectangle {
    property Item chart: parent

    objectName: 'plotFrame'

    x: chart ? chart.plotArea.x : 0
    y: chart ? chart.plotArea.y : 0
    width: chart ? chart.plotArea.width : 0
    height: chart ? chart.plotArea.height : 0

    color: 'transparent'
    border.width: 1
    border.color: EaStyle.Colors.chartForeground
    Behavior on border.color { EaAnimations.ThemeChange {} }
    // Softened so it frames the plot without outweighing the data.
    opacity: 0.5

    // Purely decorative: never takes mouse input from the chart's zoom/pan areas.
    enabled: false
}
