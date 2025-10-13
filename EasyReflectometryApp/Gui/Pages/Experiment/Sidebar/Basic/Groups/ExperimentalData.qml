import QtQuick 2.14
import QtQuick.Controls 2.14
import QtQuick.Dialogs as Dialogs1

import easyApp.Gui.Style as EaStyle
import easyApp.Gui.Elements as EaElements

import Gui.Globals as Globals

EaElements.GroupBox {
    title: qsTr("Experimental data")
    collapsible: false
    enabled: Globals.Constants.proxy.fitter.isFitFinished

    Row {
        spacing: EaStyle.Sizes.fontPixelSize

        EaElements.SideBarButton {
            enabled: true
            wide: true
            fontIcon: "upload"
            text: qsTr("Import experimental data")

            onClicked: {
                console.debug(`Clicking '${text}' button ::: ${this}`)
                Globals.References.pages.experiment.sidebar.basic.popups.loadExperimentFileDialog.open()
            }

            Loader {
                source: '../Popups/OpenExperimentFile.qml'
            }
        }
    }

    Component.onCompleted: Globals.Variables.experimentalDataGroup = this
}
