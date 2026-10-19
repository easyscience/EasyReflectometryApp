import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Dialogs as Dialogs1

import EasyApplication.Gui.Style as EaStyle
import EasyApplication.Gui.Elements as EaElements

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Experimental data")
    collapsible: false
    enabled: Globals.Constants.proxy.fitter.isFitFinished

    Column {
        spacing: EaStyle.Sizes.fontPixelSize

        EaElements.SideBarButton {
            enabled: true
            wide: true
            fontIcon: "upload"
            text: qsTr("Load experiment(s) from file(s)")

            onClicked: {
                console.debug(`Clicking '${text}' button ::: ${this}`)
                Globals.References.pages.experiment.sidebar.basic.popups.loadExperimentFileDialog.open()
            }

            Loader {
                source: '../Popups/OpenExperimentFile.qml'
            }
        }

        EaElements.SideBarButton {
            // Another angle or wavelength band of the same contrast: merged into the
            // selected experiment, every point keeping its own resolution. Not for a
            // polarized experiment, whose channels are separate datasets.
            readonly property int currentIndex: Globals.BackendWrapper.analysisExperimentsCurrentIndex
            readonly property var polarizedFlags: Globals.BackendWrapper.analysisExperimentsPolarized

            enabled: currentIndex >= 0
                     && currentIndex < polarizedFlags.length
                     && !polarizedFlags[currentIndex]
            wide: true
            fontIcon: "plus-circle"
            text: qsTr("Add file(s) to the selected experiment")
            ToolTip.text: qsTr("Merge more measured curves of the same contrast (other angles or wavelength bands) into the selected experiment. Each point keeps the resolution it was measured with.")

            onClicked: {
                console.debug(`Clicking '${text}' button ::: ${this}`)
                Globals.References.pages.experiment.sidebar.basic.popups.appendExperimentFilesDialog.open()
            }

            Loader {
                source: '../Popups/AppendExperimentFiles.qml'
            }
        }

        EaElements.SideBarButton {
            enabled: true
            wide: true
            fontIcon: "magnet"
            text: qsTr("Load polarized experiment (file per channel)")

            onClicked: {
                console.debug(`Clicking '${text}' button ::: ${this}`)
                Globals.References.pages.experiment.sidebar.basic.popups.loadPolarizedExperimentFilesDialog.open()
            }

            Loader {
                source: '../Popups/OpenPolarizedExperimentFiles.qml'
            }
            Loader {
                source: '../Popups/PolarizedChannelAssignment.qml'
            }
        }
    }

    Component.onCompleted: Globals.Variables.experimentalDataGroup = this
}
