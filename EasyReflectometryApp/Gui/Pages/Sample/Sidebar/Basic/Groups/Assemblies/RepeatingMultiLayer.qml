import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals
import "../Assemblies" as Assemblies


EaElements.GroupColumn {
    Row {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        // This integer defines how many repetitions of the layer structure should be
        // used.
        EaElements.SpinBox {
            id: repsSpinBox
            editable: true
            from: 1
            to: 9999
            value: Globals.BackendWrapper.sampleCurrentAssemblyRepeatedLayerReptitions
            onValueChanged: {
                Globals.BackendWrapper.sampleSetCurrentAssemblyRepeatedLayerReptitions(value)
            }
        }

        EaComponents.TableViewLabel{
            horizontalAlignment: Text.AlignRight
            width: EaStyle.Sizes.fontPixelSize * 10
            ToolTip.text: qsTr("To create some repeating multilayer structure")
            text: qsTr("Number of repetitions")
        }

    }
    Assemblies.MultiLayer{}
}
