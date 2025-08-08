import QtQuick 2.14
import QtQuick.Controls 2.14

import easyApp.Gui.Style as EaStyle
import easyApp.Gui.Elements as EaElements
import easyApp.Gui.Components as EaComponents

//import Gui.Globals 1.0 as ExGlobals
import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Data Explorer")
    visible: true
    collapsed: false
    Row {
        spacing: EaStyle.Sizes.fontPixelSize

        EaComponents.TableView {
            id: dataTable
            defaultInfoText: qsTr("No Experiments Loaded")
            model: Globals.BackendWrapper.analysisExperimentsAvailable.length

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
                    text: "Model"
                }

                // Placeholder for row color
                EaComponents.TableViewLabel {
                    id: colorLab
                    text: "Color"
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                }

                // Placeholder for row delete button
                EaComponents.TableViewLabel {
                    text: "Del."
                    width: EaStyle.Sizes.tableRowHeight
                }
            }

            delegate: EaComponents.TableViewDelegate {
                //property var dataModel: model

                EaComponents.TableViewLabel {
                    id: noLabel
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                    //text: model.index ? model.index : ""
                    text: index + 1
                }

                EaComponents.TableViewTextInput {
                    horizontalAlignment: Text.AlignLeft
                    id: labelLabel
                    width: EaStyle.Sizes.fontPixelSize * 11
                    text: index > -1 ? Globals.BackendWrapper.analysisExperimentsAvailable[index] : ""
                    //onEditingFinished: ExGlobals.Constants.proxy.data.setCurrentExperimentDatasetName(text)
                }

                EaComponents.TableViewComboBox {
                    id: modelAccess
                    horizontalAlignment: Text.AlignLeft
                    width: EaStyle.Sizes.sideBarContentWidth - (noLabel.width + deleteRowColumn.width + colorLabel.width + labelLabel.width + 5 * EaStyle.Sizes.tableColumnSpacing)
                    //headerText: "Model"
                    model: Globals.BackendWrapper.sampleModelNames
                    onActivated: {
                        Globals.BackendWrapper.analysisSetModelOnExperiment(currentIndex)
                    }
                    Component.onCompleted: {
                        currentIndex = 0//indexOfValue(Globals.BackendWrapper.sampleModels[index].name)
                    }
                }

                EaComponents.TableViewLabel {
                    id: colorLabel
                    backgroundColor: Globals.BackendWrapper.sampleModels[modelAccess.currentIndex].color
                }

                EaComponents.TableViewButton {
                    id: deleteRowColumn
                    fontIcon: "minus-circle"
                    ToolTip.text: qsTr("Remove this dataset")
                    onClicked: {
                        Globals.BackendWrapper.analysisRemoveExperiment(index)
                    }
                }
                mouseArea.onPressed: {
                    // Set the current experiment index in the backend
                    if (Globals.BackendWrapper.analysisExperimentsCurrentIndex !== model.index) {
                        Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(model.index)
                    }
                }

            }
            // onCurrentIndexChanged: {
            //     Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(model.index)
            // }

        }
    }
}
