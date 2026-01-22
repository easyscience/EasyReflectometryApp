import QtQuick 2.14
import QtQuick.Controls 2.14

import easyApp.Gui.Style as EaStyle
import easyApp.Gui.Elements as EaElements
import easyApp.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    title: selectedExperimentIndices.length <= 1 ?
           qsTr("Data Explorer") :
           qsTr("Data Explorer (%1 selected)").arg(selectedExperimentIndices.length)
    visible: true
    collapsed: false

    // Track selection state locally and keep backend in sync
    property var selectedExperimentIndices: []
    property bool wasMultiSelected: false

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        // Multi-selection controls (mirrors ExperimentalDataExplorer)
        Row {
            spacing: EaStyle.Sizes.fontPixelSize * 0.5
            visible: Globals.BackendWrapper.analysisExperimentsAvailable.length > 1

            EaElements.Label {
                text: qsTr("Ctrl+Click for multi-select")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.75
                color: EaStyle.Colors.themeForegroundMinor
                anchors.verticalCenter: parent.verticalCenter
            }

            EaElements.TabButton {
                height: EaStyle.Sizes.fontPixelSize * 1.5
                width: height * 2
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "check-double"
                ToolTip.text: qsTr("Select all experiments")
                enabled: selectedExperimentIndices.length < Globals.BackendWrapper.analysisExperimentsAvailable.length
                onClicked: selectAllExperiments()
            }

            EaElements.TabButton {
                height: EaStyle.Sizes.fontPixelSize * 1.5
                width: height * 2
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "times"
                ToolTip.text: qsTr("Clear selection")
                enabled: selectedExperimentIndices.length > 1
                onClicked: {
                    clearAllSelections()
                    if (Globals.BackendWrapper.analysisExperimentsAvailable.length > 0) {
                        selectSingleExperiment(0)
                    }
                }
            }

            EaElements.Label {
                visible: selectedExperimentIndices.length > 1 &&
                         selectedExperimentIndices.length < Globals.BackendWrapper.analysisExperimentsAvailable.length
                text: qsTr("Selected: %1").arg(selectedExperimentIndices.map(i => i + 1).join(", "))
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.7
                color: EaStyle.Colors.themeAccent
                anchors.verticalCenter: parent.verticalCenter
            }

            EaElements.Label {
                visible: selectedExperimentIndices.length > 1 &&
                         selectedExperimentIndices.length === Globals.BackendWrapper.analysisExperimentsAvailable.length
                text: qsTr("All experiments selected")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.7
                color: EaStyle.Colors.themeForegroundHovered
                anchors.verticalCenter: parent.verticalCenter
            }
        }

        Row {
            spacing: EaStyle.Sizes.fontPixelSize

            EaComponents.TableView {
                id: dataTable
                defaultInfoText: qsTr("No Experiments Loaded")
                model: Globals.BackendWrapper.analysisExperimentsAvailable.length

                onModelChanged: {
                    if (model === 0) {
                        clearAllSelections()
                    } else {
                        var validSelection = []
                        for (var i = 0; i < selectedExperimentIndices.length; i++) {
                            if (selectedExperimentIndices[i] < model) {
                                validSelection.push(selectedExperimentIndices[i])
                            }
                        }
                        if (validSelection.length !== selectedExperimentIndices.length) {
                            selectedExperimentIndices = validSelection
                            if (validSelection.length === 0 && model > 0) {
                                selectSingleExperiment(0)
                            } else {
                                updateBackendWithSelectedExperiments()
                            }
                        }
                    }
                }

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

                    EaComponents.TableViewLabel {
                        id: colorLab
                        text: "Color"
                        width: EaStyle.Sizes.fontPixelSize * 2.5
                    }
                }

                delegate: EaComponents.TableViewDelegate {
                    property bool isSelected: selectedExperimentIndices.indexOf(index) !== -1

                    EaComponents.TableViewLabel {
                        id: noLabel
                        width: EaStyle.Sizes.fontPixelSize * 2.5
                        text: index + 1

                        Rectangle {
                            visible: isSelected
                            anchors.fill: parent.parent
                            color: EaStyle.Colors.themeForegroundHovered
                            opacity: 0.2
                            z: -1

                            Rectangle {
                                anchors.left: parent.left
                                anchors.verticalCenter: parent.verticalCenter
                                width: 3
                                height: parent.height * 0.8
                                color: EaStyle.Colors.themeAccent
                            }
                        }
                    }

                    EaComponents.TableViewTextInput {
                        horizontalAlignment: Text.AlignLeft
                        id: labelLabel
                        width: EaStyle.Sizes.fontPixelSize * 11
                        text: index > -1 ? Globals.BackendWrapper.analysisExperimentsAvailable[index] : ""
                        onEditingFinished: Globals.BackendWrapper.analysisSetExperimentNameAtIndex(index, text)
                    }

                    EaComponents.TableViewLabel {
                        id: modelAccess
                        text: Globals.BackendWrapper.modelNamesForExperiment[model.index] || ""
                    }

                    EaComponents.TableViewLabel {
                        id: colorLabel
                        backgroundColor: Globals.BackendWrapper.modelColorsForExperiment[model.index]
                    }

                    mouseArea.onPressed: (mouse) => {
                        if (mouse.modifiers & Qt.ControlModifier) {
                            toggleExperimentSelection(index)
                        } else {
                            selectSingleExperiment(index)
                        }
                    }
                }
            }
        }
    }

    function toggleExperimentSelection(experimentIndex) {
        var currentSelection = selectedExperimentIndices.slice()
        var indexPos = currentSelection.indexOf(experimentIndex)

        if (indexPos !== -1) {
            currentSelection.splice(indexPos, 1)
        } else {
            currentSelection.push(experimentIndex)
        }

        if (currentSelection.length > 1) {
            wasMultiSelected = true
        }

        selectedExperimentIndices = currentSelection
        updateBackendWithSelectedExperiments()
    }

    function selectSingleExperiment(experimentIndex) {
        selectedExperimentIndices = [experimentIndex]
        updateBackendWithSelectedExperiments()
    }

    function selectAllExperiments() {
        var allIndices = []
        for (var i = 0; i < Globals.BackendWrapper.analysisExperimentsAvailable.length; i++) {
            allIndices.push(i)
        }
        wasMultiSelected = true
        selectedExperimentIndices = allIndices
        updateBackendWithSelectedExperiments()
    }

    function clearAllSelections() {
        wasMultiSelected = false
        selectedExperimentIndices = []
        // Don't send empty array to backend - let subsequent selection handle it
    }

    function updateBackendWithSelectedExperiments() {
        if (selectedExperimentIndices.length === 0) {
            return
        }

        // console.log(`📊 Updating backend with selection: [${selectedExperimentIndices.join(', ')}]`)
        Globals.BackendWrapper.analysisSetSelectedExperimentIndices(selectedExperimentIndices)

        var primaryIndex = selectedExperimentIndices[0]

        if (selectedExperimentIndices.length === 1) {
            if (wasMultiSelected) {
                var tempIndex = (primaryIndex === 0) ? 1 : 0
                if (tempIndex < Globals.BackendWrapper.analysisExperimentsAvailable.length) {
                    Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(tempIndex)
                }
                wasMultiSelected = false
            }
            Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(primaryIndex)
        } else {
            wasMultiSelected = true
            Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(primaryIndex)
        }

        var modelIndexFromExperiment = Globals.BackendWrapper.analysisModelForExperiment
        Globals.BackendWrapper.sampleSetCurrentModelIndex(modelIndexFromExperiment)
    }

    Component.onCompleted: {
        if (Globals.BackendWrapper.analysisExperimentsAvailable.length > 0) {
            selectSingleExperiment(0)
        }
    }
}
