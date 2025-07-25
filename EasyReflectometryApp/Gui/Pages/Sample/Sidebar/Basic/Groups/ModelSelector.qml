import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

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
                    onEditingFinished: Globals.BackendWrapper.sampleSetCurrentModelName(text)
                }

                EaComponents.TableViewButton {
                    fontIcon: "minus-circle"
                    enabled: (modelView.model > 1) ? true : false//When item is selected
                    ToolTip.text: qsTr("Remove this model")
                    onClicked: {
                        Globals.BackendWrapper.sampleRemoveModel(index)
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
                // enabled: (modelView.currentIndex > 0) ? true : false //When item is selected
                enabled: true
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
    }
}
