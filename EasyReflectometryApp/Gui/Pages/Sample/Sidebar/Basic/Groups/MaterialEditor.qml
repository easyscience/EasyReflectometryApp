import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Material editor")
    collapsible: true
    collapsed: true

    EaElements.GroupColumn {

        // Table
        EaComponents.TableView {
            id: materialsView
            tallRows: false
            defaultInfoText: qsTr("No Materials Added/Loaded")
            model: Globals.BackendWrapper.sampleMaterials.length

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
                    text: "SLD/10<sup>-6</sup> Å<sup>-2</sup>"
                }

                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.fontPixelSize * 9.5
                    horizontalAlignment: Text.AlignHCenter
                    text: "<i>i</i> SLD/10<sup>-6</sup> Å<sup>-2</sup>"
                }

                // Placeholder for row delete button
                EaComponents.TableViewLabel {
                    width: EaStyle.Sizes.tableRowHeight
                }
            }

            // Rows
            delegate: EaComponents.TableViewDelegate {

                EaComponents.TableViewLabel {
                    // Density materials carry a ρ badge: their SLD is derived from
                    // formula & density, and selecting the row opens the density
                    // detail panel below the table.
                    readonly property bool density: Globals.BackendWrapper.sampleMaterials[index].kind === 'density'
                    text: (index + 1) + (density ? ' ρ' : '')
                    color: EaStyle.Colors.themeForegroundMinor
                    ToolTip.text: density ?
                                      qsTr("Density material (%1) — select the row to edit formula, density and SLD coupling below")
                                          .arg(Globals.BackendWrapper.sampleMaterials[index].formula) :
                                      ''
                }

                EaComponents.TableViewTextInput {
                    text: Globals.BackendWrapper.sampleMaterials[index].label
                    onEditingFinished: Globals.BackendWrapper.sampleSetMaterialNameAtIndex(index, text)
                }

                EaComponents.TableViewTextInput {
                    // A coupled density material derives SLD from formula & density.
                    readonly property bool sldLocked: Globals.BackendWrapper.sampleMaterials[index].kind === 'density' &&
                                                      Globals.BackendWrapper.sampleMaterials[index].sld_coupled
                    enabled: !sldLocked
                    ToolTip.text: sldLocked ?
                                      qsTr("Derived from formula and density — uncheck 'SLD computed from formula and density' below to edit") :
                                      ''
                    text: Number(Globals.BackendWrapper.sampleMaterials[index].sld).toFixed(3)
                    onEditingFinished: Globals.BackendWrapper.sampleSetMaterialSldAtIndex(index, text)
                }

                EaComponents.TableViewTextInput {
                    readonly property bool sldLocked: Globals.BackendWrapper.sampleMaterials[index].kind === 'density' &&
                                                      Globals.BackendWrapper.sampleMaterials[index].sld_coupled
                    enabled: !sldLocked
                    ToolTip.text: sldLocked ?
                                      qsTr("Derived from formula and density — uncheck 'SLD computed from formula and density' below to edit") :
                                      ''
                    text: Number(Globals.BackendWrapper.sampleMaterials[index].isld).toFixed(3)
                    onEditingFinished: Globals.BackendWrapper.sampleSetMaterialISldAtIndex(index, text)
                }

                EaComponents.TableViewButton {
                    enabled: materialsView !== null && materialsView.model > 1
                    fontIcon: "minus-circle"
                    ToolTip.text: qsTr("Remove this material")
                    onClicked: Globals.BackendWrapper.sampleRemoveMaterial(index)
                }

                mouseArea.onPressed: {
                    if (Globals.BackendWrapper.sampleCurrentMaterialIndex !== index) {
                        Globals.BackendWrapper.sampleSetCurrentMaterialIndex(index)
                    }
                }
            }
        }

        // Control buttons below table
        Row {
            spacing: EaStyle.Sizes.fontPixelSize

            EaElements.SideBarButton {
                enabled: true
                width: (EaStyle.Sizes.sideBarContentWidth - (2 * (EaStyle.Sizes.tableRowHeight + EaStyle.Sizes.fontPixelSize)) - EaStyle.Sizes.fontPixelSize) / 2
                fontIcon: "plus-circle"
                text: qsTr("Add material")
                onClicked: Globals.BackendWrapper.sampleAddNewMaterial()
            }

            EaElements.SideBarButton {
                enabled: Globals.BackendWrapper.sampleMaterials.length// (Globals.BackendWrapper.sampleCurrentMaterialIndex > 0) ? true : false //When material is selected
                width: (EaStyle.Sizes.sideBarContentWidth - (2 * (EaStyle.Sizes.tableRowHeight + EaStyle.Sizes.fontPixelSize)) - EaStyle.Sizes.fontPixelSize) / 2
                fontIcon: "clone"
                text: qsTr("Duplicate material")
                onClicked: Globals.BackendWrapper.sampleDuplicateSelectedMaterial()
            }

            EaElements.SideBarButton {
                enabled: (Globals.BackendWrapper.sampleCurrentMaterialIndex !== 0 && Globals.BackendWrapper.sampleMaterials.length > 0) ? true : false//When item is selected
                width: EaStyle.Sizes.tableRowHeight
                fontIcon: "arrow-up"
                ToolTip.text: qsTr("Move material up")
                onClicked: Globals.BackendWrapper.sampleMoveSelectedMaterialUp()
            }

            EaElements.SideBarButton {
                enabled: (Globals.BackendWrapper.sampleCurrentMaterialIndex + 1 !== Globals.BackendWrapper.sampleMaterials.length && Globals.BackendWrapper.sampleMaterials.length > 0) ? true : false//When item is selected
                width: EaStyle.Sizes.tableRowHeight
                fontIcon: "arrow-down"
                ToolTip.text: qsTr("Move material down")
                onClicked: Globals.BackendWrapper.sampleMoveSelectedMaterialDown()
            }
        }

        // Density-material detail: formula and density are the physical inputs;
        // the checkbox decouples sld/isld for direct entry and fitting
        // (see SLD_CHECKBOX_PLAN.md). Visible only when the selected material
        // is a density material.
        Column {
            id: densityMaterialSection

            readonly property var densityMaterial:
                Globals.BackendWrapper.sampleMaterials[Globals.BackendWrapper.sampleCurrentMaterialIndex]
            readonly property bool isDensity:
                densityMaterial !== undefined && densityMaterial.kind === 'density'

            visible: isDensity
            spacing: EaStyle.Sizes.fontPixelSize * 0.5

            EaElements.Label {
                color: EaStyle.Colors.themeForegroundMinor
                text: densityMaterialSection.isDensity ?
                          qsTr("Density material '%1'").arg(densityMaterialSection.densityMaterial.label) : ''
            }

            Row {
                spacing: EaStyle.Sizes.fontPixelSize

                EaElements.TextField {
                    id: formulaField
                    width: (EaStyle.Sizes.sideBarContentWidth - parent.spacing) / 2
                    topInset: formulaLabel.height
                    topPadding: topInset + padding
                    horizontalAlignment: TextInput.AlignLeft
                    text: densityMaterialSection.isDensity ? densityMaterialSection.densityMaterial.formula : ''
                    onEditingFinished: {
                        Globals.BackendWrapper.sampleSetMaterialFormulaAtIndex(
                                    Globals.BackendWrapper.sampleCurrentMaterialIndex, text)
                        // Typing broke the declarative binding; re-establish it so
                        // the field follows the backend (which may have rejected an
                        // invalid formula) and later selection changes.
                        text = Qt.binding(function () {
                            return densityMaterialSection.isDensity ?
                                        densityMaterialSection.densityMaterial.formula : ''
                        })
                    }
                    EaElements.Label {
                        id: formulaLabel
                        text: qsTr('Chemical formula')
                    }
                }

                EaElements.TextField {
                    id: densityField
                    width: formulaField.width
                    topInset: densityLabel.height
                    topPadding: topInset + padding
                    horizontalAlignment: TextInput.AlignLeft
                    text: densityMaterialSection.isDensity ? densityMaterialSection.densityMaterial.density : ''
                    onEditingFinished: {
                        Globals.BackendWrapper.sampleSetMaterialDensityAtIndex(
                                    Globals.BackendWrapper.sampleCurrentMaterialIndex, text)
                        text = Qt.binding(function () {
                            return densityMaterialSection.isDensity ?
                                        densityMaterialSection.densityMaterial.density : ''
                        })
                    }
                    EaElements.Label {
                        id: densityLabel
                        text: qsTr('Density (g/cm³)')
                    }
                }
            }

            EaElements.CheckBox {
                text: qsTr("SLD computed from formula and density")
                checked: densityMaterialSection.isDensity ?
                             densityMaterialSection.densityMaterial.sld_coupled : true
                ToolTip.text: qsTr("When re-enabled, SLD/iSLD are recalculated from the formula and density; manually entered or fitted SLD values are discarded.")
                // toggled() also fires on the programmatic `checked` rebind below
                // (materialsTableChanged from our own backend call, or a row
                // selection change) — this only stays a no-op loop because
                // set_sld_coupled_at_index() in the backend refuses to re-emit
                // when the state already matches. Don't drop that guard.
                onToggled: {
                    Globals.BackendWrapper.sampleSetMaterialSldCoupledAtIndex(
                                Globals.BackendWrapper.sampleCurrentMaterialIndex, checked)
                    // The click already moved the box and broke the binding;
                    // follow the backend's state instead of assuming.
                    checked = Qt.binding(function () {
                        return densityMaterialSection.isDensity ?
                                    densityMaterialSection.densityMaterial.sld_coupled : true
                    })
                }
            }
        }
    }
}
