import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals


// The example projects shipped with the app, after EasyDiffraction's Project page. Clicking one
// loads its sample, data and fit settings as a project that is not created yet: nothing is saved
// until "Create a new project" (keeping the sample and data) gives it a location of the user's own.
EaComponents.TableView {
    id: tableView

    showHeader: false
    tallRows: true
    maxRowCountShow: 7

    defaultInfoText: qsTr('No examples available')

    model: Globals.BackendWrapper.projectExamples

    // Not shown, but the table takes its column widths and alignment from it.
    header: EaComponents.TableViewHeader {
        EaComponents.TableViewLabel {
            enabled: false
            width: EaStyle.Sizes.fontPixelSize * 2.5
        }

        EaComponents.TableViewLabel {
            flexibleWidth: true
            horizontalAlignment: Text.AlignLeft
            text: qsTr('name / description')
        }
    }

    delegate: EaComponents.TableViewDelegate {
        mouseArea.onPressed: requestExample(tableView.model[index])

        EaComponents.TableViewLabel {
            text: index + 1
            color: EaStyle.Colors.themeForegroundMinor
        }

        EaComponents.TableViewTwoRowsAdvancedLabel {
            fontIcon: 'archive'
            text: tableView.model[index].name
            minorText: tableView.model[index].description
            ToolTip.text: tableView.model[index].description
        }
    }

    // Asks first when that would discard unsaved work: see Gui/LoadExampleDialog.qml.
    function requestExample(example) {
        console.debug(`Clicking example '${example.name}' ::: ${this}`)
        Globals.References.applicationWindow.replaceSessionWithExample(example)
    }
}
