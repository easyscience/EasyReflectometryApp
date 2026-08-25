// SPDX-FileCopyrightText: 2026 EasyReflectometry contributors <support@easyreflectometry.org>
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyReflectometry project <https://github.com/easyscience/EasyReflectometry>

import QtQuick
import QtQuick.Controls
import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

// One-click physics constraints ("recipes") per assembly of the current model.
// The list is declarative and comes from the backend: which recipes apply to
// which assembly, whether they are available right now (and why not), whether
// they are active, and whether they can be toggled. Applying a recipe creates a
// named group of parameter ties that shows as a single row in the constraints
// table below.
EaElements.GroupBox {
    id: physicsGroup
    title: qsTr("Physics constraints")
    collapsible: true
    collapsed: false
    last: false

    property string lastMessage: ""

    readonly property var recipes: Globals.BackendWrapper.samplePhysicsConstraintRecipes || []

    // Assemblies that have at least one recipe row, in sample order.
    readonly property var assemblyNames: {
        const seen = []
        const names = []
        for (let i = 0; i < recipes.length; i++) {
            const idx = recipes[i].assemblyIndex
            if (seen.indexOf(idx) === -1) {
                seen.push(idx)
                names.push({ index: idx, name: recipes[i].assemblyName, type: recipes[i].assemblyType })
            }
        }
        return names
    }

    function recipesFor(assemblyIndex) {
        const rows = []
        for (let i = 0; i < recipes.length; i++) {
            if (recipes[i].assemblyIndex === assemblyIndex) {
                rows.push(recipes[i])
            }
        }
        return rows
    }

    function toggle(recipe, checked) {
        if (!recipe || !recipe.toggleable) {
            return
        }
        const result = checked
                     ? Globals.BackendWrapper.sampleApplyPhysicsConstraint(recipe.assemblyIndex, recipe.id)
                     : Globals.BackendWrapper.sampleRemovePhysicsConstraint(recipe.assemblyIndex, recipe.id)
        physicsGroup.lastMessage = (result && !result.success && result.message) ? result.message : ""
    }

    Column {
        width: parent ? parent.width : undefined
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        EaElements.Label {
            width: parent.width
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeForegroundMinor
            text: qsTr("Apply physically motivated constraints to an assembly with one click. Each active recipe appears as one row in the constraints table.")
        }

        EaElements.Label {
            width: parent.width
            visible: physicsGroup.recipes.length === 0
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeForegroundMinor
            text: qsTr("No assemblies in the current model.")
        }

        Repeater {
            model: physicsGroup.assemblyNames

            Column {
                id: assemblyBlock
                width: parent.width
                spacing: 0

                readonly property var assembly: modelData
                readonly property var assemblyRecipes: physicsGroup.recipesFor(modelData.index)

                EaElements.Label {
                    width: parent.width
                    text: assemblyBlock.assembly.name + "  ·  " + assemblyBlock.assembly.type
                    elide: Text.ElideRight
                    font.bold: true
                }

                Repeater {
                    model: assemblyBlock.assemblyRecipes

                    Row {
                        id: recipeRow
                        width: parent.width
                        spacing: EaStyle.Sizes.fontPixelSize * 0.25
                        readonly property var recipe: modelData

                        EaElements.CheckBox {
                            id: recipeBox
                            width: parent.width - infoLabel.width - recipeRow.spacing
                            text: recipeRow.recipe.title
                            enabled: recipeRow.recipe.toggleable
                            // Bind to the backend state; user clicks go through toggle() and the
                            // backend re-emits the recipe list, which re-evaluates this binding.
                            checked: recipeRow.recipe.active
                            onToggled: physicsGroup.toggle(recipeRow.recipe, checked)
                            // Only set the attached text: EaElements.CheckBox shows it via its
                            // embedded styled tooltip. Setting ToolTip.visible as well would pop
                            // up a second, unstyled tooltip on top of it.
                            ToolTip.text: recipeRow.recipe.description +
                                          (recipeRow.recipe.reason ? "\n" + recipeRow.recipe.reason : "")
                        }

                        EaElements.Label {
                            id: infoLabel
                            anchors.verticalCenter: parent.verticalCenter
                            width: implicitWidth
                            color: EaStyle.Colors.themeForegroundMinor
                            text: {
                                const r = recipeRow.recipe
                                if (!r.available) return qsTr("n/a")
                                if (!r.toggleable && r.active) return qsTr("always on")
                                return ""
                            }

                            // Plain labels have no embedded tooltip, so use the styled
                            // EaElements one explicitly to match the checkbox tooltip.
                            HoverHandler {
                                id: infoHover
                            }
                            EaElements.ToolTip {
                                text: recipeRow.recipe.reason ? recipeRow.recipe.reason : ""
                                visible: text !== "" &&
                                         infoLabel.text !== "" &&
                                         infoHover.hovered &&
                                         EaGlobals.Vars.showToolTips
                            }
                        }
                    }
                }
            }
        }

        EaElements.Label {
            width: parent.width
            visible: physicsGroup.lastMessage.length > 0
            wrapMode: Text.Wrap
            color: EaStyle.Colors.themeAccent
            text: physicsGroup.lastMessage
        }
    }
}
