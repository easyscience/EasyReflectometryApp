import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals
import "./Assemblies" as Assemblies

EaElements.GroupBox {
    title: qsTr("Model editor: " + Globals.BackendWrapper.sampleCurrentModelName)
    collapsible: true
    collapsed: true

    property string currentAssemblyType: Globals.BackendWrapper.sampleCurrentAssemblyType

    EaElements.GroupColumn {

        // Table
        EaComponents.TableView {
            id: assembliesView
            tallRows: false
            defaultInfoText: qsTr("No Model Present")
            model: Globals.BackendWrapper.sampleAssemblies.length

            // Headers
            header: EaComponents.TableViewHeader {

                // Placeholder for color column
                EaComponents.TableViewLabel {
                    text: qsTr('No.')
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                    id: noLabel
                }

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.sideBarContentWidth - (noLabel.width + deleteRowColumn.width + layersType.width + 4 * EaStyle.Sizes.tableColumnSpacing)
                    horizontalAlignment: Text.AlignLeft
                    text: qsTr('Label')
                }

                EaComponents.TableViewLabel {
                    id: layersType
                    width: EaStyle.Sizes.fontPixelSize * 13.8
                    text: qsTr('Type')
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
                    color: EaStyle.Colors.themeForegroundMinor
                    text: index + 1
                }

                EaComponents.TableViewTextInput {
                    horizontalAlignment: Text.AlignLeft
                    text: Globals.BackendWrapper.sampleAssemblies[index].label
                    onEditingFinished: Globals.BackendWrapper.sampleSetAssemblyNameAtIndex(index, text)
                }

                EaComponents.TableViewComboBox{
                    readonly property int rowIndex: index
                    horizontalAlignment: Text.AlignLeft
                    property var fullModel: ["Multi-layer", "Repeating Multi-layer", "Surfactant Layer"]
                    property var limitedModel: ["Multi-layer", "Repeating Multi-layer"]
                    model: index === 0 || index === assembliesView.model - 1 ? limitedModel : fullModel
                    onActivated: function(comboIndex) {
                        Globals.BackendWrapper.sampleSetAssemblyTypeAtIndex(rowIndex, model[comboIndex])
                    }
                    Component.onCompleted: {
                        currentIndex = indexOfValue(Globals.BackendWrapper.sampleAssemblies[index].type)
                    }
                }

                EaComponents.TableViewButton {
                    fontIcon: "minus-circle"
                    ToolTip.text: qsTr("Remove this assembly")
                    enabled: assembliesView.model > 1
                    onClicked: Globals.BackendWrapper.sampleRemoveAssembly(index)
                }

                mouseArea.onPressed: {
                    if (Globals.BackendWrapper.sampleCurrentAssemblyIndex !== index) {
                        Globals.BackendWrapper.sampleSetCurrentAssemblyIndex(index)
                    }
                }

            }
//            onModelChanged: Globals.BackendWrapper.sampleSetCurrentAssemblyIndex(0)

        }
        // Control buttons below table
        Row {
            spacing: EaStyle.Sizes.fontPixelSize

            EaElements.SideBarButton {
                enabled: true
                width: (EaStyle.Sizes.sideBarContentWidth - (2 * (EaStyle.Sizes.tableRowHeight + EaStyle.Sizes.fontPixelSize)) - EaStyle.Sizes.fontPixelSize) / 2
                fontIcon: "plus-circle"
                text: qsTr("Add assembly")
                onClicked: Globals.BackendWrapper.sampleAddNewAssembly()
            }

            EaElements.SideBarButton {
                enabled: Globals.BackendWrapper.sampleAssemblies.length //(assembliesView.currentIndex > 0) ? true : false//When item is selected
                width: (EaStyle.Sizes.sideBarContentWidth - (2 * (EaStyle.Sizes.tableRowHeight + EaStyle.Sizes.fontPixelSize)) - EaStyle.Sizes.fontPixelSize) / 2
                fontIcon: "clone"
                text: qsTr("Duplicate assembly")
                onClicked: Globals.BackendWrapper.sampleDuplicateSelectedAssembly()
            }

            EaElements.SideBarButton {
                enabled: (Globals.BackendWrapper.sampleCurrentAssemblyIndex !== 0 && Globals.BackendWrapper.sampleAssemblies.length > 0 ) ? true : false//When item is selected
                width: EaStyle.Sizes.tableRowHeight
                fontIcon: "arrow-up"
                ToolTip.text: qsTr("Move assembly up")
                onClicked: Globals.BackendWrapper.sampleMoveSelectedAssemblyUp()
            }

            EaElements.SideBarButton {
                enabled: (Globals.BackendWrapper.sampleCurrentAssemblyIndex + 1 !== Globals.BackendWrapper.sampleAssemblies.length && Globals.BackendWrapper.sampleAssemblies.length > 0 ) ? true : false//When item is selected
                width: EaStyle.Sizes.tableRowHeight
                fontIcon: "arrow-down"
                ToolTip.text: qsTr("Move assembly down")
                onClicked: Globals.BackendWrapper.sampleMoveSelectedAssemblyDown()
            }
        }

        // Layer editor
        EaElements.Label {
            text: qsTr("Layer editor: " + Globals.BackendWrapper.sampleCurrentAssemblyName)
            font.bold: true
        }

        Assemblies.MultiLayer {
            visible: currentAssemblyType === 'Multi-layer'
        }

        Assemblies.RepeatingMultiLayer {
            visible: currentAssemblyType === 'Repeating Multi-layer'
        }

        Assemblies.SurfactantLayer {
            visible: currentAssemblyType === 'Surfactant Layer'
        }
    }
}
