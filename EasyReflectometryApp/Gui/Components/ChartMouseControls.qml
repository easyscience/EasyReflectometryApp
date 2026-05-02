import QtQuick

import EasyApplication.Gui.Style as EaStyle


Item {
    id: root

    property var chartView: parent

    anchors.fill: parent

    enabled: chartView !== null

    Rectangle {
        id: recZoom

        property int xScaleZoom: 0
        property int yScaleZoom: 0

        visible: false
        transform: Scale {
            origin.x: 0
            origin.y: 0
            xScale: recZoom.xScaleZoom
            yScale: recZoom.yScaleZoom
        }
        border.color: EaStyle.Colors.appBorder
        border.width: 1
        opacity: 0.9
        color: 'transparent'

        Rectangle {
            anchors.fill: parent
            opacity: 0.5
            color: recZoom.border.color
        }
    }

    MouseArea {
        id: zoomMouseArea

        enabled: root.chartView ? root.chartView.allowZoom : false
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onPressed: {
            recZoom.x = mouseX
            recZoom.y = mouseY
            recZoom.visible = true
        }
        onMouseXChanged: {
            if (mouseX > recZoom.x) {
                recZoom.xScaleZoom = 1
                recZoom.width = Math.min(mouseX, root.chartView.width) - recZoom.x
            } else {
                recZoom.xScaleZoom = -1
                recZoom.width = recZoom.x - Math.max(mouseX, 0)
            }
        }
        onMouseYChanged: {
            if (mouseY > recZoom.y) {
                recZoom.yScaleZoom = 1
                recZoom.height = Math.min(mouseY, root.chartView.height) - recZoom.y
            } else {
                recZoom.yScaleZoom = -1
                recZoom.height = recZoom.y - Math.max(mouseY, 0)
            }
        }
        onReleased: {
            const x = Math.min(recZoom.x, mouseX) - root.chartView.anchors.leftMargin
            const y = Math.min(recZoom.y, mouseY) - root.chartView.anchors.topMargin
            const width = recZoom.width
            const height = recZoom.height
            root.chartView.zoomIn(Qt.rect(x, y, width, height))
            recZoom.visible = false
        }
    }

    MouseArea {
        property real pressedX
        property real pressedY
        property int threshold: 1

        enabled: !zoomMouseArea.enabled
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onPressed: {
            pressedX = mouseX
            pressedY = mouseY
        }
        onMouseXChanged: Qt.callLater(update)
        onMouseYChanged: Qt.callLater(update)

        function update() {
            const dx = mouseX - pressedX
            const dy = mouseY - pressedY
            pressedX = mouseX
            pressedY = mouseY

            if (dx > threshold)      root.chartView.scrollLeft(dx)
            else if (dx < -threshold) root.chartView.scrollRight(-dx)
            if (dy > threshold)      root.chartView.scrollUp(dy)
            else if (dy < -threshold) root.chartView.scrollDown(-dy)
        }
    }

    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.RightButton
        onClicked: root.chartView.resetAxes()
    }
}
