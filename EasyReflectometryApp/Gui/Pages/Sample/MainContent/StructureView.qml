import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals


// Schematic of the current model's layer stack: one colored box per layer,
// heights proportional to thickness (clamped), semi-infinite caps fixed.
// Data contract: MD/VISUAL_LAYERS_PLAN.md §3.2
Rectangle {
    id: root

    readonly property var boxes: Globals.BackendWrapper.sampleStructure

    readonly property real capPx: 28
    readonly property real minBoxPx: 22
    readonly property real maxBoxPx: 120
    readonly property real stackWidth: Math.min(600, Math.max(Math.min(300, width - 4 * EaStyle.Sizes.fontPixelSize), 0.4 * width))
    // Sum of proportional (non-cap) thicknesses
    readonly property real totalT: boxes.reduce((sum, box) => sum + (isCap(box) ? 0 : box.thickness), 0)

    color: EaStyle.Colors.chartBackground

    function isCap(box) {
        return box.kind === 'superphase' || box.kind === 'subphase'
    }

    function pixelHeight(box) {
        if (isCap(box))
            return capPx
        if (totalT <= 0)
            return minBoxPx
        const available = flickable.height - 2 * capPx
        return Math.min(maxBoxPx, Math.max(minBoxPx, 0.8 * available * box.thickness / totalT))
    }

    function fillColor(c) {
        return Qt.alpha(Qt.color(String(c)), 0.35)
    }

    // Empty state
    EaElements.Label {
        anchors.centerIn: parent
        visible: root.boxes.length === 0
        text: qsTr('No layers defined')
        color: EaStyle.Colors.themeForegroundMinor
    }

    // Model name header (only useful when several models exist)
    EaElements.Label {
        id: header
        anchors.top: parent.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.topMargin: EaStyle.Sizes.fontPixelSize * 0.5
        visible: Globals.BackendWrapper.sampleModels.length > 1 && root.boxes.length > 0
        text: Globals.BackendWrapper.sampleModels[Globals.BackendWrapper.sampleCurrentModelIndex]?.label ?? ''
        color: EaStyle.Colors.themeForegroundMinor
    }

    Flickable {
        id: flickable
        anchors.top: parent.top
        anchors.bottom: footer.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: EaStyle.Sizes.fontPixelSize * 2
        contentHeight: stack.height
        clip: true
        ScrollIndicator.vertical: ScrollIndicator {}

        Column {
            id: stack
            width: root.stackWidth
            x: (flickable.width - width) / 2

            Repeater {
                model: root.boxes

                Rectangle {
                    readonly property bool selected: modelData.assembly_index === Globals.BackendWrapper.sampleCurrentAssemblyIndex
                                                     && modelData.layer_index === Globals.BackendWrapper.sampleCurrentLayerIndex

                    width: stack.width
                    height: root.pixelHeight(modelData)
                    color: root.fillColor(modelData.color)
                    border.color: modelData.color
                    border.width: selected ? 3 : 1
                    gradient: modelData.kind === 'gradient' ? boxGradient : null

                    Gradient {
                        id: boxGradient
                        GradientStop { position: 0.0; color: root.fillColor(modelData.color) }
                        GradientStop { position: 1.0; color: root.fillColor(modelData.color_end || modelData.color) }
                    }

                    EaElements.Label {
                        anchors.centerIn: parent
                        visible: parent.height >= root.minBoxPx
                        text: `${index}  ${modelData.label}`
                        elide: Text.ElideRight
                        width: Math.min(implicitWidth, parent.width - EaStyle.Sizes.fontPixelSize)
                    }

                    // Thickness annotation
                    EaElements.Label {
                        anchors.right: parent.right
                        anchors.rightMargin: EaStyle.Sizes.fontPixelSize * 0.5
                        anchors.verticalCenter: parent.verticalCenter
                        visible: !root.isCap(modelData) && parent.height >= root.minBoxPx && parent.width > 250
                        text: `${modelData.thickness.toFixed(1)} Å`
                        color: EaStyle.Colors.themeForegroundMinor
                    }

                    // Repetition badge for a collapsed repeat unit
                    EaElements.Label {
                        anchors.left: parent.right
                        anchors.leftMargin: EaStyle.Sizes.fontPixelSize * 0.5
                        anchors.verticalCenter: parent.verticalCenter
                        visible: modelData.repetitions > 1
                        text: `× ${modelData.repetitions}`
                    }

                    MouseArea {
                        id: boxMouse
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: {
                            Globals.BackendWrapper.sampleSetCurrentAssemblyIndex(modelData.assembly_index)
                            Globals.BackendWrapper.sampleSetCurrentLayerIndex(modelData.layer_index)
                        }
                    }

                    ToolTip.visible: boxMouse.containsMouse
                    ToolTip.text: {
                        let lines = [
                            `${modelData.label} (${modelData.material})`,
                            qsTr('SLD: %1 + %2i').arg(modelData.sld).arg(modelData.isld),
                            qsTr('Thickness: %1 Å').arg(modelData.thickness.toFixed(1)),
                            qsTr('Roughness: %1 Å').arg(modelData.roughness),
                            qsTr('Assembly: %1').arg(modelData.assembly)
                        ]
                        if (modelData.repetitions > 1)
                            lines.push(qsTr('Repeated × %1').arg(modelData.repetitions))
                        return lines.join('\n')
                    }
                }
            }
        }
    }

    // Legend + total thickness
    Column {
        id: footer
        anchors.bottom: parent.bottom
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottomMargin: EaStyle.Sizes.fontPixelSize
        spacing: EaStyle.Sizes.fontPixelSize * 0.25
        visible: root.boxes.length > 0

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            spacing: EaStyle.Sizes.fontPixelSize

            Repeater {
                model: Globals.BackendWrapper.sampleStructureLegend

                Row {
                    spacing: EaStyle.Sizes.fontPixelSize * 0.25

                    Rectangle {
                        anchors.verticalCenter: parent.verticalCenter
                        width: EaStyle.Sizes.fontPixelSize
                        height: EaStyle.Sizes.fontPixelSize
                        color: root.fillColor(modelData.color)
                        border.color: modelData.color
                    }
                    EaElements.Label {
                        text: modelData.label
                    }
                }
            }
        }

        EaElements.Label {
            anchors.horizontalCenter: parent.horizontalCenter
            text: qsTr('Total thickness: %1 Å').arg(Globals.BackendWrapper.sampleStructureTotalThickness.toFixed(1))
            color: EaStyle.Colors.themeForegroundMinor
        }
    }
}
