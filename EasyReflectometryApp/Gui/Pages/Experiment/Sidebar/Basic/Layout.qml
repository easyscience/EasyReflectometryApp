import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals
import "./Groups" as Groups


EaComponents.SideBarColumn {
    Groups.ExperimentalDataExplorer{
        enabled: Globals.BackendWrapper.analysisIsFitFinished
        //enabled: true
    }
    Groups.ExperimentalData{
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.InstrumentParameters{
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
}

