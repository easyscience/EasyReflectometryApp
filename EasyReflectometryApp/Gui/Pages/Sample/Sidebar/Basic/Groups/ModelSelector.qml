import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Models selector")
    collapsible: true
    collapsed: true
    ToolTip.text: qsTr("Section to select and define multiple models or contrasts")

    EaElements.GroupColumn {

        // Table
        EaComponents.TableView {
            id: modelView
            tallRows: false
            defaultInfoText: qsTr("No Models Present")
            model: Globals.BackendWrapper.sampleModels.length

            // Headers
            header: EaComponents.TableViewHeader {

                // Placeholder for row color
                EaComponents.TableViewLabel {
                    id: colorLabel
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                }

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.sideBarContentWidth - (colorLabel.width + deleteRowColumn.width + 3 * EaStyle.Sizes.tableColumnSpacing)
                    horizontalAlignment: Text.AlignLeft
                    text: qsTr('Label')
                }

                // Placeholder for row delete button
                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.tableRowHeight
                    id: deleteRowColumn
                }
            }

            // Rows
            delegate: EaComponents.TableViewDelegate {

                EaComponents.TableViewLabel {
                    backgroundColor: Globals.BackendWrapper.sampleModels[index].color
                }

                EaComponents.TableViewTextInput {
                    horizontalAlignment: Text.AlignLeft
                    text: Globals.BackendWrapper.sampleModels[index].label
                    // Commit while typing so "Model editor: <name>" follows the edit
                    // instead of waiting for Enter or focus loss (#407).
                    onTextEdited: Globals.BackendWrapper.sampleSetModelNameAtIndex(index, text)
                    onEditingFinished: Globals.BackendWrapper.sampleSetModelNameAtIndex(index, text)
                }

                EaComponents.TableViewButton {
                    fontIcon: "minus-circle"
                    enabled: (modelView.model > 1) ? true : false//When item is selected
                    ToolTip.text: qsTr("Remove this model")
                    onClicked: {
                        const experiments = Globals.BackendWrapper.sampleExperimentsUsingModel(index)
                        if (experiments.length === 0) {
                            Globals.BackendWrapper.sampleRemoveModel(index, -1)
                        } else {
                            removeModelDialog.ask(index, experiments)
                        }
                    }
                }

                mouseArea.onPressed: {
                    if (Globals.BackendWrapper.sampleCurrentModelIndex !== index) {
                        Globals.BackendWrapper.sampleSetCurrentModelIndex(index)
                    }
                }
            }
        }

        // Control buttons below table
        Row {
            spacing: EaStyle.Sizes.fontPixelSize

            EaElements.SideBarButton {
                enabled: true
                width: (EaStyle.Sizes.sideBarContentWidth - (2 * (EaStyle.Sizes.tableRowHeight + EaStyle.Sizes.fontPixelSize)) - EaStyle.Sizes.fontPixelSize) / 2
                fontIcon: "plus-circle"
                text: qsTr("Add model")
                onClicked: Globals.BackendWrapper.sampleAddNewModel()
            }

            EaElements.SideBarButton {
                enabled: (modelView.currentIndex > -1) ? true : false //When item is selected
                width: (EaStyle.Sizes.sideBarContentWidth - (2 * (EaStyle.Sizes.tableRowHeight + EaStyle.Sizes.fontPixelSize)) - EaStyle.Sizes.fontPixelSize) / 2
                fontIcon: "clone"
                text: qsTr("Duplicate model")
                onClicked: Globals.BackendWrapper.sampleDuplicateSelectedModel()
            }

            EaElements.SideBarButton {
                enabled: (modelView.currentIndex !== 0 && Globals.BackendWrapper.sampleModels.length > 0) ? true : false//When item is selected
                width: EaStyle.Sizes.tableRowHeight
                fontIcon: "arrow-up"
                ToolTip.text: qsTr("Move model up")
                onClicked: Globals.BackendWrapper.sampleMoveSelectedModelUp()
            }

            EaElements.SideBarButton {
                enabled: (modelView.currentIndex + 1 !== Globals.BackendWrapper.sampleModels.length && Globals.BackendWrapper.sampleModels.length > 0 ) ? true : false//When item is selected
                width: EaStyle.Sizes.tableRowHeight
                fontIcon: "arrow-down"
                ToolTip.text: qsTr("Move model down")
                onClicked: Globals.BackendWrapper.sampleMoveSelectedModelDown()
            }
        }

        // A contrast: a new model sharing the selected model's structure
        EaElements.SideBarButton {
            wide: true
            enabled: modelView.currentIndex > -1
            fontIcon: "layer-group"
            text: qsTr("Add contrast of the selected model…")
            ToolTip.text: qsTr("A new model with the same structure, e.g. the sample measured in another solvent")
            onClicked: addContrastDialog.ask(Globals.BackendWrapper.sampleCurrentModelIndex)
        }

        EaElements.Label {
            id: contrastError
            visible: text !== ''
            width: EaStyle.Sizes.sideBarContentWidth
            wrapMode: Text.WordWrap
            color: EaStyle.Colors.red
        }
    }

    EaElements.Dialog {
        id: addContrastDialog

        property int referenceIndex: -1
        property var candidates: []

        function ask(index) {
            referenceIndex = index
            candidates = Globals.BackendWrapper.sampleContrastCandidates(index)
            contrastName.text = (Globals.BackendWrapper.sampleModels[index]?.label ?? '') + qsTr(' contrast')
            contrastError.text = ''
            open()
        }

        title: qsTr("Add contrast")
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: {
            const choices = []
            for (let i = 0; i < candidateRows.count; i++) {
                const choice = candidateRows.itemAt(i).choice()
                if (choice !== null) {
                    choices.push(choice)
                }
            }
            const result = Globals.BackendWrapper.sampleAddContrast(referenceIndex, contrastName.text, choices)
            contrastError.text = result.success ? '' : result.message
        }

        Column {
            spacing: EaStyle.Sizes.fontPixelSize * 0.5

            EaElements.Label {
                width: EaStyle.Sizes.sideBarContentWidth * 1.3
                wrapMode: Text.WordWrap
                text: qsTr("The new model shares the structure of '%1': editing a shared layer edits both. "
                           + "Choose what this contrast changes; scale, background and resolution are its own.")
                      .arg(Globals.BackendWrapper.sampleModels[addContrastDialog.referenceIndex]?.label ?? '')
            }

            Row {
                spacing: EaStyle.Sizes.fontPixelSize * 0.5
                EaElements.Label { text: qsTr("Name"); anchors.verticalCenter: parent.verticalCenter }
                EaElements.TextField { id: contrastName; width: EaStyle.Sizes.sideBarContentWidth }
            }

            Repeater {
                id: candidateRows
                model: addContrastDialog.candidates

                Row {
                    spacing: EaStyle.Sizes.fontPixelSize * 0.5

                    // The choice for this row, or null to keep it as in the reference
                    function choice() {
                        if (modelData.kind === 'material') {
                            return replacement.currentIndex > 0 ? { candidate: index, material: replacement.currentIndex - 1 } : null
                        }
                        return formula.text !== modelData.formula ? { candidate: index, formula: formula.text } : null
                    }

                    EaElements.Label {
                        width: EaStyle.Sizes.fontPixelSize * 12
                        elide: Text.ElideRight
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.label
                    }
                    EaElements.ComboBox {
                        id: replacement
                        visible: modelData.kind === 'material'
                        width: EaStyle.Sizes.fontPixelSize * 12
                        model: [qsTr("keep")].concat(Globals.BackendWrapper.sampleMaterialNames)
                    }
                    EaElements.TextField {
                        id: formula
                        visible: modelData.kind === 'formula'
                        width: EaStyle.Sizes.fontPixelSize * 12
                        text: modelData.formula ?? ''
                        ToolTip.text: qsTr("Chemical formula, e.g. with D for deuterium")
                    }
                }
            }
        }
    }

    // Removing a model that experiments use: remove them too, or move them to another model.
    EaElements.Dialog {
        id: removeModelDialog

        property int modelIndex: -1
        property var experiments: []
        // Every model but the one being removed, as {index, label}
        readonly property var otherModels: Globals.BackendWrapper.sampleModels
                                           .map((model, index) => ({ index: index, label: model.label }))
                                           .filter(model => model.index !== modelIndex)

        function ask(index, boundExperiments) {
            modelIndex = index
            experiments = boundExperiments
            removeExperimentsButton.checked = true
            open()
        }

        title: qsTr("Remove model")
        modal: true
        standardButtons: Dialog.Ok | Dialog.Cancel
        onAccepted: {
            Globals.BackendWrapper.sampleRemoveModel(modelIndex, rebindButton.checked ? otherModels[targetModel.currentIndex].index : -1)
        }

        ButtonGroup { id: experimentsChoice }

        Column {
            spacing: EaStyle.Sizes.fontPixelSize * 0.5

            EaElements.Label {
                width: EaStyle.Sizes.sideBarContentWidth
                wrapMode: Text.WordWrap
                text: qsTr("These experiments use '%1': %2")
                      .arg(Globals.BackendWrapper.sampleModels[removeModelDialog.modelIndex]?.label ?? '')
                      .arg(removeModelDialog.experiments.join(', '))
            }

            EaElements.RadioButton {
                id: removeExperimentsButton
                ButtonGroup.group: experimentsChoice
                text: qsTr("Remove them as well")
            }

            Row {
                spacing: EaStyle.Sizes.fontPixelSize * 0.5

                EaElements.RadioButton {
                    id: rebindButton
                    ButtonGroup.group: experimentsChoice
                    text: qsTr("Fit them with")
                    enabled: removeModelDialog.otherModels.length > 0
                }

                EaElements.ComboBox {
                    id: targetModel
                    enabled: rebindButton.checked
                    model: removeModelDialog.otherModels.map(model => model.label)
                }
            }
        }
    }
}
