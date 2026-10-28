import QtQuick 2.14
import QtQuick.Controls 2.14

import EasyApplication.Gui.Components 1.0 as EaComponents

import Gui.Globals as Globals
import "./Groups" as Groups

EaComponents.SideBarColumn {
    Groups.QRange{
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.PlotControl{
    }
    Groups.CalculationEngine {
        collapsed: true
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.PhysicsConstraints{
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.Constraints{
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
    Groups.ModelConstraints{
        enabled: Globals.BackendWrapper.analysisIsFitFinished
    }
}
