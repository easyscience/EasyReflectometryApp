import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / 'EasyReflectometryApp' / 'Gui'


def test_save_button_flashes_on_success_and_is_blocked_during_a_fit():
    application_window_qml = (GUI / 'ApplicationWindow.qml').read_text(encoding='utf-8')

    assert 'id: saveButton' in application_window_qml
    assert '!Globals.BackendWrapper.analysisFittingRunning' in application_window_qml
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


def test_save_button_is_disabled_when_there_is_nothing_to_save():
    application_window_qml = (GUI / 'ApplicationWindow.qml').read_text(encoding='utf-8')

    assert 'Globals.BackendWrapper.projectHasUnsavedChanges' in application_window_qml
    assert 'enabled: Globals.BackendWrapper.projectCreated' in application_window_qml
    assert "qsTr(\"No changes to save\")" in application_window_qml


def test_closing_with_unsaved_changes_asks_first():
    application_window_qml = (GUI / 'ApplicationWindow.qml').read_text(encoding='utf-8')

    assert 'onClosing: function(close)' in application_window_qml
    # The migration's bare no-op handler must be gone (a mention in a comment does not count).
    assert re.search(r'^\s*onClosing:\s*Qt\.quit\(\)\s*$', application_window_qml, re.MULTILINE) is None
    assert 'id: closeDialog' in application_window_qml
    assert 'close.accepted = false' in application_window_qml
    # Qt5's dialog offered no way back; this one does.
    assert "text: qsTr('Cancel')" in application_window_qml
    assert "text: qsTr('Exit without saving')" in application_window_qml
    assert "text: qsTr('Save and exit')" in application_window_qml


def test_save_and_exit_only_exits_once_the_save_succeeded():
    application_window_qml = (GUI / 'ApplicationWindow.qml').read_text(encoding='utf-8')

    assert 'property bool quitAfterSave: false' in application_window_qml
    assert 'applicationWindow.quitAfterSave = true' in application_window_qml
    # A failed save must cancel the pending exit, not fall through to Qt.quit().
    save_error_handler = application_window_qml.split('function onProjectSaveError(message)')[1]
    assert 'applicationWindow.quitAfterSave = false' in save_error_handler.split('}')[0]


def test_reset_dialog_names_the_unsaved_work_at_risk():
    application_window_qml = (GUI / 'ApplicationWindow.qml').read_text(encoding='utf-8')

    assert 'The project has unsaved changes that will be lost.' in application_window_qml


def test_backend_wrapper_and_mock_expose_the_dirty_flag():
    wrapper_qml = (GUI / 'Globals' / 'BackendWrapper.qml').read_text(encoding='utf-8')
    mock_qml = (ROOT / 'EasyReflectometryApp' / 'Backends' / 'Mock' / 'Project.qml').read_text(encoding='utf-8')

    assert 'readonly property bool projectHasUnsavedChanges' in wrapper_qml
    assert 'property bool hasUnsavedChanges' in mock_qml
