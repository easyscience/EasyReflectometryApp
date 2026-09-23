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


class _GraphicsApiSpy:
    """Records QQuickWindow.setGraphicsApi calls instead of touching Qt."""

    def __init__(self, monkeypatch):
        self.calls = []
        monkeypatch.setattr(helpers_module.QQuickWindow, 'setGraphicsApi', staticmethod(self.calls.append))
        self.use_renderer(monkeypatch, 'NVIDIA GeForce RTX 3060/PCIe/SSE2')

    def use_renderer(self, monkeypatch, name):
        monkeypatch.setattr(helpers_module.Rendering, 'openGlRendererName', staticmethod(lambda: name))


def test_rendering_env_override_forces_software_scene_graph_on_any_platform(monkeypatch):
    rendering = helpers_module.Rendering
    spy = _GraphicsApiSpy(monkeypatch)
    environ = {rendering.ENV_VAR: '1'}

    assert rendering.configure(environ=environ, platform='win32') == rendering.SOFTWARE
    assert spy.calls == [helpers_module.QSGRendererInterface.GraphicsApi.Software]
    assert environ[rendering.CHROMIUM_FLAGS_ENV_VAR] == rendering.CHROMIUM_DISABLE_GPU


def test_rendering_command_line_flag_forces_software_scene_graph(monkeypatch):
    rendering = helpers_module.Rendering
    spy = _GraphicsApiSpy(monkeypatch)
    environ = {}

    assert rendering.configure(forceSoftware=True, environ=environ, platform='darwin') == rendering.SOFTWARE
    assert len(spy.calls) == 1
    assert rendering.CHROMIUM_DISABLE_GPU in environ[rendering.CHROMIUM_FLAGS_ENV_VAR]


def test_rendering_env_override_off_leaves_everything_alone(monkeypatch):
    rendering = helpers_module.Rendering
    spy = _GraphicsApiSpy(monkeypatch)
    environ = {rendering.ENV_VAR: '0', 'XRDP_SESSION': '1'}

    assert rendering.configure(environ=environ, platform='linux') == rendering.DEFAULT
    assert spy.calls == []
    assert rendering.CHROMIUM_FLAGS_ENV_VAR not in environ


def test_rendering_not_changed_outside_linux(monkeypatch):
    rendering = helpers_module.Rendering
    _GraphicsApiSpy(monkeypatch)
    environ = {'VNCDESKTOP': 'host:1'}

    assert rendering.configure(environ=environ, platform='darwin') == rendering.DEFAULT
    assert rendering.CHROMIUM_FLAGS_ENV_VAR not in environ


def test_rendering_remote_linux_session_only_disables_webengine_gpu(monkeypatch):
    rendering = helpers_module.Rendering
    spy = _GraphicsApiSpy(monkeypatch)

    for name in rendering.REMOTE_SESSION_ENV_VARS:
        environ = {name: '1'}
        assert rendering.configure(environ=environ, platform='linux') == rendering.WEBENGINE_SOFTWARE
        assert environ[rendering.CHROMIUM_FLAGS_ENV_VAR] == rendering.CHROMIUM_DISABLE_GPU
    assert spy.calls == []


def test_rendering_respects_user_selected_qt_backend(monkeypatch):
    rendering = helpers_module.Rendering
    _GraphicsApiSpy(monkeypatch)
    environ = {'QT_QUICK_BACKEND': 'rhi', 'XRDP_SESSION': '1'}

    assert rendering.configure(environ=environ, platform='linux') == rendering.DEFAULT
    assert rendering.CHROMIUM_FLAGS_ENV_VAR not in environ


def test_rendering_probes_renderer_when_environment_is_inconclusive(monkeypatch):
    rendering = helpers_module.Rendering
    spy = _GraphicsApiSpy(monkeypatch)

    spy.use_renderer(monkeypatch, 'llvmpipe (LLVM 15.0.7, 256 bits)')
    environ = {}
    assert rendering.configure(environ=environ, platform='linux') == rendering.WEBENGINE_SOFTWARE
    assert environ[rendering.CHROMIUM_FLAGS_ENV_VAR] == rendering.CHROMIUM_DISABLE_GPU

    spy.use_renderer(monkeypatch, 'NVIDIA GeForce RTX 3060/PCIe/SSE2')
    environ = {}
    assert rendering.configure(environ=environ, platform='linux') == rendering.DEFAULT
    assert rendering.CHROMIUM_FLAGS_ENV_VAR not in environ
    assert spy.calls == []


def test_rendering_is_software_gl_renderer():
    rendering = helpers_module.Rendering

    assert rendering.isSoftwareGlRenderer('llvmpipe (LLVM 15.0.7, 256 bits)') is True
    assert rendering.isSoftwareGlRenderer('Mesa Software Rasterizer') is True
    assert rendering.isSoftwareGlRenderer('NVIDIA GeForce RTX 3060/PCIe/SSE2') is False
    assert rendering.isSoftwareGlRenderer('') is False


def test_rendering_keeps_existing_chromium_flags_and_does_not_duplicate():
    rendering = helpers_module.Rendering

    environ = {rendering.CHROMIUM_FLAGS_ENV_VAR: '--no-sandbox'}
    rendering.disableWebEngineGpu(environ)
    assert environ[rendering.CHROMIUM_FLAGS_ENV_VAR] == '--no-sandbox --disable-gpu'

    rendering.disableWebEngineGpu(environ)
    assert environ[rendering.CHROMIUM_FLAGS_ENV_VAR] == '--no-sandbox --disable-gpu'
