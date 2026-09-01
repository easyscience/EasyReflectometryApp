pragma Singleton

import QtQuick

QtObject {
    property bool experimentalData: true
    property double scaling: 1.
    property double background: 2.
    property string resolution: '3.00'

    // Setters
    function setScaling(value) {
        console.debug(`setScaling ${value}`)
    }
    function setBackground(value) {
        console.debug(`setBackgroun ${value}`)
    }
    function setResolution(value) {
        console.debug(`setResolution ${value}`)
    }

    function load(path) {
        console.debug(`Loading experiment from ${path}`)
    }

    // Filename-token suggestion, so the assignment dialog can be exercised
    // against the mock backend as well.
    function suggestPolarizedChannels(paths) {
        console.debug(`Suggesting polarized channels for ${paths}`)
        const list = Array.isArray(paths) ? paths : String(paths).split(',')
        const tokens = {uu: 'pp', pp: 'pp', dd: 'mm', mm: 'mm', ud: 'pm', pm: 'pm', du: 'mp', mp: 'mp'}
        return list.filter(path => path !== '').map(path => {
            const name = String(path).split(/[\\/]/).pop()
            let channel = ''
            for (const token in tokens) {
                if (name.toLowerCase().indexOf('_' + token) !== -1) {
                    channel = tokens[token]
                    break
                }
            }
            return {path: path, name: name, channel: channel}
        })
    }

    function loadPolarized(assignments) {
        console.debug(`Loading polarized experiment from ${assignments.length} file(s)`)
    }

    // Emitted with a user-facing message when an import is rejected.
    signal loadFailed(string message)
    // Emitted with the list position of a newly imported experiment.
    signal experimentLoaded(int index)
}
