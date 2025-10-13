import QtQuick 2.13
import QtQuick.Controls 2.13

import easyApp.Gui.Style as EaStyle
import easyApp.Gui.Elements as EaElements
import easyApp.Gui.Components as EaComponents
import easyApp.Gui.Logic as EaLogic

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Sample constraints")
    enabled: true
    last: false

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5
        Column {

            EaElements.Label {
                enabled: true
                text: qsTr("Numeric or Parameter-Parameter constraint")
            }

            Grid {
                columns: 4
                columnSpacing: EaStyle.Sizes.fontPixelSize * 0.5
                rowSpacing: EaStyle.Sizes.fontPixelSize * 0.5
                verticalItemAlignment: Grid.AlignVCenter

                EaElements.ComboBox {
                    id: dependentPar
                    width: 359
                    currentIndex: -1
                    displayText: currentIndex === -1 ? "Select dependent parameter" : currentText
                    model: Globals.BackendWrapper.sampleDepParameterNames
                    // Removed onCurrentIndexChanged handler to prevent circular updates
                }

                EaElements.ComboBox {
                    id: relationalOperator
                    width: 47
                    currentIndex: 0
                    font.family: EaStyle.Fonts.iconsFamily
                    model: Globals.BackendWrapper.sampleRelationOperators
                }

                Item { height: 1; width: 1 }
                Item { height: 1; width: 1 }

                EaElements.ComboBox {
                    id: independentPar
                    width: dependentPar.width
                    currentIndex: -1
                    displayText: currentIndex === -1 ? "Numeric constrain or select independent parameter" : currentText
                    // let's avoid circular dependencies by not allowing to select dependent parameter here
                    // model: Globals.BackendWrapper.sampleParameterNames
                    model: Globals.BackendWrapper.sampleDepParameterNames
                    onCurrentIndexChanged: {
                        if (currentIndex === -1){
                            arithmeticOperator.model = Globals.BackendWrapper.sampleArithmicOperators.slice(0,1)  // no arithmetic operators
                        }
                        else{
                            arithmeticOperator.model = Globals.BackendWrapper.sampleArithmicOperators.slice(1) // allow all arithmetic operators
                        }
                    }
                }

                EaElements.ComboBox {
                    id: arithmeticOperator
                    width: relationalOperator.width
                    currentIndex: 0
                    font.family: EaStyle.Fonts.iconsFamily
                    model: arithmeticOperator.model = Globals.BackendWrapper.sampleArithmicOperators.slice(0,1)
                }

                EaElements.TextField {
                    id: value
                    width: 65
                    horizontalAlignment: Text.AlignRight
                    text: "1.0000"
                }

                EaElements.SideBarButton {
                    id: addConstraint
                    enabled: ( 
                         ( dependentPar.currentIndex !== -1 && independentPar.currentIndex !== -1 && independentPar.currentIndex !== dependentPar.currentIndex ) ||
                         ( dependentPar.currentIndex !== -1 && independentPar.currentIndex === -1 )
                    )
                    width: 35
                    fontIcon: "plus-circle"
                    ToolTip.text: qsTr("Add Numeric or Parameter-Parameter constraint")
                    onClicked: {
                        Globals.BackendWrapper.sampleAddConstraint(
                            dependentPar.currentIndex,
                            relationalOperator.currentText.replace("\uf52c", "=").replace("\uf531", ">").replace("\uf536", "<"),
                            value.text,
                            arithmeticOperator.currentText.replace("\uf00d", "*").replace("\uf529", "/").replace("\uf067", "+").replace("\uf068", "-"),
                            independentPar.currentIndex
                        )

                        // Reset form
                        independentPar.currentIndex = -1
                        dependentPar.currentIndex = -1
                        relationalOperator.currentIndex = 0
                        arithmeticOperator.currentIndex = 0
                    }
                }
            }
        }

        // Constraints table to display existing constraints
        Item {
            height: EaStyle.Sizes.fontPixelSize * 0.5
            width: 1
        }

        EaElements.Label {
            enabled: true
            text: qsTr("Active Constraints")
        }

        Item {
            id: constraintTableContainer
            width: parent.width
            height: Math.min(200, Math.max(60, constraintsTable.height))

            EaComponents.TableView {
                id: constraintsTable
                width: parent.width
                height: Math.min(200, Math.max(60, Math.max(constraintsTable.contentHeight, constraintsTable.implicitHeight)))

                defaultInfoText: qsTr("No Active Constraints")

                // Table model - use backend data directly like other tables
                property int refreshTrigger: 0
                model: {
                    // Include refreshTrigger to force re-evaluation
                    refreshTrigger // This creates a dependency
                    return Globals.BackendWrapper.sampleConstraintsList.length
                }

                // No Component.onCompleted needed - table uses backend data directly

                Connections {
                    target: Globals.BackendWrapper.activeBackend.sample
                    function onConstraintsChanged() {
                        // Force table model to refresh by changing the trigger
                        constraintsTable.refreshTrigger++
                    }
                }

                // Header row
                header: EaComponents.TableViewHeader {

                    EaComponents.TableViewLabel {
                        width: EaStyle.Sizes.fontPixelSize * 2.5
                        text: qsTr("No.")
                    }

                    EaComponents.TableViewLabel {
                        id: dependentNameHeaderColumn
                        width: EaStyle.Sizes.fontPixelSize * 12
                        horizontalAlignment: Text.AlignHCenter
                        text: qsTr("Parameter")
                    }

                    EaComponents.TableViewLabel {
                        width: EaStyle.Sizes.fontPixelSize * 19
                        horizontalAlignment: Text.AlignHCenter
                        text: qsTr("Expression")
                    }

                    // Placeholder for row delete button
                    EaComponents.TableViewLabel {
                        width: EaStyle.Sizes.tableRowHeight
                    }
                }

                // Table rows
                delegate: EaComponents.TableViewDelegate {

                    EaComponents.TableViewLabel {
                        id: numberColumn
                        width: EaStyle.Sizes.fontPixelSize * 2.5
                        text: index + 1
                        color: EaStyle.Colors.themeForegroundMinor
                    }

                    EaComponents.TableViewLabel {
                        id: dependentNameColumn
                        width: EaStyle.Sizes.fontPixelSize * 12
                        horizontalAlignment: Text.AlignLeft
                        text: {
                            const constraint = Globals.BackendWrapper.sampleConstraintsList[index]
                            return constraint ? Object.keys(constraint)[0] : ""
                        }
                        elide: Text.ElideRight
                    }

                    EaComponents.TableViewLabel {
                        id: expressionColumn
                        width: EaStyle.Sizes.fontPixelSize * 15
                        horizontalAlignment: Text.AlignLeft
                        text: {
                            const constraint = Globals.BackendWrapper.sampleConstraintsList[index]
                            if (constraint) {
                                const paramName = Object.keys(constraint)[0]
                                return constraint[paramName]
                            }
                            return ""
                        }
                        elide: Text.ElideRight
                    }

                    // Placeholder for delete button space
                    Item {
                        width: EaStyle.Sizes.tableRowHeight
                    }

                    mouseArea.onPressed: {
                        if (constraintsTable.currentIndex !== index) {
                            constraintsTable.currentIndex = index
                        }
                    }
                }
            }

            // Delete buttons - separate from table content but positioned at row level
            Column {
                id: deleteButtonsColumn
                anchors.right: parent.right
                anchors.top: constraintsTable.top
                anchors.topMargin: constraintsTable.headerItem ? constraintsTable.headerItem.height : 0
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
    
