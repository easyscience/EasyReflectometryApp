import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
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

    // Loading replaces the whole session, like opening a project: ask first when that would
    // lose work that is not on disk. An untouched example is not such work: it can be loaded
    // again as it is.
    function requestExample(example) {
        console.debug(`Clicking example '${example.name}' ::: ${this}`)
        if (Globals.BackendWrapper.projectHasUnsavedWork()) {
            replaceDialog.example = example
            replaceDialog.open()
        } else {
            loadExample(example)
        }
    }

    function loadExample(example) {
        Globals.References.resetActive = true
        const tabs = Globals.References.applicationWindow.appBarCentralTabs
        tabs.sampleButton.enabled = true
        tabs.experimentButton.enabled = true
        tabs.analysisButton.enabled = true
        tabs.summaryButton.enabled = true
        Globals.BackendWrapper.projectLoadExample(example.path)
    }

    EaElements.Dialog {
        id: replaceDialog

        property var example: ({})

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
                    tableView.loadExample(replaceDialog.example)
                }
            }
        }
    }

}
