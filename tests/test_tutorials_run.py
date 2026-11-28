"""Every shipped tutorial can still be completed in the real application window.

Runs tests/tutorial_run_harness.py in a subprocess (a QGuiApplication cannot coexist with the
QCoreApplication the other tests share): the whole window with the Python backend, offscreen,
each tutorial started as the Home page does and every step done through **Show me**. This proves
that the controls exist and are framed, the actions work and the fits converge. Failure paths are
covered by test_logic_tutorial.py and test_py_tutorial.py, not here.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HARNESS = Path(__file__).resolve().parent / 'tutorial_run_harness.py'


def test_every_tutorial_runs_to_the_end_in_the_window(tmp_path):
    pytest.importorskip('PySide6.QtQml')
    pytest.importorskip('EasyApplication')
    environment = dict(os.environ)
    environment.setdefault('QT_QPA_PLATFORM', 'offscreen')
    environment.setdefault('QT_QUICK_BACKEND', 'software')
    environment['QT_FORCE_STDERR_LOGGING'] = '1'
    settings = tmp_path / 'settings.ini'

    completed = subprocess.run(  # noqa: S603 - our own interpreter running our own script
        [sys.executable, str(HARNESS), str(settings)],
        capture_output=True,
        text=True,
        encoding='utf-8',
        timeout=300,
        env=environment,
    )
    output = completed.stdout + completed.stderr
    assert completed.returncode == 0, output
    result = json.loads(completed.stdout.split('RESULT ', 1)[1].splitlines()[0])

    # The panel is docked beside the pages: EasyApp's window layout is still what it expects.
    assert result['docked'] is True, output
    assert result['tutorials'], output
    # Every problem of every tutorial at once, each step in full (pytest shortens a long dict
    # before it gets to the one that matters), with what the panel itself warned about.
    problems = []
    for tutorial in result['tutorials']:
        if not tutorial['steps']:  # it really ran, rather than finding a finished one
            problems.append(f'{tutorial["id"]}: no steps ran')
        elif tutorial['state'] != 'finished':
            problems.append(f'{tutorial["id"]}: {tutorial["state"]} at {tutorial["steps"][-1]}')
        unframed = [step for step in tutorial['steps'] if step['target'] and not step['framed']]
        problems += [f'{tutorial["id"]}: never framed {step}' for step in unframed]
    warnings = [line.strip() for line in output.splitlines() if 'Tutorial' in line]
    assert not problems, '\n'.join(problems + ['Panel warnings:'] + warnings)
    # Completion went to the settings file the window was given, not to the installed one.
    [line] = [line for line in settings.read_text(encoding='utf-8').splitlines() if line.startswith('completed=')]
    assert sorted(line[len('completed=') :].strip('"').split(',')) == sorted(t['id'] for t in result['tutorials'])
