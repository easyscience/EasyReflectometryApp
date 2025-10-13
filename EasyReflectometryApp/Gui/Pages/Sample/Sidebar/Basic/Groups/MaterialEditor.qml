import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Material editor")
    collapsible: true
    collapsed: false

    EaElements.GroupColumn {

        // Table
        EaComponents.TableView {
            id: materialsView
            tallRows: false
            defaultInfoText: qsTr("No Materials Added/Loaded")
            model: Globals.BackendWrapper.sampleMaterials.length

            // Headers
            header: EaComponents.TableViewHeader {

                EaComponents.TableViewLabel {
                    text: qsTr('No.')
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                }

                EaComponents.TableViewLabel {
                    flexibleWidth: true
                    horizontalAlignment: Text.AlignLeft
                    text: qsTr('Name')
                }

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.fontPixelSize * 9.5
                    horizontalAlignment: Text.AlignHCenter
                    text: "SLD/10<sup>-6</sup> Å<sup>-2</sup>"
                }

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.fontPixelSize * 9.5
                    horizontalAlignment: Text.AlignHCenter
                    text: "<i>i</i> SLD/10<sup>-6</sup> Å<sup>-2</sup>"
                }

                // Placeholder for row delete button
                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.tableRowHeight
                }
            }

            // Rows
            delegate: EaComponents.TableViewDelegate {

                EaComponents.TableViewLabel {
                    text: index + 1
                    color: EaStyle.Colors.themeForegroundMinor
                }

                EaComponents.TableViewTextInput {
                    text: Globals.BackendWrapper.sampleMaterials[index].label
                    onEditingFinished: Globals.BackendWrapper.sampleSetCurrentMaterialName(text)
                }

                EaComponents.TableViewTextInput {
                    text: Number(Globals.BackendWrapper.sampleMaterials[index].sld).toFixed(3)
                    onEditingFinished: Globals.BackendWrapper.sampleSetCurrentMaterialSld(text)
                }

                EaComponents.TableViewTextInput {
                    text: Number(Globals.BackendWrapper.sampleMaterials[index].isld).toFixed(3)
                    onEditingFinished: Globals.BackendWrapper.sampleSetCurrentMaterialISld(text)
                }

                EaComponents.TableViewButton {
                    enabled: materialsView !== null && materialsView.model > 1
                    fontIcon: "minus-circle"
                    ToolTip.text: qsTr("Remove this material")
                    onClicked: Globals.BackendWrapper.sampleRemoveMaterial(index)
                }

                mouseArea.onPressed: {
                    if (Globals.BackendWrapper.sampleCurrentMaterialIndex !== index) {
                        Globals.BackendWrapper.sampleSetCurrentMaterialIndex(index)
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
                text: qsTr("Add material")
                onClicked: Globals.BackendWrapper.sampleAddNewMaterial()
            }

            EaElements.SideBarButton {
                enabled: Globals.BackendWrapper.sampleMaterials.length// (Globals.BackendWrapper.sampleCurrentMaterialIndex > 0) ? true : false //When material is selected
                width: (EaStyle.Sizes.sideBarContentWidth - (2 * (EaStyle.Sizes.tableRowHeight + EaStyle.Sizes.fontPixelSize)) - EaStyle.Sizes.fontPixelSize) / 2
                fontIcon: "clone"
                text: qsTr("Duplicate material")
                onClicked: Globals.BackendWrapper.sampleDuplicateSelectedMaterial()
            }

            EaElements.SideBarButton {
                enabled: (Globals.BackendWrapper.sampleCurrentMaterialIndex !== 0 && Globals.BackendWrapper.sampleMaterials.length > 0) ? true : false//When item is selected
                width: EaStyle.Sizes.tableRowHeight
                fontIcon: "arrow-up"
                ToolTip.text: qsTr("Move material up")
                onClicked: Globals.BackendWrapper.sampleMoveSelectedMaterialUp()
            }

            EaElements.SideBarButton {
                enabled: (Globals.BackendWrapper.sampleCurrentMaterialIndex + 1 !== Globals.BackendWrapper.sampleMaterials.length && Globals.BackendWrapper.sampleMaterials.length > 0) ? true : false//When item is selected
                width: EaStyle.Sizes.tableRowHeight
                fontIcon: "arrow-down"
                ToolTip.text: qsTr("Move material down")
                onClicked: Globals.BackendWrapper.sampleMoveSelectedMaterialDown()
            }
        }
    }
}
