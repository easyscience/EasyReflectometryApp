import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


EaElements.GroupBox {
    id: root

    title: qsTr("Polarization channels")
    visible: Globals.BackendWrapper.polarizationAvailable
    collapsed: false

    property var channelsModel: Globals.BackendWrapper.polarizationChannels
    property var selectedKeys: Globals.BackendWrapper.polarizationVisibleChannelKeys
    property bool staggerEnabled: Globals.BackendWrapper.polarizationStaggerEnabled

    Column {
        spacing: EaStyle.Sizes.fontPixelSize * 0.5

        Repeater {
            model: root.channelsModel

            delegate: Row {
                property var channelData: modelData
                property bool channelEnabled: channelData.enabled !== false

                spacing: EaStyle.Sizes.fontPixelSize * 0.5
                opacity: channelEnabled ? 1.0 : 0.45

                EaElements.CheckBox {
                    checked: root.selectedKeys.indexOf(channelData.key) !== -1
                    enabled: channelEnabled
                    ToolTip.text: channelEnabled ? qsTr("Show channel") : qsTr("Channel is not available for the active experiment")
                    onClicked: Globals.BackendWrapper.polarizationSetChannelVisible(channelData.key, checked)
                }

                Rectangle {
                    width: EaStyle.Sizes.fontPixelSize
                    height: width
                    radius: 2
                    color: channelData.color || EaStyle.Colors.themeAccent
                    border.color: EaStyle.Colors.chartGridLine
                    anchors.verticalCenter: parent.verticalCenter
                }

                EaElements.Label {
                    text: `${channelData.label} (${channelData.description})`
                    color: channelEnabled ? EaStyle.Colors.themeForeground : EaStyle.Colors.themeForegroundMinor
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }

        EaElements.CheckBox {
            text: qsTr("Stagger channels")
            checked: root.staggerEnabled
            ToolTip.text: qsTr("Offset visible polarization channels on the log-scale chart")
            onClicked: Globals.BackendWrapper.polarizationSetStaggerEnabled(checked)
        }
    }
}
