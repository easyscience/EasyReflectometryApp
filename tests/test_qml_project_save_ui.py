"""Source-level contract checks on the project-save UI.

These pin the API between QML and the backends (property and signal names the wrapper and the
mock must expose) and the few decisions in ApplicationWindow.qml that are easy to lose in a
refactor and invisible to the Python tests: the close prompt's gating, the discard flag the
Qt 6 quit path depends on, and the dialogs being modal. They deliberately do not restate the
implementation line by line. The runtime behaviour of the close path is covered by
`test_qml_close_behaviour.py`.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / 'EasyReflectometryApp' / 'Gui'


def _application_window() -> str:
    return (GUI / 'ApplicationWindow.qml').read_text(encoding='utf-8')


def _block(text: str, start_marker: str, lines: int = 8) -> str:
    """The `lines` lines following the first occurrence of `start_marker`."""
    index = text.index(start_marker)
    return '\n'.join(text[index:].splitlines()[:lines])


def test_backend_wrapper_forwards_the_save_api():
    wrapper_qml = (GUI / 'Globals' / 'BackendWrapper.qml').read_text(encoding='utf-8')

    assert 'signal projectSaved(string path)' in wrapper_qml
    assert 'signal projectSaveError(string message)' in wrapper_qml
    assert 'activeBackend.project.projectSaved.connect(projectSaved)' in wrapper_qml
    assert 'activeBackend.project.projectSaveError.connect(projectSaveError)' in wrapper_qml
    assert 'readonly property string projectLastSaved' in wrapper_qml
    assert 'readonly property bool projectHasUnsavedChanges' in wrapper_qml
    assert 'readonly property bool projectCreated' in wrapper_qml


def test_mock_backend_matches_the_save_api():
    mock_qml = (ROOT / 'EasyReflectometryApp' / 'Backends' / 'Mock' / 'Project.qml').read_text(encoding='utf-8')

    assert 'signal projectSaved(string path)' in mock_qml
    assert 'signal projectSaveError(string message)' in mock_qml
    assert 'property string lastSaved' in mock_qml
    assert 'property bool hasUnsavedChanges' in mock_qml
    assert 'property bool created' in mock_qml


def test_status_bar_renders_the_save_stamp_in_the_user_locale():
    status_bar_qml = (GUI / 'StatusBar.qml').read_text(encoding='utf-8')

    assert "visible: Globals.BackendWrapper.projectLastSaved !== ''" in status_bar_qml
    assert 'Qt.locale()' in status_bar_qml
    assert 'Qt.formatTime(' in status_bar_qml


def test_save_is_gated_on_a_created_dirty_project_outside_a_fit():
    application_window_qml = _application_window()

    gate = _block(application_window_qml, 'readonly property bool canSaveProject', lines=3)
    assert 'Globals.BackendWrapper.projectCreated' in gate
    assert 'Globals.BackendWrapper.projectHasUnsavedChanges' in gate
    assert '!Globals.BackendWrapper.analysisFittingRunning' in gate
    # The button, the shortcut and "Save and exit" all defer to the same condition.
    assert application_window_qml.count('applicationWindow.canSaveProject') >= 4
    assert 'sequences: [StandardKey.Save]' in application_window_qml


def test_closing_with_unsaved_changes_asks_first_and_honours_the_discard_decision():
    application_window_qml = _application_window()

    # The migration's unconditional quit must be gone (a mention in a comment does not count).
    assert re.search(r'^\s*onClosing:\s*Qt\.quit\(\)\s*$', application_window_qml, re.MULTILINE) is None
    handler = _block(application_window_qml, 'onClosing: function(close)', lines=8)
    # Gated on a created project: before a create nothing on disk can be "unsaved", and saving
    # from the prompt would overwrite whatever project sits at the chosen path.
    assert 'Globals.BackendWrapper.projectCreated' in handler
    assert 'Globals.BackendWrapper.projectHasUnsavedChanges' in handler
    # Qt 6 runs onClosing again from Qt.quit(); without this flag "Exit without saving" loops.
    assert '!applicationWindow.discardChangesOnClose' in handler
    assert 'close.accepted = false' in handler
    assert 'property bool discardChangesOnClose: false' in application_window_qml

    exit_button = _block(application_window_qml, "text: qsTr('Exit without saving')", lines=7)
    assert 'applicationWindow.discardChangesOnClose = true' in exit_button
    assert 'Qt.quit()' not in exit_button

    assert "text: qsTr('Cancel')" in application_window_qml
    assert "text: qsTr('Save and exit')" in application_window_qml


def test_save_and_exit_only_exits_once_the_save_succeeded():
    application_window_qml = _application_window()

    assert 'property bool quitAfterSave: false' in application_window_qml
    assert 'function onProjectSaved(path)' in application_window_qml
    assert 'function onProjectSaveError(message)' in application_window_qml
    error_handler = _block(application_window_qml, 'function onProjectSaveError(message)', lines=6)
    assert 'applicationWindow.quitAfterSave = false' in error_handler


def test_test_mode_quit_cannot_be_swallowed_by_the_close_prompt():
    application_window_qml = _application_window()

    test_mode_end = _block(application_window_qml, "'*** TEST MODE 30 s DELAYED END ***'", lines=5)
    assert 'applicationWindow.discardChangesOnClose = true' in test_mode_end
    assert 'Qt.quit()' in test_mode_end


def test_the_prompt_and_error_dialogs_are_modal():
    """EaElements.Dialog is modeless by default; these must block the window behind them."""
    application_window_qml = _application_window()

    for dialog_id in ('closeDialog', 'projectSaveErrorDialog', 'resetStateDialog'):
        assert 'modal: true' in _block(application_window_qml, f'id: {dialog_id}', lines=8), dialog_id


def test_reset_dialog_names_the_unsaved_work_at_risk():
    assert 'The project has unsaved changes that will be lost.' in _application_window()
