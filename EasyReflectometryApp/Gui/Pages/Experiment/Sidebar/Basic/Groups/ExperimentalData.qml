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
