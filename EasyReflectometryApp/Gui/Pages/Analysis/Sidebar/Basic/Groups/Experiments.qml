import QtQuick 2.14
import QtQuick.Controls 2.14

import easyApp.Gui.Style as EaStyle
import easyApp.Gui.Elements as EaElements
import easyApp.Gui.Components as EaComponents

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
                    text: {
                        return Globals.BackendWrapper.modelNamesForExperiment[model.index] || ""
                    }
                }

                EaComponents.TableViewLabel {
                    id: colorLabel
                    backgroundColor:  {
                        Globals.BackendWrapper.modelColorsForExperiment[model.index]
                    }
                }

                mouseArea.onPressed: {
                    Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(model.index)
                    var modelIndexFromExperiment = Globals.BackendWrapper.analysisModelForExperiment
                    Globals.BackendWrapper.sampleSetCurrentModelIndex(modelIndexFromExperiment)
                }

            }
        }
    }
}
