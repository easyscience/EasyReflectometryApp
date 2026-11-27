pragma Singleton

import QtQuick

// The interactive tutorial part (Backends/Py/tutorial.py) with fixed data: one tutorial of two
// steps, a reading step and a step that is done once the Analysis page is open.
QtObject {

    readonly property var available: [
        { 'id': 'mock-tutorial', 'title': 'Mock tutorial', 'summary': 'Two steps of fixed text.',
          'minutes': 1, 'examplePath': '/path/to/example/project.json' }
    ]

    readonly property var _steps: [
        { 'id': 'read', 'title': 'Read this', 'body': 'A **reading** step.', 'page': 'project',
          'sidebarTab': '', 'target': '', 'actions': [], 'advance': false, 'more': 'index.html', 'hasCondition': false },
        { 'id': 'analysis', 'title': 'Open the Analysis page', 'body': 'Open the **Analysis** page.',
          'page': '', 'sidebarTab': '', 'target': 'appbar.analysisTab',
          'actions': [{ 'verb': 'goto', 'args': ['analysis'] }], 'advance': false, 'more': 'index.html',
          'hasCondition': true }
    ]

    property string state: 'idle'
    property string stopReason: ''
    property string tutorialId: ''
    readonly property string title: state === 'idle' ? '' : 'Mock tutorial'
    readonly property string examplePath: state === 'idle' ? '' : available[0].examplePath
    property int stepIndex: 0
    readonly property int stepCount: state === 'idle' ? 0 : _steps.length
    property string page: 'home'
    readonly property var step: {
        if (state === 'idle') {
            return {}
        }
        const step = _steps[stepIndex]
        const done = !step.hasCondition || page === 'analysis'
        return Object.assign({}, step, { 'state': step.hasCondition && done ? 'done' : 'waiting', 'message': '',
                                         'canNext': done, 'isLast': stepIndex === _steps.length - 1 })
    }

    signal completed(string id)

    function start(id) { tutorialId = id; stepIndex = 0; state = 'active' }
    function stop() { state = 'idle'; tutorialId = '' }
    function next() {
        if (state !== 'active' || !step.canNext) {
            return
        }
        if (stepIndex === _steps.length - 1) {
            state = 'finished'
            completed(tutorialId)
        } else {
            stepIndex += 1
        }
    }
    function previous() { if (state === 'active' && stepIndex > 0) stepIndex -= 1 }
    function skip() { if (state === 'active') stepIndex = Math.min(stepIndex + 1, _steps.length - 1) }
    function reportUi(key, value) { if (key === 'page') page = value }
}
