import QtQuick 2.14
import QtQuick.Controls 2.14

import EasyApp.Gui.Components 1.0 as EaComponents

import Gui.Globals as Globals
import "./Groups" as Groups

EaComponents.SideBarColumn {
    Groups.LoadSample{
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.MaterialEditor{
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.ModelSelector{
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.ModelEditor {
        id: modelEditor
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.AssemblyEditor{
        id: assemblyEditor
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
}
