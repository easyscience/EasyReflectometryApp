import QtQuick
import QtQuick.Controls

import EasyApplication.Gui.Globals as EaGlobals
import EasyApplication.Gui.Elements as EaElements
import EasyApplication.Gui.Components as EaComponents

import Gui.Globals as Globals

import "Logic/FitProgressText.js" as FitProgressText


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
        valueText: Globals.BackendWrapper.statusModelsCount ?? ''
        ToolTip.text: qsTr('Number of models added')
    }

    EaElements.StatusBarItem {
        keyIcon: 'microscope'
        keyText: qsTr('Experiments')
        valueText: Globals.BackendWrapper.statusExperimentsCount ?? ''
        ToolTip.text: qsTr('Number of experiments added')
    }

    // Calculator and Minimizer make room for the Fit item while a run is active.
    EaElements.StatusBarItem {
        visible: !Globals.BackendWrapper.analysisFittingRunning
        keyIcon: 'calculator'
        keyText: qsTr('Calculator')
        valueText: Globals.BackendWrapper.statusCalculator ?? ''
        ToolTip.text: qsTr('Current calculation engine')
    }

    EaElements.StatusBarItem {
        visible: !Globals.BackendWrapper.analysisFittingRunning
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
        visible: Globals.BackendWrapper.projectLastSaved !== ''
        keyIcon: 'save'
        keyText: qsTr('Saved')
        // The backend reports an ISO-8601 stamp so that the time is rendered in the user's locale.
        // Minute resolution: some locales' short time format carries seconds, which is more
        // precision than a save stamp needs.
        valueText: {
            if (Globals.BackendWrapper.projectLastSaved === '') {
                return ''
            }
            const format = Qt.locale().timeFormat(Locale.ShortFormat).replace(/[:.]?s+/g, '')
            const time = Qt.formatTime(new Date(Globals.BackendWrapper.projectLastSaved), format)
            return Globals.BackendWrapper.projectLastSaveAutomatic ? qsTr('%1 (auto)').arg(time) : time
        }
        ToolTip.text: Globals.BackendWrapper.projectLastSaveAutomatic
                      ? qsTr('Time of the last successful save, made automatically.\nThe version it replaced is kept as %1')
                            .arg(Globals.BackendWrapper.projectBackupPath)
                      : qsTr('Time of the last successful save')
    }

    // Stays up for the whole failure streak; the error dialog itself is shown only once.
    EaElements.StatusBarItem {
        visible: Globals.BackendWrapper.projectAutosaveFailing
        keyIcon: 'exclamation-triangle'
        keyText: qsTr('Autosave')
        valueText: qsTr('failed')
        ToolTip.text: qsTr('The last automatic save failed. Your work is still in memory; use Save to retry.')
    }

    EaElements.StatusBarItem {
        visible: Globals.BackendWrapper.analysisFittingRunning
        keyIcon: 'play-circle'
        keyText: qsTr('Fit')
        // Short text only; the progress strip above the status bar shows the activity.
        valueText: FitProgressText.statusText(Globals.BackendWrapper.analysisFitProgress)
        ToolTip.text: qsTr('Current fitting progress')
    }

    EaElements.StatusBarItem {
        visible: !Globals.BackendWrapper.analysisFittingRunning && Globals.BackendWrapper.analysisFitChi2 > 0
        keyIcon: 'chart-line'
        keyText: qsTr('Reduced Chi²')
        valueText: Globals.BackendWrapper.analysisFitChi2.toFixed(2)
        ToolTip.text: qsTr('Goodness of fit (reduced chi-squared)')
    }
}
