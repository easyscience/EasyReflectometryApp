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

            }

            delegate: EaComponents.TableViewDelegate {
                //property var dataModel: model

                EaComponents.TableViewLabel {
                    id: noLabel
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                    text: index + 1
                }

                EaComponents.TableViewTextInput {
                    horizontalAlignment: Text.AlignLeft
                    id: labelLabel
                    width: EaStyle.Sizes.fontPixelSize * 11
                    text: index > -1 ? Globals.BackendWrapper.analysisExperimentsAvailable[index] : ""
                }

                EaComponents.TableViewLabel {
                    id: modelAccess
                    property string modelName: {
                        if (Globals.BackendWrapper.modelForExperiment &&
                            model.index < Globals.BackendWrapper.modelForExperiment.length) {
                            return Globals.BackendWrapper.modelForExperiment[model.index] || ""
                        }
                        return ""
                    }
                    text: modelName

                    // Force an update when experiments change
                    Connections {
                        target: Globals.BackendWrapper
                        function onexperimentsChanged() {
                            // Trigger property re-evaluation
                            modelAccess.modelName = Qt.binding(function() {
                                if (Globals.BackendWrapper.modelForExperiment &&
                                    model.index < Globals.BackendWrapper.modelForExperiment.length) {
                                    return Globals.BackendWrapper.modelForExperiment[model.index] || ""
                                }
                                return ""
                            })
                        }
                    }
                }

                // Fix colorLabel similarly - though you need to get color from somewhere
                EaComponents.TableViewLabel {
                    id: colorLabel
                    // You'll need a way to map model names to colors, or modify your Python code
                    // to include color information
                    backgroundColor: {
                        var i = modelAccess.currentIndex || 0
                        console.error("Current index:", i)
                        console.error("Current model:", Globals.BackendWrapper.sampleModels[i])
                        Globals.BackendWrapper.sampleModels[i].color || "lightgray"
                    }
                }

                // EaComponents.TableViewLabel {
                //     id: modelAccess
                //     // model: Globals.BackendWrapper.modelForExperiment
                //     text: {
                //         return Globals.BackendWrapper.modelForExperiment[model.index] || ""
                //     }
                //     // Use Connections to force an update when experimentsChanged signal is emitted
                //     Connections {
                //         target: Globals.BackendWrapper
                //         function onExperimentsChanged() {
                //             // Force a re-evaluation of the text binding
                //             modelAccess.text = Qt.binding(function() {
                //                 return Globals.BackendWrapper.modelForExperiment[model.index] || ""
                //             })
                //         }
                //     }
                // }

                // EaComponents.TableViewLabel {
                //     id: colorLabel
                //     backgroundColor:  {
                //         //Globals.BackendWrapper.modelForExperiment[model.index].color
                //         Globals.BackendWrapper.sampleModels[model.index].color
                //     }
                // }

                mouseArea.onPressed: {
                    Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(model.index)
                }

            }
        }
    }
}
