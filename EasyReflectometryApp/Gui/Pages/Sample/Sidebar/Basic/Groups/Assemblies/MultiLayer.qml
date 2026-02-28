import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals


EaElements.GroupColumn {
    EaComponents.TableView {
        id: layersView
        tallRows: false
        defaultInfoText: qsTr("No Layers Added")
        model: Globals.BackendWrapper.sampleLayers.length

        // Headers
        header: EaComponents.TableViewHeader {
            EaComponents.TableViewLabel {
                text: qsTr('No.')
                width: EaStyle.Sizes.fontPixelSize * 2.5
                id: noLabel
            }

            EaComponents.TableViewLabel {
                width: EaStyle.Sizes.sideBarContentWidth - (thickLabel.width + roughLabel.width + noLabel.width + deleteRowColumn.width + 5 * EaStyle.Sizes.tableColumnSpacing)
                horizontalAlignment: Text.AlignLeft
                text: qsTr('Material')
            }

            EaComponents.TableViewLabel {
                text: qsTr('Thickness/Å')
                width: EaStyle.Sizes.fontPixelSize * 10.0
                id: thickLabel
            }

            EaComponents.TableViewLabel {
                text: qsTr('Upper Roughness/Å')
                width: EaStyle.Sizes.fontPixelSize * 10.0
                id: roughLabel
            }

            // Placeholder for row delete button
            EaComponents.TableViewLabel {
                id: deleteRowColumn
                enabled: false
                width: EaStyle.Sizes.tableRowHeight
            }
        }

        // Rows
        delegate: EaComponents.TableViewDelegate {

            EaComponents.TableViewLabel {
                text: model.index + 1
            }

            EaComponents.TableViewComboBox{
                property string currentAssemblyName: Globals.BackendWrapper.sampleCurrentAssemblyName
                horizontalAlignment: Text.AlignLeft
                model: Globals.BackendWrapper.sampleMaterialNames
                onActivated: {
                    Globals.BackendWrapper.sampleSetCurrentLayerMaterial(currentIndex)
                }
                onModelChanged: {
                    currentIndex = indexOfValue(Globals.BackendWrapper.sampleLayers[index].material)
                }
                onCurrentAssemblyNameChanged: {
                    currentIndex = indexOfValue(Globals.BackendWrapper.sampleLayers[index].material)
                }
                Component.onCompleted: {
                    currentIndex = indexOfValue(Globals.BackendWrapper.sampleLayers[index].material)
                }
            }

            EaComponents.TableViewTextInput {
                horizontalAlignment: Text.AlignHCenter
                enabled: Globals.BackendWrapper.sampleLayers[index].thickness_enabled === "True"
                text: (isNaN(Globals.BackendWrapper.sampleLayers[index].thickness)) ? '--' : Number(Globals.BackendWrapper.sampleLayers[index].thickness).toFixed(2)
                onActiveFocusChanged: if (activeFocus && Globals.BackendWrapper.sampleCurrentLayerIndex !== index) Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                onEditingFinished: Globals.BackendWrapper.sampleSetCurrentLayerThickness(text)
            }

            EaComponents.TableViewTextInput {
                horizontalAlignment: Text.AlignHCenter
                enabled: Globals.BackendWrapper.sampleLayers[index].roughness_enabled === "True"
                text: (isNaN(Globals.BackendWrapper.sampleLayers[index].roughness)) ? '--' : Number(Globals.BackendWrapper.sampleLayers[index].roughness).toFixed(2)
                onActiveFocusChanged: if (activeFocus && Globals.BackendWrapper.sampleCurrentLayerIndex !== index) Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                onEditingFinished: Globals.BackendWrapper.sampleSetCurrentLayerRoughness(text)
            }

            EaComponents.TableViewButton {
                fontIcon: "minus-circle"
                ToolTip.text: qsTr("Remove this layer")
                enabled: layersView !== null && layersView.model > 1
                onClicked: Globals.BackendWrapper.sampleRemoveLayer(index)
            }

            mouseArea.onPressed: {
                if (Globals.BackendWrapper.sampleCurrentLayerIndex !== index) {
                    Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                }
            }
        }
    }
    // Control buttons below table
    Row {
        spacing: EaStyle.Sizes.fontPixelSize

        EaElements.SideBarButton {
            width: (EaStyle.Sizes.sideBarContentWidth - (2 * (EaStyle.Sizes.tableRowHeight + EaStyle.Sizes.fontPixelSize)) - EaStyle.Sizes.fontPixelSize) / 2
            enabled: true
            fontIcon: "plus-circle"
            text: qsTr("Add layer")
            onClicked: Globals.BackendWrapper.sampleAddNewLayer()
        }

        EaElements.SideBarButton {
            width: (EaStyle.Sizes.sideBarContentWidth - (2 * (EaStyle.Sizes.tableRowHeight + EaStyle.Sizes.fontPixelSize)) - EaStyle.Sizes.fontPixelSize) / 2
            enabled: Globals.BackendWrapper.sampleLayers.length//(layersView.currentIndex > 0) ? true : false //when item is selected
            fontIcon: "clone"
            text: qsTr("Duplicate layer")
            onClicked: Globals.BackendWrapper.sampleDuplicateSelectedLayer()
        }

        EaElements.SideBarButton {
            width: EaStyle.Sizes.tableRowHeight
            enabled: (Globals.BackendWrapper.sampleCurrentLayerIndex !== 0 && Globals.BackendWrapper.sampleLayers.length > 0 ) ? true : false//When item is selected
            fontIcon: "arrow-up"
            ToolTip.text: qsTr("Move layer up")
            onClicked: Globals.BackendWrapper.sampleMoveSelectedLayerUp()
        }

        EaElements.SideBarButton {
            width: EaStyle.Sizes.tableRowHeight
            enabled: (Globals.BackendWrapper.sampleCurrentLayerIndex + 1 !== Globals.BackendWrapper.sampleLayers.length && Globals.BackendWrapper.sampleLayers.length > 0 ) ? true : false
            fontIcon: "arrow-down"
            ToolTip.text: qsTr("Move layer down")
            onClicked: Globals.BackendWrapper.sampleMoveSelectedLayerDown()
        }
    }
}
