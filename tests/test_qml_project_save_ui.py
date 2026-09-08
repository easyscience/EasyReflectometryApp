from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / 'EasyReflectometryApp' / 'Gui'


def test_save_button_flashes_on_success_and_is_blocked_during_a_fit():
    application_window_qml = (GUI / 'ApplicationWindow.qml').read_text(encoding='utf-8')

    assert 'id: saveButton' in application_window_qml
    assert (
        'enabled: Globals.BackendWrapper.projectCreated && !Globals.BackendWrapper.analysisFittingRunning'
        in application_window_qml
    )
    assert 'fontIcon: saveFlashTimer.running ? "check-circle" : "save"' in application_window_qml
    assert 'id: saveFlashTimer' in application_window_qml
    assert 'saveFlashTimer.restart()' in application_window_qml
    assert 'sequences: [StandardKey.Save]' in application_window_qml


def test_save_failure_opens_a_modal_with_the_error_message():
    application_window_qml = (GUI / 'ApplicationWindow.qml').read_text(encoding='utf-8')

    assert 'id: projectSaveErrorDialog' in application_window_qml
    assert 'function onProjectSaveError(message)' in application_window_qml
    assert 'projectSaveErrorDialog.errorMessage = message' in application_window_qml
    assert 'projectSaveErrorDialog.open()' in application_window_qml
    # A successful save must not raise a modal.
    assert 'function onProjectSaved(path)' in application_window_qml


def test_status_bar_shows_the_last_save_time_in_the_user_locale():
    status_bar_qml = (GUI / 'StatusBar.qml').read_text(encoding='utf-8')

    assert "keyText: qsTr('Saved')" in status_bar_qml
    assert "visible: Globals.BackendWrapper.projectLastSaved !== ''" in status_bar_qml
    # Locale-aware, but at minute resolution: the locale's short format may carry seconds.
    assert 'Qt.locale().timeFormat(Locale.ShortFormat)' in status_bar_qml
    assert "replace(/[:.]?s+/g, '')" in status_bar_qml
    assert 'Qt.formatTime(new Date(Globals.BackendWrapper.projectLastSaved), format)' in status_bar_qml


def test_backend_wrapper_forwards_the_save_signals():
    wrapper_qml = (GUI / 'Globals' / 'BackendWrapper.qml').read_text(encoding='utf-8')

    assert 'signal projectSaved(string path)' in wrapper_qml
    assert 'signal projectSaveError(string message)' in wrapper_qml
    assert 'activeBackend.project.projectSaved.connect(projectSaved)' in wrapper_qml
    assert 'activeBackend.project.projectSaveError.connect(projectSaveError)' in wrapper_qml
    assert 'readonly property string projectLastSaved' in wrapper_qml


def test_mock_backend_matches_the_save_api():
    mock_qml = (ROOT / 'EasyReflectometryApp' / 'Backends' / 'Mock' / 'Project.qml').read_text(encoding='utf-8')

    assert 'signal projectSaved(string path)' in mock_qml
    assert 'signal projectSaveError(string message)' in mock_qml
    assert 'property string lastSaved' in mock_qml
