from EasyReflectometryApp.Backends.Py import helpers as helpers_module


def test_generalize_path_non_windows_returns_parsed_path(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'linux')

    result = helpers_module.IO.generalizePath('file:///tmp/demo/file.dat')

    assert result == '/tmp/demo/file.dat'


def test_generalize_path_windows_strips_leading_slash_and_normalizes(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'win32')

    result = helpers_module.IO.generalizePath('/C:/demo/folder/file.dat')

    # generalizePath joins with os.path.sep, which follows the host OS, not sys.platform
    assert result == 'C:/demo/folder/file.dat'.replace('/', helpers_module.os.path.sep)


def test_generalize_path_keeps_the_drive_of_a_plain_windows_path(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'win32')

    assert helpers_module.IO.generalizePath('C:\\demo\\folder\\file.dat') == 'C:\\demo\\folder\\file.dat'
    assert helpers_module.IO.generalizePath('D:/demo/folder/file.dat') == 'D:/demo/folder/file.dat'


def test_generalize_path_windows_empty_path(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'win32')

    assert helpers_module.IO.generalizePath('file://') == ''


def test_format_msg_main_prefix_and_columns():
    message = helpers_module.IO.formatMsg('main', 'alpha', 'beta')

    assert message.startswith('* ')
    assert 'alpha' in message
    assert 'beta' in message
    assert ' ▌ ' in message


def test_format_msg_accepts_more_columns_than_widths():
    message = helpers_module.IO.formatMsg('sub', 'a', 'b', 'c', 'd', 'e')

    assert message.startswith('  - ')
    assert message.endswith(' ▌ e')


def test_local_file_to_url_windows_branch(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'win32')

    result = helpers_module.IO.localFileToUrl('C:/demo/folder/file.dat')

    assert result.startswith('file:///')
    assert '/demo/folder/file.dat' in result
