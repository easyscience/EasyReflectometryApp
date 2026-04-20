import QtQuick 2.14
import QtQuick.Controls 2.14

import EasyApp.Gui.Components 1.0 as EaComponents

import Gui.Globals as Globals
import "./Groups" as Groups

EaComponents.SideBarColumn {
    Groups.LoadSample{
        collapsed: false
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.MaterialEditor{
        collapsed: true
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.ModelSelector{
        collapsed: true
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.ModelEditor {
        id: modelEditor
        collapsed: true
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
}
