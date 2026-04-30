from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_status_bar_shows_transient_fit_progress_and_hides_final_chi2_while_running():
    status_bar_qml = (
        ROOT / 'EasyReflectometryApp' / 'Gui' / 'StatusBar.qml'
    ).read_text(encoding='utf-8')

    assert "keyText: qsTr('Fit')" in status_bar_qml
    assert 'visible: Globals.BackendWrapper.analysisFittingRunning' in status_bar_qml
    assert 'Globals.BackendWrapper.analysisFitHasInterimUpdate' in status_bar_qml
    assert 'Globals.BackendWrapper.analysisFitInterimReducedChi2.toFixed(4)' in status_bar_qml
    assert '!Globals.BackendWrapper.analysisFittingRunning && Globals.BackendWrapper.analysisFitChi2 > 0' in status_bar_qml


def test_fit_status_dialog_stays_results_only():
    dialog_qml = (
        ROOT
        / 'EasyReflectometryApp'
        / 'Gui'
        / 'Pages'
        / 'Analysis'
        / 'Sidebar'
        / 'Basic'
        / 'Popups'
        / 'FitStatusDialog.qml'
    ).read_text(encoding='utf-8')

    assert 'visible: Globals.BackendWrapper.analysisShowFitResultsDialog' in dialog_qml
    assert 'standardButtons: Dialog.Ok' in dialog_qml
    assert 'Refinement Running' not in dialog_qml
    assert 'Globals.BackendWrapper.analysisStopFit()' not in dialog_qml
    assert 'Globals.BackendWrapper.analysisFitIteration' not in dialog_qml
    assert 'Globals.BackendWrapper.analysisFitInterimChi2.toFixed(4)' not in dialog_qml
    assert 'Globals.BackendWrapper.analysisFitInterimReducedChi2.toFixed(4)' not in dialog_qml


def test_fit_buttons_toggle_between_start_and_cancel_via_start_stop_action():
    layout_qml = (
        ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Analysis' / 'Layout.qml'
    ).read_text(encoding='utf-8')
    fitting_group_qml = (
        ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Analysis' / 'Sidebar' / 'Basic' / 'Groups' / 'Fitting.qml'
    ).read_text(encoding='utf-8')

    assert "Globals.BackendWrapper.analysisFittingRunning ? qsTr('Cancel fitting') : qsTr('Start fitting')" in layout_qml
    assert 'Globals.BackendWrapper.analysisFittingStartStop()' in layout_qml
    assert "Globals.BackendWrapper.analysisFittingRunning  ? qsTr('Cancel fitting') : qsTr('Start fitting')" in fitting_group_qml
    assert 'Globals.BackendWrapper.analysisFittingStartStop()' in fitting_group_qml


def test_fit_status_dialog_is_loaded_once_at_stable_page_scope():
    layout_qml = (
        ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Analysis' / 'Layout.qml'
    ).read_text(encoding='utf-8')
    fitting_group_qml = (
        ROOT / 'EasyReflectometryApp' / 'Gui' / 'Pages' / 'Analysis' / 'Sidebar' / 'Basic' / 'Groups' / 'Fitting.qml'
    ).read_text(encoding='utf-8')

    assert "source: 'Sidebar/Basic/Popups/FitStatusDialog.qml'" in layout_qml
    assert 'FitStatusDialog.qml' not in fitting_group_qml