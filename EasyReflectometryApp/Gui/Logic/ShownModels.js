// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>
//
// Which models a chart draws, shared by the reflectivity and SLD charts of the
// Sample and Analysis pages. `shown` lists the model indices to draw; null (or
// undefined) draws every model.

function includes(shown, modelIndex) {
    return !shown || shown.indexOf(modelIndex) !== -1
}

// Show or hide the curves of each model: `modelSeries[i]` is model i's curve,
// each of `entries` ({series, modelIndex}) a further curve of one model.
function apply(shown, modelSeries, entries) {
    for (let i = 0; i < modelSeries.length; i++) {
        if (modelSeries[i]) {
            modelSeries[i].visible = includes(shown, i)
        }
    }
    for (let e = 0; e < entries.length; e++) {
        if (entries[e].series) {
            entries[e].series.visible = includes(shown, entries[e].modelIndex)
        }
    }
}
