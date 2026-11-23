"""The light startup package: Application, Rendering and the splash screen (MD/SPLASH-DESIGN.md)."""

import os
import re
import subprocess
import sys
import textwrap
from pathlib import Path

from EasyReflectometryApp.Startup import application as application_module

ROOT = Path(__file__).resolve().parents[1]
SPLASH_QML = ROOT / 'EasyReflectometryApp' / 'Startup' / 'Splash.qml'


def _run_python(code: str) -> subprocess.CompletedProcess:
    """Run `code` in a fresh interpreter from the repository root (a QGuiApplication cannot
    coexist with the QCoreApplication the other tests share, and sys.modules must be clean)."""
    environment = dict(os.environ)
    environment.setdefault('QT_QPA_PLATFORM', 'offscreen')
    environment.setdefault('QT_LOGGING_RULES', '*.debug=false')
    return subprocess.run(  # noqa: S603 - our own interpreter running our own code
        [sys.executable, '-c', textwrap.dedent(code)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=ROOT,
        env=environment,
    )


def test_startup_package_does_not_import_the_scientific_stack():
    completed = _run_python(
        """
        import sys
        import EasyReflectometryApp.Startup
        heavy = ['numpy', 'scipy', 'easyscience', 'easyreflectometry', 'EasyReflectometryApp.Backends']
        print('LOADED', [name for name in heavy if name in sys.modules])
        """
    )
    assert 'LOADED []' in completed.stdout, completed.stdout + completed.stderr


def test_splash_qml_moves_only_with_render_thread_animators():
    qml = SPLASH_QML.read_text(encoding='utf-8')
    code = '\n'.join(line for line in qml.splitlines() if not line.lstrip().startswith('//'))

    assert re.findall(r'^import .*$', code, flags=re.MULTILINE) == ['import QtQuick']
    for forbidden in ('NumberAnimation', 'Behavior', 'Timer', 'PauseAnimation', 'ShaderEffect', 'BusyIndicator'):
        assert forbidden not in code, forbidden
    assert 'ScaleAnimator' in code and 'XAnimator' in code


def test_main_registers_the_backend_singleton_before_the_splash_engine_exists():
    # PySide6 6.10: qmlRegisterSingletonType after any QQmlEngine exists breaks Material's
    # ElevationEffect, and with it the main window (it fails to load).
    main = (ROOT / 'EasyReflectometryApp' / 'main.py').read_text(encoding='utf-8')

    assert main.index('qmlRegisterSingletonType(') < main.index('splash = Splash(')


def test_qt_webengine_is_bundled_but_not_loaded_at_startup():
    # The WebEngine library takes seconds to load on the first launch after a boot, and the
    # Bayesian views that use it are created on demand. Application sets the context-sharing
    # attribute that QtWebEngineQuick.initialize() would otherwise set (see the smoke test).
    main = (ROOT / 'EasyReflectometryApp' / 'main.py').read_text(encoding='utf-8')
    freeze = (ROOT / 'tools' / 'Scripts' / 'FreezeApp.py').read_text(encoding='utf-8')

    assert 'QtWebEngine' not in main
    assert re.search(r"'--hidden-import',\s*'PySide6\.QtWebEngineQuick'", freeze)


def test_application_window_creates_pages_on_first_visit_and_keeps_them():
    window = (ROOT / 'EasyReflectometryApp' / 'Gui' / 'ApplicationWindow.qml').read_text(encoding='utf-8')
    content_area = window[window.index('contentArea: [') : window.index(']', window.index('contentArea: ['))]

    assert re.search(r'component Page: Loader \{\s*active: SwipeView\.isCurrentItem\s*onLoaded: active = true', window)
    assert content_area.count('Page { source:') == 6
    assert 'Loader' not in content_area


def test_application_and_splash_smoke():
    completed = _run_python(
        """
        import sys
        from PySide6.QtCore import QCoreApplication, Qt
        from PySide6.QtQuick import QQuickWindow
        from EasyReflectometryApp.Startup import Application, Splash

        app = Application(sys.argv)
        print('SHARED CONTEXTS', QCoreApplication.testAttribute(Qt.AA_ShareOpenGLContexts))
        assert Splash(enabled=False) and not app.topLevelWindows()

        splash = Splash()
        [view] = app.topLevelWindows()
        root = view.rootObject()

        def step():  # the QML `var` property is a QJSValue or an already-converted dict, depending on the PySide6 version
            value = root.property('step')
            if hasattr(value, 'toVariant'):
                value = value.toVariant()
            return float(value['from']), float(value['to']), value['ms'] > 0

        splash.status('Loading')
        print('STATUS', root.property('status'), 'VERSION', bool(root.property('version')))
        print('NO STEP', step())

        splash.status('Importing', until=0.5)
        print('STEP', step())
        splash.status('Going back', until=0.3)  # never moves back
        print('STEP', step())

        window = QQuickWindow()
        window.show()
        splash.handOver(window)
        print('STEP', step())
        splash.finish()
        splash.finish()
        print('VISIBLE', view.isVisible())
        """
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    assert 'SHARED CONTEXTS True' in output, output
    assert 'STATUS Loading VERSION True' in output, output
    assert 'NO STEP (0.0, 0.0, False)' in output, output  # a status without `until` leaves the bar alone
    assert 'STEP (0.0, 0.5, True)' in output, output
    assert 'STEP (0.5, 0.5, False)' in output, output
    assert 'STEP (0.5, 1.0, True)' in output, output
    assert 'VISIBLE False' in output, output


def test_main_startup_steps_fill_the_splash_bar_in_order():
    main = (ROOT / 'EasyReflectometryApp' / 'main.py').read_text(encoding='utf-8')
    fractions = [float(value) for value in re.findall(r'splash\.status\(.*until=([0-9.]+)\)', main)]

    assert len(fractions) == 5
    assert fractions == sorted(fractions) and 0 < fractions[0] and fractions[-1] < 1


class _GraphicsApiSpy:
    """Records QQuickWindow.setGraphicsApi calls instead of touching Qt."""

    def __init__(self, monkeypatch):
        self.calls = []
        monkeypatch.setattr(application_module.QQuickWindow, 'setGraphicsApi', staticmethod(self.calls.append))
        self.use_renderer(monkeypatch, 'NVIDIA GeForce RTX 3060/PCIe/SSE2')

    def use_renderer(self, monkeypatch, name):
        monkeypatch.setattr(application_module.Rendering, 'openGlRendererName', staticmethod(lambda: name))


def test_rendering_env_override_forces_software_scene_graph_on_any_platform(monkeypatch):
    rendering = application_module.Rendering
    spy = _GraphicsApiSpy(monkeypatch)
    environ = {rendering.ENV_VAR: '1'}

    assert rendering.configure(environ=environ, platform='win32') == rendering.SOFTWARE
    assert spy.calls == [application_module.QSGRendererInterface.GraphicsApi.Software]
    assert environ[rendering.CHROMIUM_FLAGS_ENV_VAR] == rendering.CHROMIUM_DISABLE_GPU


def test_rendering_command_line_flag_forces_software_scene_graph(monkeypatch):
    rendering = application_module.Rendering
    spy = _GraphicsApiSpy(monkeypatch)
    environ = {}

    assert rendering.configure(forceSoftware=True, environ=environ, platform='darwin') == rendering.SOFTWARE
    assert len(spy.calls) == 1
    assert rendering.CHROMIUM_DISABLE_GPU in environ[rendering.CHROMIUM_FLAGS_ENV_VAR]


def test_rendering_env_override_off_leaves_everything_alone(monkeypatch):
    rendering = application_module.Rendering
    spy = _GraphicsApiSpy(monkeypatch)
    environ = {rendering.ENV_VAR: '0', 'XRDP_SESSION': '1'}

    assert rendering.configure(environ=environ, platform='linux') == rendering.DEFAULT
    assert spy.calls == []
    assert rendering.CHROMIUM_FLAGS_ENV_VAR not in environ


def test_rendering_not_changed_outside_linux(monkeypatch):
    rendering = application_module.Rendering
    _GraphicsApiSpy(monkeypatch)
    environ = {'VNCDESKTOP': 'host:1'}

    assert rendering.configure(environ=environ, platform='darwin') == rendering.DEFAULT
    assert rendering.CHROMIUM_FLAGS_ENV_VAR not in environ


def test_rendering_remote_linux_session_only_disables_webengine_gpu(monkeypatch):
    rendering = application_module.Rendering
    spy = _GraphicsApiSpy(monkeypatch)

    for name in rendering.REMOTE_SESSION_ENV_VARS:
        environ = {name: '1'}
        assert rendering.configure(environ=environ, platform='linux') == rendering.WEBENGINE_SOFTWARE
        assert environ[rendering.CHROMIUM_FLAGS_ENV_VAR] == rendering.CHROMIUM_DISABLE_GPU
    assert spy.calls == []


def test_rendering_respects_user_selected_qt_backend(monkeypatch):
    rendering = application_module.Rendering
    _GraphicsApiSpy(monkeypatch)
    environ = {'QT_QUICK_BACKEND': 'rhi', 'XRDP_SESSION': '1'}

    assert rendering.configure(environ=environ, platform='linux') == rendering.DEFAULT
    assert rendering.CHROMIUM_FLAGS_ENV_VAR not in environ


def test_rendering_probes_renderer_when_environment_is_inconclusive(monkeypatch):
    rendering = application_module.Rendering
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
    rendering = application_module.Rendering

    assert rendering.isSoftwareGlRenderer('llvmpipe (LLVM 15.0.7, 256 bits)') is True
    assert rendering.isSoftwareGlRenderer('Mesa Software Rasterizer') is True
    assert rendering.isSoftwareGlRenderer('NVIDIA GeForce RTX 3060/PCIe/SSE2') is False
    assert rendering.isSoftwareGlRenderer('') is False


def test_rendering_keeps_existing_chromium_flags_and_does_not_duplicate():
    rendering = application_module.Rendering

    environ = {rendering.CHROMIUM_FLAGS_ENV_VAR: '--no-sandbox'}
    rendering.disableWebEngineGpu(environ)
    assert environ[rendering.CHROMIUM_FLAGS_ENV_VAR] == '--no-sandbox --disable-gpu'

    rendering.disableWebEngineGpu(environ)
    assert environ[rendering.CHROMIUM_FLAGS_ENV_VAR] == '--no-sandbox --disable-gpu'
