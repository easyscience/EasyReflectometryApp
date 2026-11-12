pragma Singleton

import QtQuick

QtObject {

    property bool created: false
    property string creationDate: ''
    property string lastSaved: ''
    property bool hasUnsavedChanges: false

    // Like the Python backend, carries the path of the project file that was written.
    signal projectSaved(string path)
    signal projectSaveError(string message)
    function projectFilePath() { return `${location}/${name}/project.json` }

    property string name: 'Super duper project'
    function setName(value) { name = value; hasUnsavedChanges = true }
    property string description: 'Default project description from Mock proxy'
    function setDescription(value) { description = value; hasUnsavedChanges = true }
    property string location: '/path to the project'
    function setLocation(value) { location = value; hasUnsavedChanges = true }    

    function create() {
        console.debug(`Creating project ${name}`)
        creationDate = `${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`
        created = true
        lastSaved = new Date().toISOString()
        hasUnsavedChanges = false
        projectSaved(projectFilePath())
    }

    function save() {
        console.debug(`Saving project ${name}`)
        lastSaved = new Date().toISOString()
        lastSaveAutomatic = false
        hasUnsavedChanges = false
        projectSaved(projectFilePath())
    }

    // Automatic saves, with the same gating as the Python backend (minus the fit blocker).
    property bool autosaveEnabled: true
    function setAutosaveEnabled(value) { autosaveEnabled = value }
    property bool autosaveFailing: false
    property bool lastSaveAutomatic: false
    property string backupPath: `${projectFilePath()}.bak`
    signal autosaveError(string message)
    function autosave(reason) {
        if (!autosaveEnabled || !created || !hasUnsavedChanges) {
            return false
        }
        console.debug(`Autosaving project ${name} (${reason})`)
        lastSaved = new Date().toISOString()
        lastSaveAutomatic = true
        hasUnsavedChanges = false
        projectSaved(projectFilePath())
        return true
    }

    function hasCustomContent() { return created }

    function reset() {
        console.debug(`Reset project ${name}`)
        created = false
        lastSaved = ''
        hasUnsavedChanges = false
    }

    function load(path) {
        console.debug(`Loading project from ${path}`)
        creationDate = `${new Date().toLocaleDateString()} ${new Date().toLocaleTimeString()}`
        created = true
        lastSaved = ''
        hasUnsavedChanges = false
    }

}
