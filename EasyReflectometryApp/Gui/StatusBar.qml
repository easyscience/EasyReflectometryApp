import QtQuick
import QtQuick.Controls

import EasyApp.Gui.Globals as EaGlobals
import EasyApp.Gui.Elements as EaElements
import EasyApp.Gui.Components as EaComponents

import Gui.Globals as Globals


EaElements.StatusBar {

    visible: EaGlobals.Vars.appBarCurrentIndex !== 0

    EaElements.StatusBarItem {
        keyIcon: 'archive'
        keyText: qsTr('Project')
        valueText: Globals.BackendWrapper.statusProject ?? ''
        ToolTip.text: qsTr('Current project')
    }

    EaElements.StatusBarItem {
        keyIcon: 'layer-group'
        keyText: qsTr('Models')
        valueText: Globals.BackendWrapper.statusPhaseCount ?? ''
        ToolTip.text: qsTr('Number of models added')
    }

    EaElements.StatusBarItem {
        keyIcon: 'microscope'
        keyText: qsTr('Experiments')
        valueText: Globals.BackendWrapper.statusExperimentsCount ?? ''
        ToolTip.text: qsTr('Number of experiments added')
    }

    EaElements.StatusBarItem {
        keyIcon: 'calculator'
        keyText: qsTr('Calculator')
        valueText: Globals.BackendWrapper.statusCalculator ?? ''
        ToolTip.text: qsTr('Current calculation engine')
    }

    EaElements.StatusBarItem {
        keyIcon: 'level-down-alt'
        keyText: qsTr('Minimizer')
        valueText: Globals.BackendWrapper.statusMinimizer ?? ''
        ToolTip.text: qsTr('Current minimization engine and method')
    }

    EaElements.StatusBarItem {
        keyIcon: 'th-list'
        keyText: qsTr('Parameters')
        valueText: Globals.BackendWrapper.statusVariables ?? ''
        ToolTip.text: qsTr('Number of parameters: total, free and fixed')
    }
    EaElements.StatusBarItem {
        visible: Globals.BackendWrapper.analysisFitChi2 > 0
        keyIcon: 'chart-line'
        keyText: qsTr('Red. \u03c7\u00b2')
        valueText: Globals.BackendWrapper.analysisFitChi2.toFixed(2)
        ToolTip.text: qsTr('Goodness of fit (reduced chi-squared)')
    }
}
