import QtQuick 2.14
import QtQuick.Controls 2.14

import EasyApp.Gui.Style as EaStyle
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Instrumental parameters")
    visible: Globals.BackendWrapper.experimentExperimentalData
    collapsed: false
    Row {
        spacing: EaStyle.Sizes.fontPixelSize

        EaComponents.TableViewLabel{
            text: qsTr("Scaling:")
            horizontalAlignment: Text.AlignRight
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
        }
        EaElements.Parameter {
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
            text: Globals.BackendWrapper.experimentScaling.toFixed(3)
            onEditingFinished: Globals.BackendWrapper.experimentSetScaling(text)
            enabled: Globals.BackendWrapper.experimentExperimentalData
        }

        EaComponents.TableViewLabel{
            text: qsTr("Background:")
            horizontalAlignment: Text.AlignRight
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
        }
        EaElements.Parameter {
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
            text: Globals.BackendWrapper.experimentBackground.toFixed(2)
            onEditingFinished: Globals.BackendWrapper.experimentSetBackground(text)
            enabled: Globals.BackendWrapper.experimentExperimentalData
        }

        EaComponents.TableViewLabel{
            text: qsTr("Resolution:")
            horizontalAlignment: Text.AlignRight
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
        }
        EaElements.Parameter {
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
            units: Globals.BackendWrapper.experimentResolution !== "-" ? "%" : ""
            text: Globals.BackendWrapper.experimentResolution !== "-" ? Globals.BackendWrapper.experimentResolution : "Spline"
            enabled: Globals.BackendWrapper.experimentResolution !== "-" && Globals.BackendWrapper.experimentExperimentalData
            onEditingFinished: Globals.BackendWrapper.experimentSetResolution(text)
        }
    }
}
