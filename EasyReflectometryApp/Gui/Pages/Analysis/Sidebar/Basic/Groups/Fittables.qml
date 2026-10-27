// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import QtCharts

import EasyApplication.Gui.Logic as EaLogic
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    //title: qsTr("Parameters")
    collapsible: false
    last: true
    readonly property var backend: Globals.BackendWrapper
    // The row the slider and the Detach controls act on (undefined when there is none).
    readonly property var currentParameter: backend.analysisEnabledParameters[backend.analysisCurrentParameterIndex]

    Column {
        id: fittables
        property int selectedParamIndex: Globals.BackendWrapper.analysisCurrentParameterIndex
        property bool bulkUpdatingSelection: false
        property real fitColumnWidth: EaStyle.Sizes.fontPixelSize * 3.0
        property alias parameterSlider: slider
        onSelectedParamIndexChanged: {
            if (bulkUpdatingSelection) {
                return
            }
            updateSliderLimits()
            updateSliderValue()
        }

        property string selectedColor: EaStyle.Colors.themeForegroundHovered

        spacing: EaStyle.Sizes.fontPixelSize

        // Filter parameters widget
        Row {
            spacing: EaStyle.Sizes.fontPixelSize * 0.5

            // Filter criteria
            EaElements.TextField {
                id: filterCriteriaField

                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 3

                placeholderText: qsTr("Filter criteria")
                text: Globals.BackendWrapper.analysisNameFilterCriteria

                onTextChanged: {
                    Globals.BackendWrapper.analysisSetNameFilterCriteria(text)
                    const matchingIndex = nameFilterSelector.indexOfValue(text)
                    if (matchingIndex !== nameFilterSelector.currentIndex) {
                        nameFilterSelector.currentIndex = matchingIndex
                    }
                }
            }
            // Filter criteria

            // Filter by name
            EaElements.ComboBox {
                id: nameFilterSelector

                topInset: 0
                bottomInset: 0

                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 3

                valueRole: "value"
                textRole: "text"

                displayText: {
                    if (currentIndex === -1) {
                        return qsTr('Filter by name')
                    }
                    const entry = model && model[currentIndex]
                    if (!entry || !entry.text) {
                        return qsTr('Filter by name')
                    }
                    return entry.text.replace('&nbsp;◦ ', '')
                }

                model: [
                    { value: "", text: `All names (${Globals.BackendWrapper.analysisModelParametersCount + Globals.BackendWrapper.analysisExperimentParametersCount})` },
                    { value: "model", text: `<font color='${EaStyle.Colors.themeForegroundMinor}' face='${EaStyle.Fonts.iconsFamily}'>layer-group </font>Model (${Globals.BackendWrapper.analysisModelParametersCount})` },
                    { value: "experiment", text: `<font color='${EaStyle.Colors.themeForegroundMinor}' face='${EaStyle.Fonts.iconsFamily}'>microscope </font>Experiment (${Globals.BackendWrapper.analysisExperimentParametersCount})` },
                    { value: "background", text: `<font color='${EaStyle.Colors.themeForegroundMinor}' face='${EaStyle.Fonts.iconsFamily}'>wave-square </font>Background` }
                ]

                onActivated: filterCriteriaField.text = currentValue

                delegate: EaElements.MenuItem {
                    width: nameFilterSelector.width
                    height: EaStyle.Sizes.comboBoxHeight
                    textFormat: Text.RichText
                    elide: Text.ElideMiddle
                    text: {
                        const entry = nameFilterSelector.model && nameFilterSelector.model[index]
                        return entry && entry.text ? entry.text : ''
                    }
                    highlighted: nameFilterSelector.highlightedIndex === index
                    hoverEnabled: nameFilterSelector.hoverEnabled
                }

                Component.onCompleted: {
                    const selected = Globals.BackendWrapper.analysisNameFilterCriteria
                    const index = indexOfValue(selected)
                    currentIndex = index >= 0 ? index : 0
                }

                Connections {
                    target: Globals.BackendWrapper

                    function onAnalysisNameFilterCriteriaChanged() {
                        const selected = Globals.BackendWrapper.analysisNameFilterCriteria
                        const index = nameFilterSelector.indexOfValue(selected)
                        const targetIndex = index >= 0 ? index : -1
                        if (nameFilterSelector.currentIndex !== targetIndex) {
                            nameFilterSelector.currentIndex = targetIndex
                        }
                    }
                }
            }
            // Filter by name

            // Filter by variability
            EaElements.ComboBox {
                id: variabilityFilterSelector

                topInset: 0
                bottomInset: 0

                width: (EaStyle.Sizes.sideBarContentWidth - EaStyle.Sizes.fontPixelSize) / 3

                displayText: {
                    if (currentIndex === -1) {
                        return qsTr('Filter by variability')
                    }
                    const entry = model && model[currentIndex]
                    if (!entry || !entry.text) {
                        return qsTr('Filter by variability')
                    }
                    return entry.text
                }

                valueRole: "value"
                textRole: "text"

                model: [
                    { value: 'all', text: `All parameters (${Globals.BackendWrapper.analysisFreeParametersCount +
                                                        Globals.BackendWrapper.analysisFixedParametersCount})` },
                    { value: 'free', text: `Free parameters (${Globals.BackendWrapper.analysisFreeParametersCount})` },
                    { value: 'fixed', text: `Fixed parameters (${Globals.BackendWrapper.analysisFixedParametersCount})` }
                ]

                onActivated: {
                    Globals.BackendWrapper.analysisSetVariabilityFilterCriteria(currentValue)
                }

                delegate: EaElements.MenuItem {
                    width: variabilityFilterSelector.width
                    height: EaStyle.Sizes.comboBoxHeight
                    textFormat: Text.RichText
                    elide: Text.ElideMiddle
                    text: {
                        const entry = variabilityFilterSelector.model && variabilityFilterSelector.model[index]
                        return entry && entry.text ? entry.text : ''
                    }
                    highlighted: variabilityFilterSelector.highlightedIndex === index
                    hoverEnabled: variabilityFilterSelector.hoverEnabled
                }

                Component.onCompleted: {
                    const selected = Globals.BackendWrapper.analysisVariabilityFilterCriteria
                    const index = indexOfValue(selected)
                    currentIndex = index >= 0 ? index : 0
                }

                Connections {
                    target: Globals.BackendWrapper

                    function onAnalysisVariabilityFilterCriteriaChanged() {
                        const selected = Globals.BackendWrapper.analysisVariabilityFilterCriteria
                        const index = variabilityFilterSelector.indexOfValue(selected)
                        const targetIndex = index >= 0 ? index : 0
                        if (variabilityFilterSelector.currentIndex !== targetIndex) {
                            variabilityFilterSelector.currentIndex = targetIndex
                        }
                    }
                }
            }
            // Filter by variability

        }
        // Filter parameters widget

        // Table
        EaComponents.TableView {
            id: tableView
            defaultInfoText: qsTr("No parameters found")

            maxRowCountShow: 8 +
                            Math.trunc((applicationWindow.height - EaStyle.Sizes.appWindowMinimumHeight) /
                             EaStyle.Sizes.tableRowHeight)

            // Table model
            // We only use the length of the model object defined in backend logic and
            // directly access that model in every row using the TableView index property.
            model: Globals.BackendWrapper.analysisEnabledParameters.length
            // Table model

            Component.onCompleted: {
                Globals.BackendWrapper.analysisSetCurrentParameterIndex(0)// fittables.selectedParamIndex = 0
                updateSliderLimits()
                updateSliderValue()
            }

            // Header row
            header: EaComponents.TableViewHeader {
                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.fontPixelSize * 2.5
                    text: qsTr("No.")
                }

                EaComponents.TableViewLabel {
                    flexibleWidth: true
                    horizontalAlignment: Text.AlignLeft
                    color: EaStyle.Colors.themeForegroundMinor
                    text: qsTr("Name")
                }

                EaComponents.TableViewLabel {
                    id: valueLabel
                    width: EaStyle.Sizes.fontPixelSize * 4.5
                    horizontalAlignment: Text.AlignRight
                    color: EaStyle.Colors.themeForegroundMinor
                    text: qsTr("Value")
                }

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.fontPixelSize * 4.0
                    horizontalAlignment: Text.AlignLeft
                    //text: qsTr("units")
                }

                EaComponents.TableViewLabel {
                    width: valueLabel.width
                    horizontalAlignment: Text.AlignRight
                    color: EaStyle.Colors.themeForegroundMinor
                    text: qsTr("Error")
                }

                EaComponents.TableViewLabel {
                    width: valueLabel.width
                    horizontalAlignment: Text.AlignRight
                    color: EaStyle.Colors.themeForegroundMinor
                    text: qsTr("Min")
                }

                EaComponents.TableViewLabel {
                    width: valueLabel.width
                    horizontalAlignment: Text.AlignRight
                    color: EaStyle.Colors.themeForegroundMinor
                    text: qsTr("Max")
                }

                EaComponents.TableViewLabel {
                    width: fittables.fitColumnWidth
                    color: EaStyle.Colors.themeForegroundMinor
                    text: qsTr("Fit")
                }
            }
            // Header row

            // Table content row
            delegate: EaComponents.TableViewDelegate {
                id: parameterRow
                // Read through the id: TableViewParameter has its own `parameter`,
                // `value`, `fit`, ... properties that would shadow bare names.
                readonly property var param: Globals.BackendWrapper.analysisEnabledParameters[index]
                // Derived (computed, read-only) parameters carry an ƒ badge. Inactive
                // rows are a decoupled density material's unused knobs.
                readonly property bool derived: param.kind === 'derived'
                readonly property bool inactive: param.kind === 'inactive'
                readonly property bool editable: isEditable(param)

                enabled: !Globals.BackendWrapper.analysisFittingRunning

                mouseArea.onPressed: {
                    if (Globals.BackendWrapper.analysisCurrentParameterIndex !== index) {
                        Globals.BackendWrapper.analysisSetCurrentParameterIndex(index)
                        updateSliderLimits()
                        updateSliderValue()
                    }
                }

                EaComponents.TableViewLabel {
                    text: index + 1
                    color: EaStyle.Colors.themeForegroundMinor
                }

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.fontPixelSize * 5
                    // ⇄: one parameter of several models (contrasts sharing a layer or material)
                    readonly property var sharedBy: parameterRow.param.sharedBy ?? []
                    readonly property int followedBy: parameterRow.param.followedBy ?? 0
                    text: (parameterRow.derived ? 'ƒ ' : '') + (sharedBy.length > 1 ? '⇄ ' : '') + parameterRow.param.name
                    textFormat: Text.PlainText
                    color: parameterRow.editable ? EaStyle.Colors.themeForeground : EaStyle.Colors.themeForegroundDisabled
                    // The embedded TableViewLabel tooltip only appears while the
                    // text is elided, so a hover on a truncated name (e.g.
                    // 'Ni on Si L... roughness') reveals the full name. Derived and
                    // inactive rows also say what they are computed from.
                    ToolTip.text: parameterRow.derived
                                  ? qsTr("%1 — derived, read-only: %2")
                                        .arg(text)
                                        .arg(parameterRow.param.dependency || '')
                                  : parameterRow.inactive
                                  ? qsTr("%1 — %2")
                                        .arg(text)
                                        .arg(parameterRow.param.dependency || '')
                                  : text
                                    + (sharedBy.length > 1 ? qsTr("\nOne parameter of %1: changing it changes all of them.").arg(sharedBy.join(', ')) : '')
                                    + (followedBy > 0 ? qsTr("\nFollowed by %1 parameter(s) of other models.").arg(followedBy) : '')
                }

                EaComponents.TableViewParameter {
                    id: valueColumn
                    enabled: parameterRow.editable
                    selected: index === Globals.BackendWrapper.analysisCurrentParameterIndex
                    text: EaLogic.Utils.toMaxPrecision(parameterRow.param.value, 3)
                    onEditingFinished: {
                        focus = false
                        console.debug("*** Editing (manual) 'value' field of fittable on Analysis page ***")
                        Globals.BackendWrapper.analysisSetCurrentParameterValue(text)
                        updateSliderValue()
                        updateSliderLimits()
                    }
                }

                EaComponents.TableViewLabel {
                    text: {
                        const unit = parameterRow.param.units
                        if (unit !== undefined && unit !== 'dimensionless') {
                            if (unit.endsWith('Å^2')) {
                                '10⁻⁶Å⁻²'
                            } else {
                                unit
                            }
                        } else {
                            ""
                        }
                    }
                    color: EaStyle.Colors.themeForegroundMinor
                }

                EaComponents.TableViewLabel {
                    // A constrained (dependent) parameter derives its value from another
                    // parameter, so it has no error of its own to report; an inactive
                    // knob's error is stale (the parameter no longer enters the fit).
                    text: parameterRow.editable ? formatError(parameterRow.param.error) : ''
                    color: EaStyle.Colors.themeForegroundDisabled
                }

                // A derived row is computed from other parameters and never fitted:
                // the core recomputes its bounds by interval arithmetic over the
                // operands, so they are an envelope, not limits anyone set or that
                // anything enforces. Showing them next to editable bounds only
                // invites reading them as physical limits, so leave the cells empty.
                // Locked rows: derived (computed bounds) and inactive (a decoupled
                // density material's unused knobs — bounds are real but unused).
                EaComponents.TableViewParameter {
                    enabled: !parameterRow.derived && parameterRow.editable
                    text: parameterRow.derived ? '' :
                          EaLogic.Utils.toDefaultPrecision(parameterRow.param.min).replace('Infinity', 'inf')
                    // Missing bound of a free parameter while the minimizer needs finite ones
                    warned: Globals.BackendWrapper.analysisMinimizerRequiresFiniteBounds &&
                            parameterRow.param.fit &&
                            !isFinite(parameterRow.param.min)
                    onEditingFinished: {
                        focus = false
                        console.debug("*** Editing 'min' field of fittable on Analysis page ***")
                        const value = (text === '' ? '-inf' : text)
                        Globals.BackendWrapper.analysisSetCurrentParameterMin(value)
                        }
                }

                EaComponents.TableViewParameter {
                    enabled: !parameterRow.derived && parameterRow.editable
                    text: parameterRow.derived ? '' :
                          EaLogic.Utils.toDefaultPrecision(parameterRow.param.max).replace('Infinity', 'inf')
                    // Missing bound of a free parameter while the minimizer needs finite ones
                    warned: Globals.BackendWrapper.analysisMinimizerRequiresFiniteBounds &&
                            parameterRow.param.fit &&
                            !isFinite(parameterRow.param.max)
                    onEditingFinished: {
                        focus = false
                        console.debug("*** Editing 'max' field of fittable on Analysis page ***")
                        const value = (text === '' ? 'inf' : text)
                        Globals.BackendWrapper.analysisSetCurrentParameterMax(value)
                       }
                }

                EaComponents.TableViewCheckBox {
                    id: fitColumn
                    // The kind check matters here: an inactive density knob IS
                    // independent, but fitting it would silently do nothing (it no
                    // longer affects the reflectivity while SLD is fitted directly).
                    enabled: Globals.BackendWrapper.analysisExperimentsAvailable.length &&
                             parameterRow.editable
                    checked: parameterRow.param.fit
                    onToggled: {
                        console.debug("*** Editing 'fit' field of fittable on Analysis page ***")
                        // Ensure this row is selected before toggling the fit value
                        if (Globals.BackendWrapper.analysisCurrentParameterIndex !== index) {
                            Globals.BackendWrapper.analysisSetCurrentParameterIndex(index)
                        }
                        Globals.BackendWrapper.analysisSetCurrentParameterFit(checked)
                    }
                }
            }
            // Table content row
        }
        // Table

        Item {
            id: fitAllContainer
            visible: Globals.BackendWrapper.analysisEnabledParameters.length
            width: tableView.width
            height: EaStyle.Sizes.tableRowHeight

            EaComponents.TableViewLabel {
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.right: fitAllCheckBox.left
                anchors.rightMargin: EaStyle.Sizes.fontPixelSize * 0.5
                text: qsTr("Select All")
                horizontalAlignment: Text.AlignRight
                elide: Text.ElideNone
            }

            EaComponents.TableViewCheckBox {
                id: fitAllCheckBox
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: Math.max(tableView.width - fittables.fitColumnWidth, 0)
                enabled: Globals.BackendWrapper.analysisExperimentsAvailable.length &&
                         Globals.BackendWrapper.analysisEnabledParameters.length
                checked: allFittablesSelected()
                onToggled: {
                    setAllFittablesFit(checked)
                }
            }
        }

        // Parameter change slider
        Row {
            visible: Globals.BackendWrapper.analysisEnabledParameters.length

            spacing: EaStyle.Sizes.fontPixelSize

            EaElements.TextField {
                readOnly: true
                width: EaStyle.Sizes.fontPixelSize * 6
                text: EaLogic.Utils.toDefaultPrecision(slider.from)
            }

            EaElements.Slider {
                id: slider

                enabled: !Globals.BackendWrapper.analysisFittingRunning && isEditable(currentParameter)
                width: tableView.width - EaStyle.Sizes.fontPixelSize * 14

                stepSize: (to - from) / 20
                snapMode: Slider.SnapAlways

                toolTipText: {
                    return EaLogic.Utils.toDefaultPrecision(value)
                }
//                onMoved: {
//                        console.debug("*** Editing (slider) 'value' field of fittable on Analysis page ***")
//                        Globals.BackendWrapper.analysisSetCurrentParameterValue(value)
//                }
                onPressedChanged: {
                    if (!pressed) {
                        console.debug("*** Editing (slider) 'value' field of fittable on Analysis page ***")
                        Globals.BackendWrapper.analysisSetCurrentParameterValue(value)
                        updateSliderLimits()
                    }
                }
            }

            EaElements.TextField {
                readOnly: true
                width: EaStyle.Sizes.fontPixelSize * 6
                text: {
                    return EaLogic.Utils.toDefaultPrecision(slider.to)
                }
            }
        }

        // A parameter several models share (one object): give one of them its own copy.
        Row {
            id: detachRow
            readonly property var current: currentParameter
            readonly property var sharedBy: current?.sharedBy ?? []
            visible: current?.detachable ?? false
            spacing: EaStyle.Sizes.fontPixelSize * 0.5

            EaElements.Label {
                anchors.verticalCenter: parent.verticalCenter
                text: qsTr("Shared by %1. Detach in").arg(detachRow.sharedBy.join(', '))
            }
            EaElements.ComboBox {
                id: detachModel
                width: EaStyle.Sizes.fontPixelSize * 8
                model: detachRow.sharedBy
            }
            EaElements.Button {
                text: qsTr("Detach")
                ToolTip.text: qsTr("That model gets its own copy of the layers, still tied to the others except this parameter")
                onClicked: {
                    const result = Globals.BackendWrapper.sampleDetachParameter(
                        detachRow.current.unique_name, detachRow.current.sharedByIndices[detachModel.currentIndex])
                    detachMessage.text = result.success ? '' : result.message
                }
            }
        }

        EaElements.Label {
            id: detachMessage
            visible: text !== ''
            width: tableView.width
            wrapMode: Text.WordWrap
            color: EaStyle.Colors.red
        }
    }

    // Logic

    // Dependent (constrained) rows take their value from another parameter, and
    // inactive rows (a decoupled density material's unused knobs) are
    // independent but never enter the fit: neither can be edited or fitted.
    function isEditable(parameter) {
        return parameter !== undefined && parameter.kind !== 'inactive' && (parameter.independent ?? true)
    }

    function updateSliderValue() {
        if (currentParameter === undefined) {
            return
        }
        fittables.parameterSlider.value = EaLogic.Utils.toDefaultPrecision(currentParameter.value)
    }

    function updateSliderLimits() {
        const parameter = currentParameter
        if (parameter === undefined) {
            return
        }
        var from = parameter.value * 0.9
        var to = parameter.value * 1.1
        if (from === 0 && to === 0) {
            to = 0.1
        }
        if (parameter.max < to) {
            to = parameter.max
        }
        if (parameter.min > from) {
            from = parameter.min
        }
        fittables.parameterSlider.from = EaLogic.Utils.toDefaultPrecision(from)
        fittables.parameterSlider.to = EaLogic.Utils.toDefaultPrecision(to)
    }

    function formatError(value) {
        // A Python None (the minimizer completed but produced no error bars, e.g.
        // lmfit's gradient-free powell/cobyla) crosses the PySide6 QVariant
        // boundary as undefined, not null — check both.
        if (value === undefined || value === null) return 'n/a'
        if (value === 0 || isNaN(value)) return ''
        var s = Number(value.toPrecision(2)).toString()
        if (s.length <= 6) return s
        return value.toExponential(1)
    }

    function allFittablesSelected() {
        const params = backend.analysisEnabledParameters
        if (!params || !params.length) {
            return false
        }
        for (let i = 0; i < params.length; i++) {
            const parameter = params[i]
            if (!isEditable(parameter)) {
                continue
            }
            if (!parameter.fit) {
                return false
            }
        }
        return true
    }

    function setAllFittablesFit(enable) {
        const params = backend.analysisEnabledParameters
        if (!params || !params.length) {
            return
        }
        const originalIndex = backend.analysisCurrentParameterIndex
        var hasChanges = false
        const targetFit = !!enable
        fittables.bulkUpdatingSelection = true
        try {
            for (let i = 0; i < params.length; i++) {
                const parameter = params[i]
                if (!isEditable(parameter)) {
                    continue
                }
                if (!!parameter.fit === targetFit) {
                    continue
                }
                backend.analysisSetCurrentParameterIndex(i)
                backend.analysisSetCurrentParameterFit(targetFit)
                hasChanges = true
            }
        } finally {
            const paramsLength = params.length
            if (paramsLength) {
                const targetIndex = originalIndex >= 0 && originalIndex < paramsLength ? originalIndex : Math.min(Math.max(originalIndex, 0), paramsLength - 1)
                backend.analysisSetCurrentParameterIndex(targetIndex)
            }
            fittables.bulkUpdatingSelection = false
        }
        if (hasChanges) {
            updateSliderLimits()
            updateSliderValue()
        }
    }
}

