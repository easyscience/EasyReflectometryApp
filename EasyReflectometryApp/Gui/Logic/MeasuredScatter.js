// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>
//
// Shared helpers for the "measured data" scatter series rendered on the
// Analysis, Combined and Experiment chart views.
//
// Centralising the series style here keeps the three views in sync and
// gives us a single place to tweak marker shape / size / opacity on demand.

// Style constants. These are the only place where these magic numbers live.
// MARKER_SHAPE expects one of `ScatterSeries.MarkerShape*` enum values; it is
// resolved lazily inside `applyStyle` so this file does not depend on QtCharts
// being importable at load time.
var MARKER_SIZE_DOTS   = 2
var MARKER_SIZE_CIRCLES = 5
var BORDER_WIDTH  = 0
var OPACITY       = 0.95
var MARKER_SHAPE  = "Circle"   // "Circle" or "Rectangle" (ScatterSeries.MarkerShape*)

// Resolve a marker-shape name to the matching ScatterSeries enum value.
// `scatterSeriesType` is the QML type object (e.g. ScatterSeries) from which
// to read the enum. Falls back to 0 (Circle) if anything is missing.
// `shape` is the shape name, defaults to MARKER_SHAPE
function _resolveMarkerShape(scatterSeriesType, shape) {
    if (!shape) {
        shape = MARKER_SHAPE
    }
    if (!scatterSeriesType) {
        return 0
    }
    var key = "MarkerShape" + shape
    var value = scatterSeriesType[key]
    return (value !== undefined) ? value : 0
}

// Apply the canonical measured-scatter style to an existing ScatterSeries.
//   serie              -- the ScatterSeries to style (must not be null)
//   color              -- foreground/border color
//   markerStyle        -- 0: dots, 1: circles, 2: line
//   scatterSeriesType  -- the ScatterSeries QML type, used to resolve the
//                         marker-shape enum (pass `ScatterSeries` from QML)
function applyStyle(serie, color, markerStyle, scatterSeriesType) {
    if (!serie) {
        console.warn("MeasuredScatter.applyStyle: serie is null - style not applied")
        return
    }
    var markerSize = (markerStyle === 0) ? MARKER_SIZE_DOTS : MARKER_SIZE_CIRCLES
    serie.color       = color
    serie.borderColor = color
    serie.markerSize  = markerSize
    serie.borderWidth = BORDER_WIDTH
    serie.opacity     = OPACITY
    serie.markerShape = _resolveMarkerShape(scatterSeriesType)
}

// Create a styled measured series on the given chart.
//   chartView          -- ChartView instance
//   chartViewType      -- the ChartView QML type (for SeriesType enum)
//   scatterSeriesType  -- the ScatterSeries QML type (for MarkerShape enum, if scatter)
//   name, axisX, axisY -- forwarded to createSeries
//   color              -- color applied via applyStyle
//   markerStyle        -- 0: dots, 1: circles, 2: line
// Returns the new series, or null if creation failed.
function create(chartView, chartViewType, scatterSeriesType, name, axisX, axisY, color, markerStyle) {
    if (!chartView) {
        console.warn("MeasuredScatter.create: chartView is null")
        return null
    }
    var seriesType
    if (markerStyle === 2) {  // line
        seriesType = (chartViewType && chartViewType.SeriesTypeLine !== undefined)
                     ? chartViewType.SeriesTypeLine
                     : 1  // fallback: ChartView.SeriesTypeLine == 1
    } else {  // scatter
        seriesType = (chartViewType && chartViewType.SeriesTypeScatter !== undefined)
                     ? chartViewType.SeriesTypeScatter
                     : 2  // fallback: ChartView.SeriesTypeScatter == 2
    }
    var serie = chartView.createSeries(seriesType, name, axisX, axisY)
    if (!serie) {
        console.warn("MeasuredScatter.create: createSeries returned null for '" + name + "'")
        return null
    }
    if (markerStyle !== 2) {  // apply scatter style only if not line
        applyStyle(serie, color, markerStyle, scatterSeriesType)
    } else {  // line style
        serie.color = color
        serie.width = 2  // line width
    }
    serie.useOpenGL = chartView.useOpenGL
    return serie
}

// Update color + borderColor in lockstep. Useful when the selected experiment
// changes and the series should track the new color.
function setColor(serie, color) {
    if (!serie) {
        return
    }
    serie.color = color
    if (serie.borderColor !== undefined) {
        serie.borderColor = color
    }
}
