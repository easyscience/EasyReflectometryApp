import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


// The automatic-save preference. Lives here rather than in the Preferences dialog because that
// dialog belongs to the shared EasyApplication package. ApplicationWindow persists the choice.
Column {
    spacing: EaStyle.Sizes.fontPixelSize * 0.5

    EaElements.CheckBox {
        id: autosaveCheckBox
        text: qsTr('Save automatically')
        checked: Globals.BackendWrapper.projectAutosaveEnabled
        ToolTip.text: qsTr('Save the project when leaving a page, after a successful fit, and before a fit, '
                           + 'a calculation engine switch or replacing the sample from an ORSO file')
        onToggled: {
            Globals.BackendWrapper.projectSetAutosaveEnabled(checked)
            // Clicking replaced the binding with a plain value; follow the backend again.
            checked = Qt.binding(() => Globals.BackendWrapper.projectAutosaveEnabled)
        }
    }

    EaElements.Label {
        width: EaStyle.Sizes.sideBarContentWidth
        wrapMode: Text.WordWrap
        color: EaStyle.Colors.themeForegroundMinor
        text: qsTr('Applies once a project has been created. Each automatic save keeps the version '
                   + 'it replaces as project.json.bak in the project folder.')
    }
}
