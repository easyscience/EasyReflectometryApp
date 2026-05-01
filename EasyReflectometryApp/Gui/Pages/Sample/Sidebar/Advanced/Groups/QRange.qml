import QtQuick 2.13
import QtQuick.Controls 2.13

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Q range of interest")
    collapsed: false
    Row {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        EaComponents.TableViewLabel{
            text: qsTr("q-min:")
            horizontalAlignment: Text.AlignRight
            width: labelWidth()
        }
        EaElements.Parameter {
            width: textFieldWidth()
            units: "Å<sup>-1</sup>"
            text: Globals.BackendWrapper.sampleQMin.toFixed(3)
            onEditingFinished: Globals.BackendWrapper.sampleSetQMin(text)
        }

        EaComponents.TableViewLabel{
            text: qsTr("q-max:")
            horizontalAlignment: Text.AlignRight
            width: labelWidth()
        }
        EaElements.Parameter {
            width: textFieldWidth()
            units: "Å<sup>-1</sup>"
            text: Globals.BackendWrapper.sampleQMax.toFixed(3)
            onEditingFinished: Globals.BackendWrapper.sampleSetQMax(text)
        }

        EaComponents.TableViewLabel{
            text: qsTr("q-res:")
            horizontalAlignment: Text.AlignRight
            width: labelWidth()
        }
        EaElements.Parameter {
            width: textFieldWidth()
            text: Globals.BackendWrapper.sampleQResolution
            onEditingFinished: Globals.BackendWrapper.sampleSetQElements(text)
        }
    }
    
    // Logic
    function labelWidth() {
        return (EaStyle.Sizes.sideBarContentWidth - spacing * 5 - textFieldWidth() * 3) / 3
    }
    function textFieldWidth() {
        return EaStyle.Sizes.fontPixelSize * 7.0
    }
}

