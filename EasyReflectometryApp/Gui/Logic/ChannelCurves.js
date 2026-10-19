// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>
//
// The model spin cross-sections drawn next to the model curve on the sample
// page reflectivity charts (SampleView and the combined view). Shared so the
// two views cannot drift apart.

// Cross-section series of one model, as {series, modelIndex, channel, label}
// entries. Empty unless the model is magnetic and the user asked for the split,
// so an ordinary project draws exactly the curves it always did.
function create(chartView, chartViewType, backend, modelIndex, model, xAxis, yAxis, useOpenGL, hovered) {
    let created = []
    if (!backend.plottingShowModelChannels || !backend.plottingModelHasMagnetism(modelIndex)) {
        return created
    }
    const curves = [
        {channel: 'pp', label: qsTr("R↑↑ (up-up)"), color: Qt.lighter(model.color, 1.15)},
        {channel: 'mm', label: qsTr("R↓↓ (down-down)"), color: Qt.darker(model.color, 1.2)},
    ]
    for (let i = 0; i < curves.length; i++) {
        const line = chartView.createSeries(chartViewType.SeriesTypeLine,
                                            model.label + ' ' + curves[i].channel, xAxis, yAxis)
        // Same hue as the model, dashed and shaded: the colour still says
        // "which model", the dash and shade say "which cross-section".
        line.color = curves[i].color
        line.width = 1.5
        line.style = Qt.DashLine
        line.useOpenGL = useOpenGL
        line.hovered.connect(hovered)
        created.push({series: line, modelIndex: modelIndex, channel: curves[i].channel,
                      label: curves[i].label + ' ' + model.label})
    }
    return created
}

function remove(chartView, entries) {
    for (let i = 0; i < entries.length; i++) {
        chartView.removeSeries(entries[i].series)
    }
}

function refresh(backend, entries) {
    for (let i = 0; i < entries.length; i++) {
        backend.plottingFillSampleChannelSeriesForModel(entries[i].series, entries[i].modelIndex,
                                                        entries[i].channel)
    }
}
