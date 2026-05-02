import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements


Row {
    id: root

    property var chartView: null
    property bool showLegend: false
    property bool controlsVisible: true

    signal interactionModeChanged(bool allowZoom)
    signal resetClicked()

    z: 1
    visible: controlsVisible
    x: chartView ? chartView.plotArea.x + chartView.plotArea.width - width : 0
    y: chartView ? chartView.plotArea.y - height - EaStyle.Sizes.fontPixelSize : 0

    spacing: 0.25 * EaStyle.Sizes.fontPixelSize

    EaElements.TabButton {
        checked: root.showLegend
        autoExclusive: false
        height: EaStyle.Sizes.toolButtonHeight
        width: EaStyle.Sizes.toolButtonHeight
        borderColor: EaStyle.Colors.chartAxis
        fontIcon: "align-left"
        ToolTip.text: root.showLegend ? qsTr("Hide legend") : qsTr("Show legend")
        onClicked: root.showLegend = checked
    }

    EaElements.TabButton {
        checked: root.chartView ? root.chartView.allowHover : false
        autoExclusive: false
        height: EaStyle.Sizes.toolButtonHeight
        width: EaStyle.Sizes.toolButtonHeight
        borderColor: EaStyle.Colors.chartAxis
        fontIcon: "comment-alt"
        ToolTip.text: qsTr("Show coordinates tooltip on hover")
        onClicked: {
            if (root.chartView) {
                root.chartView.allowHover = checked
            }
        }
    }

    Item { height: 1; width: 0.5 * EaStyle.Sizes.fontPixelSize }

    EaElements.TabButton {
        checked: root.chartView ? !root.chartView.allowZoom : false
        autoExclusive: false
        height: EaStyle.Sizes.toolButtonHeight
        width: EaStyle.Sizes.toolButtonHeight
        borderColor: EaStyle.Colors.chartAxis
        fontIcon: "arrows-alt"
        ToolTip.text: qsTr("Enable pan")
        onClicked: {
            if (root.chartView) {
                root.chartView.allowZoom = !checked
                root.interactionModeChanged(root.chartView.allowZoom)
            }
        }
    }

    EaElements.TabButton {
        checked: root.chartView ? root.chartView.allowZoom : false
        autoExclusive: false
        height: EaStyle.Sizes.toolButtonHeight
        width: EaStyle.Sizes.toolButtonHeight
        borderColor: EaStyle.Colors.chartAxis
        fontIcon: "expand"
        ToolTip.text: qsTr("Enable box zoom")
        onClicked: {
            if (root.chartView) {
                root.chartView.allowZoom = checked
                root.interactionModeChanged(root.chartView.allowZoom)
            }
        }
    }

    EaElements.TabButton {
        checkable: false
        height: EaStyle.Sizes.toolButtonHeight
        width: EaStyle.Sizes.toolButtonHeight
        borderColor: EaStyle.Colors.chartAxis
        fontIcon: "home"
        ToolTip.text: qsTr("Reset axes")
        onClicked: {
            if (root.chartView) {
                root.chartView.resetAxes()
            }
            root.resetClicked()
        }
    }
}
