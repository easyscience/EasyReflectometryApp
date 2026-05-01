import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupColumn {
    
    EaComponents.TableView {
        id: surfactantView
        tallRows: false
        defaultInfoText: qsTr("No Layers Added")
        model: Globals.BackendWrapper.sampleLayers.length

        // Headers
        header: EaComponents.TableViewHeader {
            EaComponents.TableViewLabel {
                text: "Formula"
                width: EaStyle.Sizes.sideBarContentWidth - (thickLabel.width + roughLabel.width + solvLabel.width + apmLabel.width + solvMatLabel.width + 6 * EaStyle.Sizes.tableColumnSpacing)
                id: formulaLabel
            }

            EaComponents.TableViewLabel {
                text: qsTr('Thickness/Å')
                width: EaStyle.Sizes.fontPixelSize * 5.5
                id: thickLabel
            }

            EaComponents.TableViewLabel {
                text: qsTr('Roughness/Å')
                width: EaStyle.Sizes.fontPixelSize * 6.0
                id: roughLabel
            }

            EaComponents.TableViewLabel {
                text: "Solvation"
                width: EaStyle.Sizes.fontPixelSize * 4.5
                id: solvLabel
            }

            EaComponents.TableViewLabel {
                text: "APM/Å<sup>2</sup>"
                width: EaStyle.Sizes.fontPixelSize * 4.0
                id: apmLabel
            }

            EaComponents.TableViewLabel {
                text: "Solvent"
                width: EaStyle.Sizes.fontPixelSize * 6.5
                id: solvMatLabel
            }

        }
        // Rows
        delegate: EaComponents.TableViewDelegate {

            EaComponents.TableViewTextInput {
                horizontalAlignment: Text.AlignHCenter
                text: Globals.BackendWrapper.sampleLayers[index].formula
                onActiveFocusChanged: if (activeFocus && Globals.BackendWrapper.sampleCurrentLayerIndex !== index) Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                onEditingFinished: Globals.BackendWrapper.sampleSetLayerFormulaAtIndex(index, text)
            }

            EaComponents.TableViewTextInput {
                horizontalAlignment: Text.AlignHCenter
                enabled: Globals.BackendWrapper.sampleLayers[index].thickness_enabled === "True"
                text: (isNaN(Globals.BackendWrapper.sampleLayers[index].thickness)) ? '--' : Number(Globals.BackendWrapper.sampleLayers[index].thickness).toFixed(2)
                onActiveFocusChanged: if (activeFocus && Globals.BackendWrapper.sampleCurrentLayerIndex !== index) Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                onEditingFinished: Globals.BackendWrapper.sampleSetLayerThicknessAtIndex(index, text)
            }

            EaComponents.TableViewTextInput {
                horizontalAlignment: Text.AlignHCenter
                enabled: Globals.BackendWrapper.sampleLayers[index].roughness_enabled === "True"
                text: (isNaN(Globals.BackendWrapper.sampleLayers[index].roughness)) ? '--' : Number(Globals.BackendWrapper.sampleLayers[index].roughness).toFixed(2)
                onActiveFocusChanged: if (activeFocus && Globals.BackendWrapper.sampleCurrentLayerIndex !== index) Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                onEditingFinished: Globals.BackendWrapper.sampleSetLayerRoughnessAtIndex(index, text)
            }

            EaComponents.TableViewTextInput {
                horizontalAlignment: Text.AlignHCenter
                text: (isNaN(Globals.BackendWrapper.sampleLayers[index].solvation)) ? '--' : Number(Globals.BackendWrapper.sampleLayers[index].solvation).toFixed(2)
                onActiveFocusChanged: if (activeFocus && Globals.BackendWrapper.sampleCurrentLayerIndex !== index) Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                onEditingFinished: Globals.BackendWrapper.sampleSetLayerSolvationAtIndex(index, text)
            }

            EaComponents.TableViewTextInput {
                horizontalAlignment: Text.AlignHCenter
                enabled: Globals.BackendWrapper.sampleLayers[index].apm_enabled === "True"
                text: (isNaN(Globals.BackendWrapper.sampleLayers[index].apm)) ? '--' : Number(Globals.BackendWrapper.sampleLayers[index].apm).toFixed(2)
                onActiveFocusChanged: if (activeFocus && Globals.BackendWrapper.sampleCurrentLayerIndex !== index) Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                onEditingFinished: Globals.BackendWrapper.sampleSetLayerAPMAtIndex(index, text)
            }

            EaComponents.TableViewComboBox{
                readonly property int rowIndex: index
                property string currentAssemblyName: Globals.BackendWrapper.sampleCurrentAssemblyName
                horizontalAlignment: Text.AlignLeft
                model: Globals.BackendWrapper.sampleMaterialNames
                onActivated: function(comboIndex) {
                    Globals.BackendWrapper.sampleSetLayerSolventAtIndex(rowIndex, comboIndex)
                }
                onModelChanged: {
                    currentIndex = indexOfValue(Globals.BackendWrapper.sampleLayers[index].solvent)
                }
                onCurrentAssemblyNameChanged: {
                    currentIndex = indexOfValue(Globals.BackendWrapper.sampleLayers[index].solvent)
                }
                Component.onCompleted: {
                    currentIndex = indexOfValue(Globals.BackendWrapper.sampleLayers[index].solvent)
                }
            }
            mouseArea.onPressed: {
                if (Globals.BackendWrapper.sampleCurrentLayerIndex !== index) {
                    Globals.BackendWrapper.sampleSetCurrentLayerIndex(index)
                }
            }
        }
    }
    Row {
        EaElements.CheckBox {
            checked: false
            id: apm_check
            text: qsTr("Area-per-molecule")
            ToolTip.text: qsTr("Checking this box will ensure that the area-per-molecule of the head and tail layers is the same")
            onCheckedChanged: Globals.BackendWrapper.sampleSetCurrentAssemblyConstrainAPM(checked)
        }
        EaElements.CheckBox {
            checked: false
            id: conformal
            text: qsTr("Conformal roughness")
            ToolTip.text: qsTr("Checking this box will ensure that the interfacial roughness is the same for all interfaces of the surfactant")
            onCheckedChanged: Globals.BackendWrapper.sampleSetCurrentAssemblyConformalRoughness(checked)
        }
    }
    /* NOT FUNCTIONAL YET

    Row {
        EaElements.CheckBox {
            checked: false
            id: solvent_rough
            text: qsTr("Constrain roughness to item")
            enabled: conformal.checked
            ToolTip.text: qsTr("Checking this box allows another item to be selected and the conformal roughness will be constrained to this")
            onCheckedChanged: checked ? ExGlobals.Constants.proxy.model.currentSurfactantSolventRoughness(solvent_rough_item.currentText) : ExGlobals.Constants.proxy.model.currentSurfactantSolventRoughness(null)
        }
        EaElements.ComboBox {
            id: solvent_rough_item
            enabled: solvent_rough.checked
            onActivated: {
                ExGlobals.Constants.proxy.model.currentSurfactantSolventRoughness(null)
                ExGlobals.Constants.proxy.model.currentSurfactantSolventRoughness(currentText)
            }
            model: ExGlobals.Constants.proxy.model.itemsNamesConstrain
        }
    }*/
}
