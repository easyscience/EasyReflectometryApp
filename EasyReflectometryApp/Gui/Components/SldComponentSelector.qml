import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


EaElements.GroupBox {
    id: root

    title: qsTr("SLD components")
    visible: Globals.BackendWrapper.polarizationAvailable
    collapsed: false

    property var componentsModel: Globals.BackendWrapper.polarizationSldComponents
    property var selectedKeys: Globals.BackendWrapper.polarizationVisibleSldComponentKeys

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        Repeater {
            model: root.componentsModel

            delegate: Row {
                property var componentData: modelData
                property bool componentEnabled: componentData.enabled !== false && componentData.available !== false

                spacing: EaStyle.Sizes.fontPixelSize * 0.5
                opacity: componentEnabled ? 1.0 : 0.45

                EaElements.CheckBox {
                    checked: root.selectedKeys.indexOf(componentData.key) !== -1
                    enabled: componentEnabled
                    ToolTip.text: componentEnabled ? qsTr("Show SLD component") : qsTr("Component is not available for the active model")
                    onClicked: Globals.BackendWrapper.polarizationSetSldComponentVisible(componentData.key, checked)
                }

                Rectangle {
                    width: EaStyle.Sizes.fontPixelSize
                    height: width
                    radius: 2
                    color: componentData.color || EaStyle.Colors.themeAccent
                    border.color: EaStyle.Colors.chartGridLine
                    anchors.verticalCenter: parent.verticalCenter
                }

                EaElements.Label {
                    text: `${componentData.label} (${componentData.symbol})`
                    color: componentEnabled ? EaStyle.Colors.themeForeground : EaStyle.Colors.themeForegroundMinor
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}
