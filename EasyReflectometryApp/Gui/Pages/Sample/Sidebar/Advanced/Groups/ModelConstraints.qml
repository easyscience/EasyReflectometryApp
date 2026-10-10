import QtQuick
import QtQuick.Controls
import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    id: modelConstraintsGroup
    title: qsTr("Link contrasts")
    enabled: true
    last: true

    property var selectedModelIndices: []
    property int selectedModelsCount: selectedModelIndices.length

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.75
        width: parent ? parent.width : undefined

        EaElements.Label {
            width: parent.width
            text: qsTr("Tie the parameters of the selected models to those of the first one, e.g. contrasts "
                       + "of one sample. Scale and background stay per model.")
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeForegroundMinor
        }

        // Models table
        Item {
            id: modelTableContainer
            width: parent.width
            height: Math.min(200, Math.max(60, modelsTable.height))

            EaComponents.TableView {
                id: modelsTable
                width: parent.width
                height: Math.min(200, Math.max(60, Math.max(modelsTable.contentHeight, modelsTable.implicitHeight)))
                enabled: Globals.BackendWrapper.sampleModelNames && Globals.BackendWrapper.sampleModelNames.length > 1

                defaultInfoText: qsTr("No Models Available")

                // Table model - use backend data directly
                model: Globals.BackendWrapper.sampleModelNames ? Globals.BackendWrapper.sampleModelNames.length : 0

                // Header row
                header: EaComponents.TableViewHeader {

                    EaComponents.TableViewLabel {
                        width: EaStyle.Sizes.fontPixelSize * 3
                        text: qsTr("Select")
                    }

                    EaComponents.TableViewLabel {
                        id: modelNameHeaderColumn
                        width: EaStyle.Sizes.fontPixelSize * 30
                        horizontalAlignment: Text.AlignLeft
                        text: qsTr("")
                    }
                }

                // Table rows
                delegate: EaComponents.TableViewDelegate {

                    EaElements.CheckBox {
                        id: modelCheckBox
                        width: EaStyle.Sizes.fontPixelSize * 3
                        checked: false
                        topPadding: 0
                        bottomPadding: 0
                        anchors.verticalCenter: parent.verticalCenter
                        onToggled: {
                            var newIndices = modelConstraintsGroup.selectedModelIndices.slice() // Copy the array
                            if (checked) {
                                newIndices.push(index)
                            } else {
                                const idx = newIndices.indexOf(index)
                                if (idx > -1) {
                                    newIndices.splice(idx, 1)
                                }
                            }
                            modelConstraintsGroup.selectedModelIndices = newIndices // Reassign to trigger update
                            // console.debug("Model", index, "checked state:", checked, "Selected indices:", modelConstraintsGroup.selectedModelIndices)
                        }
                    }

                    EaComponents.TableViewLabel {
                        id: modelNameColumn
                        width: EaStyle.Sizes.fontPixelSize * 30
                        horizontalAlignment: Text.AlignLeft
                        text: {
                            const modelName = Globals.BackendWrapper.sampleModelNames[index]
                            return modelName ? modelName : ""
                        }
                        elide: Text.ElideRight
                    }

                    mouseArea.onPressed: {
                        if (modelsTable.currentIndex !== index) {
                            modelsTable.currentIndex = index
                        }
                    }
                }
            }
        }

        Item {
            height: EaStyle.Sizes.fontPixelSize * 0.5
            width: 1
        }

        // Contrasts differ in their materials, so their SLDs are tied only on request.
        EaElements.CheckBox {
            id: tieMaterialsCheckBox
            checked: false
            text: qsTr("Also tie material SLDs and densities")
            ToolTip.text: qsTr("Leave unticked when the models are contrasts, i.e. differ in their materials")
        }

        EaElements.SideBarButton {
            id: constrainModelsButton
            wide: true
            fontIcon: "link"
            text: qsTr("Link selected models")
            enabled: modelConstraintsGroup.selectedModelsCount > 1
            onClicked: {
                const result = Globals.BackendWrapper.sampleConstrainModelsParameters(
                    modelConstraintsGroup.selectedModelIndices, tieMaterialsCheckBox.checked)
                linkResult.text = result
                    ? qsTr("%1 parameter(s) tied.").arg(result.tied)
                      + (result.messages.length ? '\n' + result.messages.join('\n') : '')
                    : ''
            }
        }

        EaElements.Label {
            id: linkResult
            width: parent.width
            visible: text !== ''
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeForegroundMinor
        }

        // Model constraints table
        Item {
            height: EaStyle.Sizes.fontPixelSize * 0.5
            width: 1
        }

        EaElements.Label {
            enabled: true
            text: qsTr("Model Constraints")
        }

        Item {
            id: modelConstraintsTableContainer
            width: parent.width
            height: modelConstraintsTable.height

            EaComponents.TableView {
                id: modelConstraintsTable
                width: parent.width
                maxRowCountShow: 1000

                defaultInfoText: qsTr("No Model Constraints")

                // Table model - use backend data directly
                model: Globals.BackendWrapper.sampleConstraintsList.length

                // Header row
                header: EaComponents.TableViewHeader {

                    EaComponents.TableViewLabel {
                        width: EaStyle.Sizes.fontPixelSize * 2.5
                        text: qsTr("No.")
                    }

                    EaComponents.TableViewLabel {
                        id: modelConstraintNameHeaderColumn
                        width: EaStyle.Sizes.fontPixelSize * 31
                        horizontalAlignment: Text.AlignHCenter
                        text: qsTr("Constraint")
                    }

                    // Placeholder for row delete button
                    EaComponents.TableViewLabel {
                        width: EaStyle.Sizes.tableRowHeight
                    }
                }

                // Table rows
                delegate: EaComponents.TableViewDelegate {

                    EaComponents.TableViewLabel {
                        id: modelConstraintNumberColumn
                        width: EaStyle.Sizes.fontPixelSize * 2.5
                        text: index + 1
                        color: EaStyle.Colors.themeForegroundMinor
                    }

                    EaComponents.TableViewLabel {
                        id: modelConstraintColumn
                        width: EaStyle.Sizes.fontPixelSize * 31
                        horizontalAlignment: Text.AlignLeft
                        text: {
                            const constraint = Globals.BackendWrapper.sampleConstraintsList[index]
                            if (!constraint) {
                                return ""
                            }
                            const prefix = constraint.relation ? constraint.relation + ' ' : ''
                            return constraint.dependentName + ' ' + prefix + constraint.expression
                        }
                        elide: Text.ElideRight
                    }

                    // Placeholder for delete button space
                    Item {
                        width: EaStyle.Sizes.tableRowHeight
                    }

                    mouseArea.onPressed: {
                        if (modelConstraintsTable.currentIndex !== index) {
                            modelConstraintsTable.currentIndex = index
                        }
                    }
                }
            }

            // Delete buttons - separate from table content but positioned at row level
            Column {
                id: modelDeleteButtonsColumn
                anchors.right: parent.right
                anchors.top: modelConstraintsTable.top
                anchors.topMargin: modelConstraintsTable.headerItem ? modelConstraintsTable.headerItem.height : 0
                spacing: 0

                Repeater {
                    model: Globals.BackendWrapper.sampleConstraintsList.length

                    EaElements.SideBarButton {
                        width: 35
                        height: EaStyle.Sizes.tableRowHeight
                        fontIcon: "minus-circle"
                        ToolTip.text: qsTr("Remove this constraint")

                        onClicked: {
                            Globals.BackendWrapper.sampleRemoveConstraintByIndex(index)
                        }
                    }
                }
            }
        }
    }
}
    