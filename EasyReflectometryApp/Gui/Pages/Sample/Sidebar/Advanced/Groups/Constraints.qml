import QtQuick
import QtQuick.Controls
import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    id: constraintsGroup
    title: qsTr("Single constraints")
    enabled: true
    last: false

    property bool expressionValid: false
    property string validationMessage: ""
    property string expressionPreview: ""
    property string lastConstraintType: ""
    property bool validationDirty: false

    function currentRelationValue() {
        if (relationalOperator.currentIndex === -1 || typeof relationalOperator.currentValue === 'undefined') {
            return '='
        }
        return relationalOperator.currentValue
    }

    function resetValidation() {
        validationMessage = ""
        expressionPreview = ""
        lastConstraintType = ""
        expressionValid = false
        validationDirty = false
    }

    function scheduleValidation() {
        validationDirty = true
        validationTimer.restart()
    }

    function runValidation() {
        if (!validationDirty) {
            return
        }

        if (dependentPar.currentIndex === -1) {
            expressionValid = false
            expressionPreview = ""
            lastConstraintType = ""
            validationMessage = qsTr("Select a dependent parameter.")
            return
        }

        const expr = expressionEditor.text ? expressionEditor.text.trim() : ""
        if (expr.length === 0) {
            expressionValid = false
            expressionPreview = ""
            lastConstraintType = ""
            validationMessage = qsTr("Expression cannot be empty.")
            return
        }

        if (typeof Globals.BackendWrapper.sampleValidateConstraintExpression === 'function') {
            const result = Globals.BackendWrapper.sampleValidateConstraintExpression(
                                    dependentPar.currentIndex,
                                    currentRelationValue(),
                                    expressionEditor.text)
            if (result && result.valid) {
                expressionValid = true
                validationMessage = ""
                expressionPreview = result.preview || expr
                lastConstraintType = result.type || 'expression'
            } else {
                expressionValid = false
                expressionPreview = ""
                lastConstraintType = ""
                validationMessage = result && result.message ? result.message : qsTr("Expression is not valid.")
                // Debug: show available parameters when validation fails
                if (result && result.message && result.message.includes("not defined")) {
                    console.log("Available constraint parameters:")
                    const params = Globals.BackendWrapper.sampleConstraintParametersMetadata
                    for (let i = 0; i < params.length; i++) {
                        console.log(`  ${params[i].alias}: ${params[i].displayName}`)
                    }
                }
            }
        } else {
            expressionValid = true
            validationMessage = ""
            expressionPreview = expr
            lastConstraintType = 'expression'
        }
    }

    function insertAlias(aliasText) {
        if (!aliasText || aliasText.length === 0) {
            return
        }

        const position = expressionEditor.cursorPosition
        const sourceText = expressionEditor.text
        const before = sourceText.slice(0, position)
        const after = sourceText.slice(position)
        const needsLeadingSpace = before.length > 0 && !before.slice(-1).match(/[\s(*/+-]/)
        const prefix = needsLeadingSpace ? before + ' ' : before
        const needsTrailingSpace = after.length > 0 && !after.slice(0, 1).match(/[\s)*/+-]/)
        const suffix = needsTrailingSpace ? ' ' + after : after
        expressionEditor.text = prefix + aliasText + suffix
        expressionEditor.cursorPosition = prefix.length + aliasText.length
        scheduleValidation()
    }

    function resetForm() {
        validationTimer.stop()
        dependentPar.currentIndex = -1
        relationalOperator.currentIndex = relationalOperator.model && relationalOperator.model.length > 0 ? 0 : -1
        expressionEditor.text = ""
        parameterInsert.currentIndex = -1
        resetValidation()
    }

    Timer {
        id: validationTimer
        interval: 320
        repeat: false
        onTriggered: constraintsGroup.runValidation()
    }

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.75
        width: parent ? parent.width : undefined

        EaElements.Label {
            width: parent.width
            text: qsTr("Create numeric or symbolic relationships between parameters.")
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeForegroundMinor
        }

        Row {
            id: parameterRow
            spacing: EaStyle.Sizes.fontPixelSize * 0.5
            width: parent.width

            EaElements.ComboBox {
                id: dependentPar
                width: Math.max(0, parameterRow.width - relationalOperator.width - parameterRow.spacing)
                currentIndex: -1
                displayText: currentIndex === -1 ? qsTr("Select dependent parameter") : currentText
                model: Globals.BackendWrapper.sampleDepParameterNames
                onCurrentIndexChanged: constraintsGroup.scheduleValidation()
            }

            EaElements.ComboBox {
                id: relationalOperator
                width: EaStyle.Sizes.fontPixelSize * 4
                valueRole: "value"
                textRole: "text"
                displayText: currentIndex === -1 ? qsTr("=") : currentText
                model: Globals.BackendWrapper.sampleRelationOperators
                onCurrentIndexChanged: constraintsGroup.scheduleValidation()
                Component.onCompleted: {
                    if (model && model.length > 0) {
                        currentIndex = 0
                    }
                }
            }
        }

        EaElements.TextArea {
            id: expressionEditor
            width: parent.width
            placeholderText: qsTr("Enter expression, e.g. np.sqrt(1 / sld_ni) + 4")
            wrapMode: TextEdit.WrapAnywhere
            selectByMouse: true
            onTextChanged: constraintsGroup.scheduleValidation()
        }

        EaElements.ComboBox {
            id: parameterInsert
            width: parent.width
            valueRole: "alias"
            textRole: "displayName"
            displayText: {
                if (currentIndex === -1) {
                    return qsTr("Insert parameter alias…")
                }
                const entry = model && model[currentIndex]
                if (!entry) {
                    return qsTr("Insert parameter alias…")
                }
                const alias = entry.alias || ""
                const name = entry.displayName || alias
                return alias ? name + " (" + alias + ")" : name
            }
            model: Globals.BackendWrapper.sampleConstraintParametersMetadata
            onActivated: {
                constraintsGroup.insertAlias(currentValue)
                Qt.callLater(() => parameterInsert.currentIndex = -1)
            }
        }

        EaElements.Label {
            id: previewLabel
            width: parent.width
            visible: constraintsGroup.expressionValid && constraintsGroup.expressionPreview.length > 0
            text: qsTr("Preview: %1 %2").arg(constraintsGroup.currentRelationValue()).arg(constraintsGroup.expressionPreview)
            color: EaStyle.Colors.themeForegroundMinor
            wrapMode: Text.Wrap
        }

        EaElements.Label {
            id: validationLabel
            width: parent.width
            visible: !constraintsGroup.expressionValid && constraintsGroup.validationDirty && constraintsGroup.validationMessage.length > 0
            text: constraintsGroup.validationMessage
            color: EaStyle.Colors.themeAccent
            wrapMode: Text.Wrap
        }

        EaElements.SideBarButton {
            id: addConstraintButton
            wide: true
            fontIcon: "plus-circle"
            text: qsTr("Add constraint")
            enabled: constraintsGroup.expressionValid && dependentPar.currentIndex !== -1
            onClicked: {
                if (typeof Globals.BackendWrapper.sampleAddConstraint !== 'function') {
                    return
                }
                const result = Globals.BackendWrapper.sampleAddConstraint(
                                    dependentPar.currentIndex,
                                    constraintsGroup.currentRelationValue(),
                                    expressionEditor.text)
                if (!result || !result.success) {
                    constraintsGroup.expressionValid = false
                    constraintsGroup.validationDirty = true
                    constraintsGroup.validationMessage = result && result.message ? result.message : qsTr("Constraint could not be created.")
                } else {
                    constraintsGroup.resetForm()
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
                model: Globals.BackendWrapper.sampleConstraintsList.length

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
                            return constraint ? constraint.dependentName : ""
                        }
                        elide: Text.ElideRight
                    }

                    EaComponents.TableViewLabel {
                        id: expressionColumn
                        width: EaStyle.Sizes.fontPixelSize * 15
                        horizontalAlignment: Text.AlignLeft
                        text: {
                            const constraint = Globals.BackendWrapper.sampleConstraintsList[index]
                            if (!constraint) {
                                return ""
                            }
                            const prefix = constraint.relation ? constraint.relation + ' ' : ''
                            return prefix + constraint.expression
                        }
                        elide: Text.ElideRight
                        ToolTip.visible: hovered && Globals.BackendWrapper.sampleConstraintsList[index] && Globals.BackendWrapper.sampleConstraintsList[index].rawExpression
                        ToolTip.text: Globals.BackendWrapper.sampleConstraintsList[index] ? Globals.BackendWrapper.sampleConstraintsList[index].rawExpression : ""
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
    
