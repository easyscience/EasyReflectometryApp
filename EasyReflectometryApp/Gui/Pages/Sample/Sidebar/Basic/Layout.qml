import QtQuick 2.14
import QtQuick.Controls 2.14

import EasyApp.Gui.Components 1.0 as EaComponents

import Gui.Globals as Globals
import "./Groups" as Groups

EaComponents.SideBarColumn {
    Groups.LoadSample{
        forceAutoCollapse: true
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.MaterialEditor{
        forceAutoCollapse: true
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.ModelSelector{
        forceAutoCollapse: true
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.ModelEditor {
        id: modelEditor
        forceAutoCollapse: true
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
}
