import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

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
        visible: Globals.BackendWrapper.analysisFittingRunning
        keyIcon: 'play-circle'
        keyText: qsTr('Fit')
        valueText: {
            if (Globals.BackendWrapper.analysisFitHasInterimUpdate) {
                const iter = Globals.BackendWrapper.analysisFitIteration
                const rchi2 = Globals.BackendWrapper.analysisFitInterimReducedChi2.toFixed(4)
                return qsTr('iter %1 · χ² %2').arg(iter).arg(rchi2)
            }
            return qsTr('Fitting running') + '.'.repeat(dotCount % 5)
        }
        ToolTip.text: qsTr('Current fitting progress')

        property int dotCount: 0
        Timer {
            interval: 600
            repeat: true
            running: Globals.BackendWrapper.analysisFittingRunning
                     && !Globals.BackendWrapper.analysisFitHasInterimUpdate
            onTriggered: parent.dotCount++
        }
        onVisibleChanged: if (!visible) dotCount = 0
    }

    EaElements.StatusBarItem {
        visible: !Globals.BackendWrapper.analysisFittingRunning && Globals.BackendWrapper.analysisFitChi2 > 0
        keyIcon: 'chart-line'
        keyText: qsTr('Reduced Chi²')
        valueText: Globals.BackendWrapper.analysisFitChi2.toFixed(2)
        ToolTip.text: qsTr('Goodness of fit (reduced chi-squared)')
    }
}
