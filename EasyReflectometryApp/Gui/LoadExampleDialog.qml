import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


// Replacing the session with an example project: the one path for it, shared by the Examples
// list on the Project page and the start of a tutorial on the Home page (which can run before
// the Project page exists). ApplicationWindow.qml publishes `request` as
// Globals.References.applicationWindow.replaceSessionWithExample.
EaElements.Dialog {
    id: replaceDialog

    property var example: ({})
    // Called after a successful load only: not on Cancel, not on a load error.
    property var onLoaded: null

    // Loading replaces the whole session, like opening a project: ask first when that would
    // lose work that is not on disk. An untouched example is not such work: it can be loaded
    // again as it is.
    function request(example, onLoaded) {
        console.debug(`Requesting example '${example.name}' ::: ${this}`)
        if (Globals.BackendWrapper.projectHasUnsavedWork()) {
            replaceDialog.example = example
            replaceDialog.onLoaded = onLoaded ?? null
            replaceDialog.open()
        } else {
            load(example, onLoaded)
        }
    }

    function load(example, onLoaded) {
        Globals.References.resetActive = true
        const tabs = Globals.References.applicationWindow.appBarCentralTabs
        for (const button of [tabs.projectButton, tabs.sampleButton, tabs.experimentButton, tabs.analysisButton, tabs.summaryButton]) {
            button.enabled = true
        }
        // The Project page first: its Get started group is what shows a load error.
        if (!tabs.projectButton.checked) {
            tabs.projectButton.toggle()
        }
        let failed = false
        const onError = () => failed = true
        Globals.BackendWrapper.projectLoadError.connect(onError)
        Globals.BackendWrapper.projectLoadExample(example.path)
        Globals.BackendWrapper.projectLoadError.disconnect(onError)
        if (!failed && onLoaded) {
            onLoaded()
        }
    }

    title: qsTr('Load an example')
    modal: true
    closePolicy: Popup.CloseOnEscape

    // The dialog takes its width from its content's implicit width. A Label's is its text on
    // one line however `width` is set (and it is read-only), so the label sits in a Column,
    // whose implicit width is the label's actual width.
    Column {
        EaElements.Label {
            id: replaceMessage
            // As wide as the text, wrapping beyond a readable line length.
            width: Math.min(EaStyle.Sizes.fontPixelSize * 28, replaceMessageMetrics.advanceWidth + 1)
            wrapMode: Text.WordWrap
            TextMetrics {
                id: replaceMessageMetrics
                font: replaceMessage.font
                text: replaceMessage.text
            }
            text: {
                const name = replaceDialog.example.name ?? ''
                if (Globals.BackendWrapper.projectCreated) {
                    return qsTr('The project "%1" has unsaved changes. Loading the example "%2" discards them.')
                               .arg(Globals.BackendWrapper.projectName).arg(name)
                }
                if (Globals.BackendWrapper.projectIsExample) {
                    return qsTr('The current example has been changed, and the changes have not been saved to a project. Loading the example "%1" discards them.')
                               .arg(name)
                }
                return qsTr('This session holds work that has not been saved to a project. Loading the example "%1" discards it.')
                           .arg(name)
            }
        }
    }

    footer: EaElements.DialogButtonBox {
        EaElements.Button {
            text: qsTr('Cancel')
            onClicked: replaceDialog.close()
        }

        EaElements.Button {
            text: qsTr('Load example')
            onClicked: {
                replaceDialog.close()
                replaceDialog.load(replaceDialog.example, replaceDialog.onLoaded)
            }
        }
    }
}
