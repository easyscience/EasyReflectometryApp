import warnings

from EasyReflectometryApp.Backends.Py import helpers as helpers_module


def test_generalize_path_non_windows_returns_parsed_path(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'linux')

    result = helpers_module.IO.generalizePath('file:///tmp/demo/file.dat')

    assert result == '/tmp/demo/file.dat'


def test_generalize_path_windows_strips_leading_slash_and_normalizes(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'win32')

    result = helpers_module.IO.generalizePath('/C:/demo/folder/file.dat')

    assert result == 'C:\\demo\\folder\\file.dat'


def test_local_file_to_url_windows_branch(monkeypatch):
    monkeypatch.setattr(helpers_module.sys, 'platform', 'win32')

    result = helpers_module.IO.localFileToUrl('C:/demo/folder/file.dat')

    assert result.startswith('file:///')
    assert '/demo/folder/file.dat' in result


def test_to_std_dev_smallest_precision_for_large_std_dev():
    value_str, std_dev_str, combined = helpers_module.IO.toStdDevSmalestPrecision(12.7, 2.6)

    assert value_str == '13'
    assert std_dev_str == '3'
    assert combined == '13(3)'


def test_to_std_dev_smallest_precision_for_fractional_std_dev():
    value_str, std_dev_str, combined = helpers_module.IO.toStdDevSmalestPrecision(12.345, 0.034)

    assert value_str == '12.35'
    assert std_dev_str == '0.03'
    assert combined == '12.35(3)'


def test_old_precision_formatter_still_returns_three_parts():
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        value_str, std_dev_str, combined = helpers_module.IO.toStdDevSmalestPrecision_OLD(1.23, 0.04)

    assert value_str
    assert std_dev_str
    assert '(' in combined and ')' in combined


def test_rendering_env_override_wins_on_any_platform():
    rendering = helpers_module.Rendering

    assert rendering.softwareRequested({rendering.ENV_VAR: '1'}, 'win32') is True
    assert rendering.softwareRequested({rendering.ENV_VAR: '0', 'XRDP_SESSION': '1'}, 'linux') is False


def test_rendering_not_changed_outside_linux():
    assert helpers_module.Rendering.softwareRequested({'VNCDESKTOP': 'host:1'}, 'darwin') is False


def test_rendering_software_in_linux_remote_sessions():
    rendering = helpers_module.Rendering

    for name in rendering.REMOTE_SESSION_ENV_VARS:
        assert rendering.softwareRequested({name: '1'}, 'linux') is True


def test_rendering_respects_user_selected_qt_backend():
    environ = {'QT_QUICK_BACKEND': 'rhi', 'XRDP_SESSION': '1'}

    assert helpers_module.Rendering.softwareRequested(environ, 'linux') is False


def test_rendering_probes_renderer_when_environment_is_inconclusive():
    rendering = helpers_module.Rendering

    assert rendering.softwareRequested({}, 'linux') is None
    assert rendering.isSoftwareGlRenderer('llvmpipe (LLVM 15.0.7, 256 bits)') is True
    assert rendering.isSoftwareGlRenderer('NVIDIA GeForce RTX 3060/PCIe/SSE2') is False


def test_rendering_configure_selects_software_backend_for_software_gl(monkeypatch):
    rendering = helpers_module.Rendering
    selected = []
    monkeypatch.setattr(helpers_module.sys, 'platform', 'linux')
    monkeypatch.setattr(helpers_module.os, 'environ', {})
    monkeypatch.setattr(rendering, 'openGlRendererName', staticmethod(lambda: 'llvmpipe (LLVM 15.0.7, 256 bits)'))
    monkeypatch.setattr(helpers_module.QQuickWindow, 'setGraphicsApi', staticmethod(selected.append))

    assert rendering.configure() is True
    assert selected == [helpers_module.QSGRendererInterface.GraphicsApi.Software]
