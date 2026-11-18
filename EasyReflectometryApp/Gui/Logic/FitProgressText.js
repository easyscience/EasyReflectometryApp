// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>
//
// The words for the backend's fit/sampling progress map (`analysisFitProgress`):
// the one place that turns it into text, so the status bar and the Analysis
// sidebar cannot disagree. `p` is the map; see `Fitting.progress_snapshot`.

// "Fitting", "Burn-in", "Sampling", ...
function phaseText(p) {
    switch (p.phase) {
    case 'starting': return p.kind === 'sample' ? qsTr("Sampling…") : qsTr("Fitting…")
    case 'fitting': return qsTr("Fitting")
    case 'burn': return qsTr("Burn-in")
    case 'sampling': return qsTr("Sampling")
    case 'cancelling': return qsTr("Cancelling…")
    }
    return ''
}

// "132 evaluations", or with the total: "132 of max 1000 evaluations", "generation 400 of 2171"
function countText(p, withTotal) {
    const total = withTotal ? p.total : 0
    switch (p.unit) {
    case 'generations':
        return total > 0 ? qsTr("generation %1 of %2").arg(p.count).arg(total) : qsTr("generation %1").arg(p.count)
    case 'steps':
        return total > 0 ? qsTr("%1 of max %2 steps").arg(p.count).arg(total) : qsTr("%1 steps").arg(p.count)
    case 'evaluations':
        return total > 0 ? qsTr("%1 of max %2 evaluations").arg(p.count).arg(total) : qsTr("%1 evaluations").arg(p.count)
    }
    return ''
}

function reducedChi2Text(p) {
    return qsTr("reduced χ² %1").arg(p.reducedChi2.toFixed(4))
}

// Time since the run started, "0:42" or "1:02:03"; `nowMs` is Date.now().
function elapsedText(p, nowMs) {
    const seconds = Math.max(0, Math.floor((nowMs - p.startedAtMs) / 1000))
    const h = Math.floor(seconds / 3600)
    const m = Math.floor(seconds / 60) % 60
    const s = String(seconds % 60).padStart(2, '0')
    return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${s}` : `${m}:${s}`
}

// Short, for the status bar: "Sampling 42 %", "132 evaluations · reduced χ² 1.2345"
function statusText(p) {
    switch (p.phase) {
    case 'fitting':
        return countText(p, false) + ' · ' + reducedChi2Text(p)
    case 'burn':
    case 'sampling':
        return p.fraction >= 0 ? phaseText(p) + ' ' + Math.round(100 * p.fraction) + ' %'
                               : phaseText(p) + ' · ' + countText(p, false)
    }
    return phaseText(p)
}

// Detailed, for the Analysis sidebar (may hold two lines):
// "Sampling · generation 2050 of 2171 · 6:02", "Fitting · 132 evaluations · 0:42\nreduced χ² 1.2345"
function detailText(p, nowMs) {
    switch (p.phase) {
    case '':
    case 'cancelling':
        return phaseText(p)
    case 'starting':
        return phaseText(p) + ' · ' + elapsedText(p, nowMs)
    case 'fitting':
        return [phaseText(p), countText(p, true), elapsedText(p, nowMs)].join(' · ') + '\n' + reducedChi2Text(p)
    }
    return [phaseText(p), countText(p, true), elapsedText(p, nowMs)].join(' · ')
}
