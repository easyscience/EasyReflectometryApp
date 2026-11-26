import QtQuick 2.14
import QtQuick.Controls 2.14

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents
import EasyApplication.Gui.Logic as EaLogic

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Instrumental parameters")
    visible: Globals.BackendWrapper.experimentExperimentalData
    collapsed: false

    // 4 significant digits, small values as an exponent: a background of 4e-7 is
    // "4e-7", not "0.00" (nor a "0.0000004" too wide for the field).
    function format(value) {
        const rounded = Number(EaLogic.Utils.toMaxPrecision(value, 4))
        return rounded !== 0 && Math.abs(rounded) < 1e-3 ? rounded.toExponential() : String(rounded)
    }

    // Called on Enter and on focus loss: only an edited value is sent, so clicking
    // into a field and out again cannot replace the value with its rounded display.
    // Text that is not a number is dropped, and the field shows the value again.
    function submit(field, setter, shown, asText) {
        const text = field.text.trim()
        if (text !== shown() && text !== '' && !isNaN(Number(text)))
            setter(asText ? text : Number(text))
        field.text = Qt.binding(shown)
    }

    Row {
        spacing: EaStyle.Sizes.fontPixelSize

        EaComponents.TableViewLabel{
            text: qsTr("Scaling:")
            horizontalAlignment: Text.AlignRight
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
        }
        EaElements.Parameter {
            id: scalingField
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
            text: format(Globals.BackendWrapper.experimentScaling)
            onEditingFinished: submit(scalingField, Globals.BackendWrapper.experimentSetScaling,
                                      () => format(Globals.BackendWrapper.experimentScaling))
            enabled: Globals.BackendWrapper.experimentExperimentalData
        }

        EaComponents.TableViewLabel{
            text: qsTr("Background:")
            horizontalAlignment: Text.AlignRight
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
        }
        EaElements.Parameter {
            id: backgroundField
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
            text: format(Globals.BackendWrapper.experimentBackground)
            onEditingFinished: submit(backgroundField, Globals.BackendWrapper.experimentSetBackground,
                                      () => format(Globals.BackendWrapper.experimentBackground))
            enabled: Globals.BackendWrapper.experimentExperimentalData
        }

        EaComponents.TableViewLabel{
            text: qsTr("Resolution:")
            horizontalAlignment: Text.AlignRight
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
        }
        EaElements.Parameter {
            id: resolutionField
            width: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
            units: Globals.BackendWrapper.experimentResolution !== "-" ? "%" : ""
            text: Globals.BackendWrapper.experimentResolution !== "-" ? Globals.BackendWrapper.experimentResolution : "Spline"
            enabled: Globals.BackendWrapper.experimentResolution !== "-" && Globals.BackendWrapper.experimentExperimentalData
            onEditingFinished: submit(resolutionField, Globals.BackendWrapper.experimentSetResolution,
                                      () => Globals.BackendWrapper.experimentResolution !== "-" ? Globals.BackendWrapper.experimentResolution : "Spline",
                                      true)
        }
    }
}
