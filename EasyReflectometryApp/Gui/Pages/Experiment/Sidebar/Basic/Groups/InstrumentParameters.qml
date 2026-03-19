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
    EaElements.GroupColumn {
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
        }

        Row {
            id: resolutionRow
            property real defaultFieldWidth: (EaStyle.Sizes.sideBarContentWidth - 5 * EaStyle.Sizes.fontPixelSize) / 6
            property real labelWidth: defaultFieldWidth
            property real percentLabelWidth: labelWidth / 2
            property real comboWidth: resolutionTypeMetrics.width + 2 * EaStyle.Sizes.fontPixelSize
            spacing: EaStyle.Sizes.fontPixelSize

            TextMetrics {
                id: resolutionTypeMetrics
                font: resolutionTypeCombo.font
                text: qsTr('PercentageFwhm')
            }

            EaComponents.TableViewLabel{
                text: qsTr("Resolution:")
                horizontalAlignment: Text.AlignRight
                width: resolutionRow.labelWidth
            }
            EaElements.ComboBox {
                id: resolutionTypeCombo
                width: resolutionRow.comboWidth
                model: Globals.BackendWrapper.experimentResolutionTypes
                currentIndex: Globals.BackendWrapper.experimentResolutionTypeCurrentIndex
                onCurrentIndexChanged: {
                    if (currentIndex !== Globals.BackendWrapper.experimentResolutionTypeCurrentIndex) {
                        Globals.BackendWrapper.experimentSetResolutionType(currentIndex)
                    }
                }
            }

            EaComponents.TableViewLabel{
                text: qsTr("%")
                horizontalAlignment: Text.AlignRight
                width: resolutionRow.percentLabelWidth
                visible: Globals.BackendWrapper.experimentResolutionTypeCurrentIndex === 0
            }
            EaElements.Parameter {
                width: resolutionRow.defaultFieldWidth
                units: "%"
                text: Globals.BackendWrapper.experimentResolution
                enabled: Globals.BackendWrapper.experimentExperimentalData
                visible: Globals.BackendWrapper.experimentResolutionTypeCurrentIndex === 0
                onEditingFinished: Globals.BackendWrapper.experimentSetResolution(text)
            }
        }
    }
}
