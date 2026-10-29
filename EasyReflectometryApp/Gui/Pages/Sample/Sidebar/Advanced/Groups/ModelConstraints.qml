import QtQuick
import QtQuick.Controls
import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    id: modelConstraintsGroup
    title: qsTr("Link contrasts")
    enabled: true
    last: true

    property var selectedModelIndices: []
    property int selectedModelsCount: selectedModelIndices.length
    readonly property var sortedSelection: selectedModelIndices.slice().sort((a, b) => a - b)

    // The model the others are tied to: the user's choice while it is selected, else the lowest selected.
    property int referenceModelIndex: -1
    readonly property int effectiveReferenceIndex: sortedSelection.indexOf(referenceModelIndex) >= 0
                                                   ? referenceModelIndex
                                                   : (sortedSelection.length ? sortedSelection[0] : -1)

    // Rows of the link preview (backend planModelLink). A row is ticked by its default unless
    // the user changed it: `rowOverrides` maps a row key to the user's tick.
    property var planRows: []
    property var planMessages: []
    property var rowOverrides: ({})
    readonly property var visiblePlanRows: planRows.filter(
        row => showUntieableCheckBox.checked || row.selectable || row.action === 'conflict')
    readonly property int tickedCount: planRows.filter(row => row.selectable && isRowTicked(row)).length

    // One row per model link, with its index in the full constraints list (for removal).
    readonly property var linkRows: {
        const rows = []
        const constraints = Globals.BackendWrapper.sampleConstraintsList || []
        for (let i = 0; i < constraints.length; i++) {
            if (constraints[i].type === 'link') {
                rows.push({ row: constraints[i], index: i })
            }
        }
        return rows
    }
    readonly property var currentLinkPairs: {
        const i = linksTable.currentIndex
        return i >= 0 && i < linkRows.length ? linkRows[i].row.pairs : []
    }

    function isRowTicked(row) {
        return rowOverrides.hasOwnProperty(row.key) ? rowOverrides[row.key] : row.selected
    }

    function setRowTicked(row, ticked) {
        const overrides = Object.assign({}, rowOverrides)
        overrides[row.key] = ticked
        rowOverrides = overrides
    }

    function setAllTicked(ticked) {
        const overrides = {}
        for (const row of planRows) {
            if (row.selectable) {
                overrides[row.key] = ticked
            }
        }
        rowOverrides = overrides
    }

    function tickedKeys() {
        return planRows.filter(row => row.selectable && isRowTicked(row)).map(row => row.key)
    }

    function refreshPlan() {
        if (selectedModelsCount < 2) {
            planRows = []
            planMessages = []
            return
        }
        const plan = Globals.BackendWrapper.samplePlanModelLink(
            selectedModelIndices, effectiveReferenceIndex, tieMaterialsCheckBox.checked)
        planRows = plan ? plan.rows : []
        planMessages = plan ? plan.messages : []
    }

    // Selection, reference and the project can change together; plan once for all of them.
    Timer {
        id: planTimer
        interval: 0
        onTriggered: modelConstraintsGroup.refreshPlan()
    }

    onSelectedModelIndicesChanged: planTimer.restart()
    onEffectiveReferenceIndexChanged: planTimer.restart()

    Connections {
        target: Globals.BackendWrapper
        // Linking, unlinking or editing constraints changes what can still be tied.
        function onSampleConstraintsListChanged() { planTimer.restart() }
        // Indices of a selection made before models were added or removed mean other models now.
        function onSampleModelNamesChanged() {
            modelConstraintsGroup.selectedModelIndices = []
            modelConstraintsGroup.rowOverrides = ({})
        }
    }

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.75
        width: parent ? parent.width : undefined

        EaElements.Label {
            width: parent.width
            text: qsTr("Tie the parameters of the selected models to those of the reference model, e.g. contrasts "
                       + "of one sample. Scale and background stay per model. Untick the parameters to leave free.")
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeForegroundMinor
        }

        // Models table
        Item {
            id: modelTableContainer
            width: parent.width
            height: Math.min(200, Math.max(60, modelsTable.height))

            EaComponents.TableView {
                id: modelsTable
                width: parent.width
                height: Math.min(200, Math.max(60, Math.max(modelsTable.contentHeight, modelsTable.implicitHeight)))
                enabled: Globals.BackendWrapper.sampleModelNames && Globals.BackendWrapper.sampleModelNames.length > 1

                defaultInfoText: qsTr("No Models Available")

                // Table model - use backend data directly
                model: Globals.BackendWrapper.sampleModelNames ? Globals.BackendWrapper.sampleModelNames.length : 0

                // Header row
                header: EaComponents.TableViewHeader {

                    EaComponents.TableViewLabel {
                        width: EaStyle.Sizes.fontPixelSize * 3
                        text: qsTr("Select")
                    }

                    EaComponents.TableViewLabel {
                        id: modelNameHeaderColumn
                        width: EaStyle.Sizes.fontPixelSize * 30
                        horizontalAlignment: Text.AlignLeft
                        text: qsTr("")
                    }
                }

                // Table rows
                delegate: EaComponents.TableViewDelegate {

                    EaElements.CheckBox {
                        id: modelCheckBox
                        width: EaStyle.Sizes.fontPixelSize * 3
                        checked: modelConstraintsGroup.selectedModelIndices.indexOf(index) >= 0
                        topPadding: 0
                        bottomPadding: 0
                        anchors.verticalCenter: parent.verticalCenter
                        onToggled: {
                            var newIndices = modelConstraintsGroup.selectedModelIndices.slice() // Copy the array
                            if (checked) {
                                newIndices.push(index)
                            } else {
                                const idx = newIndices.indexOf(index)
                                if (idx > -1) {
                                    newIndices.splice(idx, 1)
                                }
                            }
                            modelConstraintsGroup.selectedModelIndices = newIndices // Reassign to trigger update
                            checked = Qt.binding(() => modelConstraintsGroup.selectedModelIndices.indexOf(index) >= 0)
                        }
                    }

                    EaComponents.TableViewLabel {
                        id: modelNameColumn
                        width: EaStyle.Sizes.fontPixelSize * 30
                        horizontalAlignment: Text.AlignLeft
                        text: {
                            const modelName = Globals.BackendWrapper.sampleModelNames[index]
                            const reference = index === modelConstraintsGroup.effectiveReferenceIndex
                                              && modelConstraintsGroup.selectedModelsCount > 1
                            return modelName ? modelName + (reference ? qsTr("  (reference)") : "") : ""
                        }
                        elide: Text.ElideRight
                    }

                    mouseArea.onPressed: {
                        if (modelsTable.currentIndex !== index) {
                            modelsTable.currentIndex = index
                        }
                    }
                }
            }
        }

        Row {
            spacing: EaStyle.Sizes.fontPixelSize * 0.5

            EaElements.Label {
                anchors.verticalCenter: parent.verticalCenter
                enabled: modelConstraintsGroup.selectedModelsCount > 1
                text: qsTr("Reference model")
            }

            EaElements.ComboBox {
                id: referenceBox
                width: EaStyle.Sizes.fontPixelSize * 20
                enabled: modelConstraintsGroup.selectedModelsCount > 1
                model: modelConstraintsGroup.sortedSelection.map(index => Globals.BackendWrapper.sampleModelNames[index] || '')
                currentIndex: modelConstraintsGroup.sortedSelection.indexOf(modelConstraintsGroup.effectiveReferenceIndex)
                onActivated: {
                    modelConstraintsGroup.referenceModelIndex = modelConstraintsGroup.sortedSelection[currentIndex]
                    currentIndex = Qt.binding(() => modelConstraintsGroup.sortedSelection.indexOf(modelConstraintsGroup.effectiveReferenceIndex))
                }
            }
        }

        // Contrasts differ in their materials, so their SLDs are tied only on request.
        EaElements.CheckBox {
            id: tieMaterialsCheckBox
            checked: false
            text: qsTr("Also tie material SLDs and densities")
            ToolTip.text: qsTr("Leave unticked when the models are contrasts, i.e. differ in their materials")
            onToggled: {
                // The checkbox sets the material rows again; the user's other ticks stay.
                const overrides = Object.assign({}, modelConstraintsGroup.rowOverrides)
                for (const row of modelConstraintsGroup.planRows) {
                    if (row.action === 'undecided') {
                        delete overrides[row.key]
                    }
                }
                modelConstraintsGroup.rowOverrides = overrides
                planTimer.restart()
            }
        }

        // Link preview: what linking would tie, row by row
        EaElements.Label {
            visible: modelConstraintsGroup.selectedModelsCount > 1
            text: qsTr("Parameters to tie (%1 of %2 ticked)")
                      .arg(modelConstraintsGroup.tickedCount)
                      .arg(modelConstraintsGroup.planRows.filter(row => row.selectable).length)
        }

        EaComponents.TableView {
            id: planTable
            width: parent.width
            visible: modelConstraintsGroup.selectedModelsCount > 1
            maxRowCountShow: 8

            defaultInfoText: modelConstraintsGroup.planMessages.length ? qsTr("These models cannot be linked")
                                                                        : qsTr("Nothing to tie")

            model: modelConstraintsGroup.visiblePlanRows.length

            header: EaComponents.TableViewHeader {

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                    text: qsTr("Tie")
                }

                EaComponents.TableViewLabel {
                    flexibleWidth: true
                    horizontalAlignment: Text.AlignLeft
                    text: qsTr("Parameter")
                }

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.fontPixelSize * 12
                    horizontalAlignment: Text.AlignLeft
                    text: qsTr("Note")
                }
            }

            delegate: EaComponents.TableViewDelegate {
                property var planRow: modelConstraintsGroup.visiblePlanRows[index]

                EaComponents.TableViewCheckBox {
                    enabled: planRow !== undefined && planRow.selectable
                    checked: planRow !== undefined && planRow.selectable && modelConstraintsGroup.isRowTicked(planRow)
                    onToggled: {
                        modelConstraintsGroup.setRowTicked(planRow, checked)
                        checked = Qt.binding(() => planRow !== undefined && planRow.selectable
                                                   && modelConstraintsGroup.isRowTicked(planRow))
                    }
                }

                EaComponents.TableViewLabel {
                    horizontalAlignment: Text.AlignLeft
                    text: planRow ? planRow.name : ""
                    color: planRow && planRow.selectable ? EaStyle.Colors.themeForeground : EaStyle.Colors.themeForegroundMinor
                    elide: Text.ElideRight
                    ToolTip.text: planRow ? planRow.path : ""
                }

                EaComponents.TableViewLabel {
                    horizontalAlignment: Text.AlignLeft
                    text: planRow ? planRow.reason : ""
                    color: planRow && planRow.action === 'conflict' ? EaStyle.Colors.themeAccent : EaStyle.Colors.themeForegroundMinor
                    elide: Text.ElideRight
                    ToolTip.text: planRow ? planRow.reason : ""
                }
            }
        }

        Row {
            visible: modelConstraintsGroup.selectedModelsCount > 1
            spacing: EaStyle.Sizes.fontPixelSize

            EaElements.SideBarButton {
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 2
                enabled: modelConstraintsGroup.planRows.some(row => row.selectable)
                fontIcon: "check-square"
                text: qsTr("Tick all")
                onClicked: modelConstraintsGroup.setAllTicked(true)
            }

            EaElements.SideBarButton {
                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 2
                enabled: modelConstraintsGroup.tickedCount > 0
                fontIcon: "square"
                text: qsTr("Untick all")
                onClicked: modelConstraintsGroup.setAllTicked(false)
            }
        }

        EaElements.CheckBox {
            id: showUntieableCheckBox
            visible: modelConstraintsGroup.selectedModelsCount > 1
            checked: false
            text: qsTr("Show the parameters that cannot be tied")
        }

        EaElements.SideBarButton {
            id: constrainModelsButton
            wide: true
            fontIcon: "link"
            text: qsTr("Link selected models")
            enabled: modelConstraintsGroup.selectedModelsCount > 1 && modelConstraintsGroup.tickedCount > 0
            onClicked: {
                const result = Globals.BackendWrapper.sampleLinkModels(
                    modelConstraintsGroup.selectedModelIndices,
                    modelConstraintsGroup.effectiveReferenceIndex,
                    tieMaterialsCheckBox.checked,
                    modelConstraintsGroup.tickedKeys())
                linkResult.text = result
                    ? qsTr("%1 parameter(s) tied.").arg(result.tied)
                      + (result.messages.length ? '\n' + result.messages.join('\n') : '')
                    : ''
                modelConstraintsGroup.rowOverrides = ({})
            }
        }

        // Why the selected models cannot be linked (layouts differ, ...)
        EaElements.Label {
            width: parent.width
            visible: modelConstraintsGroup.selectedModelsCount > 1 && text !== ''
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeAccent
            text: modelConstraintsGroup.planMessages.join('\n')
        }

        EaElements.Label {
            id: linkResult
            width: parent.width
            visible: text !== ''
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeForegroundMinor
        }

        // Model links: one row per link; selecting one lists its ties below
        Item {
            height: EaStyle.Sizes.fontPixelSize * 0.5
            width: 1
        }

        EaElements.Label {
            enabled: true
            text: qsTr("Model links")
        }

        EaComponents.TableView {
            id: linksTable
            width: parent.width

            defaultInfoText: qsTr("No Model Links")

            model: modelConstraintsGroup.linkRows.length

            header: EaComponents.TableViewHeader {

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                    text: qsTr("No.")
                }

                EaComponents.TableViewLabel {
                    flexibleWidth: true
                    horizontalAlignment: Text.AlignLeft
                    text: qsTr("Link")
                }

                // Placeholder for row delete button
                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.tableRowHeight
                }
            }

            delegate: EaComponents.TableViewDelegate {
                property var link: modelConstraintsGroup.linkRows[index]

                EaComponents.TableViewLabel {
                    text: index + 1
                    color: EaStyle.Colors.themeForegroundMinor
                }

                EaComponents.TableViewLabel {
                    horizontalAlignment: Text.AlignLeft
                    text: link ? qsTr("%1 → %2 (%3 tied)").arg(link.row.dependentName).arg(link.row.referenceName).arg(link.row.count) : ""
                    elide: Text.ElideRight
                    ToolTip.text: link ? link.row.members.join(", ") : ""
                }

                EaComponents.TableViewButton {
                    fontIcon: "minus-circle"
                    ToolTip.text: qsTr("Remove this link: every tied parameter gets back its value from before the link")
                    onClicked: Globals.BackendWrapper.sampleRemoveConstraintByIndex(link.index)
                }

                mouseArea.onPressed: {
                    if (linksTable.currentIndex !== index) {
                        linksTable.currentIndex = index
                    }
                }
            }
        }

        EaElements.Label {
            visible: modelConstraintsGroup.currentLinkPairs.length > 0
            text: {
                const i = linksTable.currentIndex
                return i >= 0 && i < modelConstraintsGroup.linkRows.length
                       ? qsTr("Tied parameters of link %1").arg(i + 1) : ""
            }
        }

        EaComponents.TableView {
            id: linkPairsTable
            width: parent.width
            visible: modelConstraintsGroup.currentLinkPairs.length > 0
            maxRowCountShow: 8

            model: modelConstraintsGroup.currentLinkPairs.length

            header: EaComponents.TableViewHeader {

                EaComponents.TableViewLabel {
                    flexibleWidth: true
                    horizontalAlignment: Text.AlignLeft
                    text: qsTr("Parameter")
                }

                // Placeholder for row delete button
                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.tableRowHeight
                }
            }

            delegate: EaComponents.TableViewDelegate {
                property var pair: modelConstraintsGroup.currentLinkPairs[index]

                EaComponents.TableViewLabel {
                    horizontalAlignment: Text.AlignLeft
                    text: pair ? pair.name : ""
                    elide: Text.ElideRight
                }

                EaComponents.TableViewButton {
                    fontIcon: "minus-circle"
                    ToolTip.text: qsTr("Untie this parameter: it gets back its value from before the link")
                    onClicked: Globals.BackendWrapper.sampleRemoveLinkedParameter(pair.uniqueName)
                }
            }
        }
    }
}
