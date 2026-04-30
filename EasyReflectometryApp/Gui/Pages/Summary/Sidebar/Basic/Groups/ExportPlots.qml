// SPDX-FileCopyrightText: 2026 EasyApp contributors
// SPDX-License-Identifier: BSD-3-Clause
// © 2026 Contributors to the EasyApp project <https://github.com/easyscience/EasyApp>

import QtQuick
import QtQuick.Controls
import QtQuick.Dialogs

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Logic as EaLogic

import Gui.Globals as Globals


Column {
    spacing: EaStyle.Sizes.fontPixelSize
    property string _lastRequestedPlotPath: ''

    // Open in matplotlib button
    EaElements.SideBarButton {
        id: showPlotButton
        wide: true
        fontIcon: 'chart-line'
        text: qsTr('Open in matplotlib')
        onClicked: {
            if (typeof Globals.BackendWrapper.summaryShowPlot === 'function') {
                Globals.BackendWrapper.summaryShowPlot(
                    parseFloat(widthField.text),
                    parseFloat(heightField.text)
                )
            }
        }
    }

    // Name field + format selector
    Row {
        spacing: EaStyle.Sizes.fontPixelSize

        // Name field
        EaElements.TextField {
            id: plotNameField
            width: savePlotButton.width - plotFormatField.width - parent.spacing
            topInset: plotNameLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            placeholderText: qsTr('Enter figure file name here')
            Component.onCompleted: text = Globals.BackendWrapper.summaryPlotFileName
            onEditingFinished: Globals.BackendWrapper.summarySetPlotFileName(text)
            EaElements.Label {
                id: plotNameLabel
                text: qsTr('Name')
            }
        }

        EaElements.ComboBox {
            id: plotFormatField
            topInset: plotFormatLabel.height
            topPadding: topInset + padding
            width: EaStyle.Sizes.fontPixelSize * 10
            model: Globals.BackendWrapper.summaryPlotExportFormats
            EaElements.Label {
                id: plotFormatLabel
                text: qsTr('Format')
            }
        }
    }

    // Location field (shows the full output path)
    EaElements.TextField {
        id: plotLocationField
        width: savePlotButton.width
        topInset: plotLocationLabel.height
        topPadding: topInset + padding
        rightPadding: plotChooseButton.width
        horizontalAlignment: TextInput.AlignLeft
        Component.onCompleted: text = Globals.BackendWrapper.summaryPlotFilePath +
            '.' + plotFormatField.currentValue.toLowerCase()
        EaElements.Label {
            id: plotLocationLabel
            text: qsTr('Location')
        }

        EaElements.ToolButton {
            id: plotChooseButton
            anchors.right: parent.right
            topPadding: parent.topPadding
            showBackground: false
            fontIcon: 'folder-open'
            ToolTip.text: qsTr('Choose figure parent directory')
            onClicked: plotParentDirDialog.open()
        }
    }

    // Width + Height fields
    Row {
        spacing: EaStyle.Sizes.fontPixelSize

        EaElements.TextField {
            id: widthField
            width: (savePlotButton.width - parent.spacing) / 2
            topInset: widthLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            text: '16'
            EaElements.Label {
                id: widthLabel
                text: qsTr('Width (cm)')
            }
        }

        EaElements.TextField {
            id: heightField
            width: (savePlotButton.width - parent.spacing) / 2
            topInset: heightLabel.height
            topPadding: topInset + padding
            horizontalAlignment: TextInput.AlignLeft
            text: '12'
            EaElements.Label {
                id: heightLabel
                text: qsTr('Height (cm)')
            }
        }
    }

    // Save plot button
    EaElements.SideBarButton {
        id: savePlotButton
        wide: true
        fontIcon: 'download'
        text: qsTr('Save plot')
        onClicked: {
            if (typeof Globals.BackendWrapper.summarySavePlot === 'function') {
                _lastRequestedPlotPath = plotLocationField.text
                Globals.BackendWrapper.summarySavePlot(
                    plotLocationField.text,
                    parseFloat(widthField.text),
                    parseFloat(heightField.text)
                )
            }
        }
    }

    Connections {
        target: Globals.BackendWrapper
        function onSummaryExportingFinished(success, filePath) {
            if (filePath !== _lastRequestedPlotPath) {
                return
            }
            plotSavedDialog.success = success
            plotSavedDialog.filePath = filePath
            plotSavedDialog.open()
        }
    }

    // Directory dialog
    FolderDialog {
        id: plotParentDirDialog
        title: qsTr("Choose figure parent directory")
        currentFolder: Globals.BackendWrapper.summaryPlotFileUrl
        onAccepted: plotLocationField.text = EaLogic.Utils.urlToLocalFile(
            selectedFolder + '/' +
            plotNameField.text + '.' +
            plotFormatField.currentValue.toLowerCase()
        )
    }

    SaveConfirmationDialog {
        id: plotSavedDialog
    }
}
