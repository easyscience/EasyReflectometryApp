import QtQuick 2.14
import QtQuick.Controls 2.14

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

//import Gui.Globals 1.0 as ExGlobals
import Gui.Globals as Globals

EaElements.GroupBox {
    title: selectedExperimentIndices.length <= 1 ? 
           qsTr("Data Explorer") : 
           qsTr("Data Explorer (%1 selected)").arg(selectedExperimentIndices.length)
    visible: true
    collapsed: false
    
    // Property to track selected experiment indices for multi-selection
    property var selectedExperimentIndices: []
    // Property to track if we were in multi-selection mode
    property bool wasMultiSelected: false
    
    // Watch for changes in selection to automatically disable staggered mode
    onSelectedExperimentIndicesChanged: {
        if (selectedExperimentIndices.length <= 1 && Globals.Variables.useStaggeredPlotting) {
            console.log(`🔄 Selection changed to single experiment - disabling staggered plotting`)
            Globals.Variables.useStaggeredPlotting = false
        }
    }
    
    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5
        
        // Multi-selection controls
        Row {
            spacing: EaStyle.Sizes.fontPixelSize * 0.5
            visible: Globals.BackendWrapper.analysisExperimentsAvailable.length > 1
            
            // Helper text for multi-selection
            EaElements.Label {
                text: qsTr("Ctrl+Click for multi-select")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.75
                color: EaStyle.Colors.themeForegroundMinor
                anchors.verticalCenter: parent.verticalCenter
            }
            
            // Select all button
            EaElements.TabButton {
                height: EaStyle.Sizes.fontPixelSize * 1.5
                width: height * 2
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "check-double"
                ToolTip.text: qsTr("Select all experiments")
                onClicked: selectAllExperiments()
                enabled: selectedExperimentIndices.length < Globals.BackendWrapper.analysisExperimentsAvailable.length
            }
            
            // Clear selection button
            EaElements.TabButton {
                height: EaStyle.Sizes.fontPixelSize * 1.5
                width: height * 2
                borderColor: EaStyle.Colors.chartAxis
                fontIcon: "times"
                ToolTip.text: qsTr("Clear selection")
                onClicked: {
                    clearAllSelections()
                    if (Globals.BackendWrapper.analysisExperimentsAvailable.length > 0) {
                        selectSingleExperiment(0)
                    }
                }
                enabled: selectedExperimentIndices.length > 1
            }
            
            // Status indicator
            EaElements.Label {
                text: selectedExperimentIndices.length > 1 ? 
                      qsTr("Selected: %1").arg(selectedExperimentIndices.map(i => i + 1).join(", ")) :
                      ""
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.7
                color: EaStyle.Colors.themeAccent
                anchors.verticalCenter: parent.verticalCenter
                visible: selectedExperimentIndices.length > 1
            }
        }

        // Staggered plotting toggle
        Row {
            spacing: EaStyle.Sizes.fontPixelSize * 0.5
            visible: selectedExperimentIndices.length > 1

            EaElements.CheckBox {
                id: staggeredPlottingCheckbox
                enabled: selectedExperimentIndices.length > 1
                checked: Globals.Variables.useStaggeredPlotting && selectedExperimentIndices.length > 1
                text: qsTr("Staggered view")
                font.pixelSize: EaStyle.Sizes.fontPixelSize * 0.75
                ToolTip.text: qsTr("Vertically offset experiment lines for easier comparison")
                onCheckedChanged: {
                    if (selectedExperimentIndices.length > 1) {
                        Globals.Variables.useStaggeredPlotting = checked
                        console.log(`📊 Staggered plotting mode changed to: ${checked}`)
                        console.log(`🔄 Updating backend with multi-experiment selection`)
                        updateBackendWithSelectedExperiments()
                    } else {
                        console.log(`⚠️ Single experiment mode - staggering not applicable`)
                    }
                }
            }

            // Staggering distance slider
            EaElements.Slider {
                id: staggeringSlider
                width: EaStyle.Sizes.fontPixelSize * 6
                anchors.verticalCenter: parent.verticalCenter
                from: 0.0
                to: 5.0
                value: Globals.Variables.staggeringFactor !== undefined ? Globals.Variables.staggeringFactor : 0.5
                stepSize: 0.05
                enabled: staggeredPlottingCheckbox.checked && selectedExperimentIndices.length > 1
                ToolTip.text: "Adjust staggering distance (" + Number(value).toFixed(2) + ")"
                ToolTip.visible: hovered

                onValueChanged: {
                    // Always update the global variable to trigger watchers
                    Globals.Variables.staggeringFactor = value
                    // console.log(`📏 Staggering factor changed to: ${value.toFixed(2)}`)
                }
            }
        }

        Row {
            spacing: EaStyle.Sizes.fontPixelSize

            EaComponents.TableView {
                id: dataTable
                defaultInfoText: qsTr("No Experiments Loaded")
                model: Globals.BackendWrapper.analysisExperimentsAvailable.length
                
                // Watch for model changes and update selection accordingly
                onModelChanged: {
                    if (model === 0) {
                        clearAllSelections()
                    } else {
                        // Remove any selected indices that are now out of range
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
                }            // Headers
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
                
                // Property to track if this row is selected
                property bool isSelected: {
                    for (var i = 0; i < selectedExperimentIndices.length; i++) {
                        if (selectedExperimentIndices[i] === index) {
                            return true
                        }
                    }
                    return false
                }

                EaComponents.TableViewLabel {
                    id: noLabel
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                    text: index + 1
                    
                    // Selection background overlay - placed as child to avoid layout interference
                    Rectangle {
                        visible: isSelected
                        anchors.fill: parent
                        color: EaStyle.Colors.themeForegroundHovered
                        opacity: 0.2
                        z: -1
                        
                        // Visual selection indicator bar
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

                    // Always show each experiment in its distinct palette color
                    color: Globals.Variables.experimentColor(index)
                    font.bold: true
                }

                EaComponents.TableViewComboBox {
                    id: modelAccess
                    horizontalAlignment: Text.AlignLeft
                    width: EaStyle.Sizes.sideBarContentWidth - (noLabel.width + deleteRowColumn.width + colorLabel.width + labelLabel.width + 5 * EaStyle.Sizes.tableColumnSpacing)
                    model: Globals.BackendWrapper.sampleModelNames
                    onActivated: {
                        Globals.BackendWrapper.analysisSetModelOnExperiment(currentIndex)
                    }
                    Component.onCompleted: {
                        Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(model.index)
                        Globals.BackendWrapper.analysisSetModelOnExperiment(model.index)
                        currentIndex = 0
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
                mouseArea.onPressed: (mouse) => {
                    // Handle multi-selection with Ctrl key
                    if (mouse.modifiers & Qt.ControlModifier) {
                        // Multi-selection mode: toggle selection of this experiment
                        toggleExperimentSelection(index)
                    } else {
                        // Single selection mode: select only this experiment
                        selectSingleExperiment(index)
                    }
                }

            }
            // onCurrentIndexChanged: {
            //     Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(model.index)
            // }

            }
        }
    }
    
    /*
     * MULTI-EXPERIMENT SELECTION IMPLEMENTATION
     * 
     * This QML implementation provides the UI for selecting multiple experiments
     * and concatenating their data for plotting. To complete the functionality,
     * the following backend methods need to be implemented:
     * 
     * 1. Globals.BackendWrapper.analysisSetSelectedExperimentIndices(indices: list)
     *    - Store the list of selected experiment indices
     *    - Concatenate data from all selected experiments
     *    - Update plotting data to show combined datasets
     * 
     * 2. Globals.BackendWrapper.analysisExperimentsSelectedCount (property)
     *    - Return the count of currently selected experiments
     *    - Used for UI feedback (legend, title, etc.)
     * 
     * 3. Backend plotting concatenation logic:
     *    - Combine q-values, intensities, and errors from selected experiments
     *    - Handle potential overlapping q-ranges appropriately
     *    - Maintain proper error propagation for combined datasets
     *    - Update plot bounds (min/max X/Y) for concatenated data
     * 
     * Current behavior:
     * - Single selection works with existing backend
     * - Multi-selection logs selected indices to console
     * - Visual feedback works in UI (selection highlighting, counters)
     */
    
    // Functions to handle multi-selection
    function toggleExperimentSelection(experimentIndex) {
        var currentSelection = selectedExperimentIndices.slice() // Create a copy
        var indexPos = currentSelection.indexOf(experimentIndex)
        
        if (indexPos !== -1) {
            // Remove from selection
            currentSelection.splice(indexPos, 1)
        } else {
            // Add to selection
            currentSelection.push(experimentIndex)
        }

        // Track if we now have multiple selections
        if (currentSelection.length > 1) {
            wasMultiSelected = true
        }

        selectedExperimentIndices = currentSelection
        updateBackendWithSelectedExperiments()
    }
    
    function selectSingleExperiment(experimentIndex) {
        // console.log("selectSingleExperiment called with index:", experimentIndex)
        selectedExperimentIndices = [experimentIndex]
        // console.log("Updated selectedExperimentIndices to:", selectedExperimentIndices)
        updateBackendWithSelectedExperiments()
    }
    
    function updateBackendWithSelectedExperiments() {
        if (selectedExperimentIndices.length === 0) {
            return
        }

        // Always notify backend of the current selection (single or multi)
        Globals.BackendWrapper.analysisSetSelectedExperimentIndices(selectedExperimentIndices)

        if (selectedExperimentIndices.length === 1) {
            var currentIndex = selectedExperimentIndices[0]

            // If we were in multi-selection mode and now switching to single selection,
            // force a plot refresh by toggling the current index
            if (wasMultiSelected) {
                var tempIndex = (currentIndex === 0) ? 1 : 0
                if (tempIndex < Globals.BackendWrapper.analysisExperimentsAvailable.length) {
                    Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(tempIndex)
                }
                Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(currentIndex)
                wasMultiSelected = false
            } else {
                // Normal single selection
                Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(currentIndex)
            }
        } else {
            // Mark that we're in multi-selection mode
            wasMultiSelected = true
            Globals.BackendWrapper.analysisSetExperimentsCurrentIndex(selectedExperimentIndices[0])
        }
    }
    
    function clearAllSelections() {
        wasMultiSelected = false
        selectedExperimentIndices = []
        Globals.BackendWrapper.analysisSetSelectedExperimentIndices([])
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
    
    // Initialize with first experiment selected by default
    Component.onCompleted: {
        if (Globals.BackendWrapper.analysisExperimentsAvailable.length > 0) {
            selectSingleExperiment(0)
        }
    }
}
