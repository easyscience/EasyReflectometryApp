"""What "Create a new project" asks about: whether the session holds work of the user's own.

A fresh backend is needed (the startup order is part of what is under test), so the object
registry is cleared around each test, as the other real-backend tests do.
"""

from pathlib import Path

import pytest
from easyscience import global_object

from EasyReflectometryApp.Backends.Py import py_backend as backend_module


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.registry.clear()
    yield
    global_object.registry.clear()


def test_only_own_samples_data_or_fit_settings_count_as_custom_content(qcore_application, tmp_path):
    """A fresh session creates a project straight away; anything the user added asks first."""
    url = (Path(__file__).parents[1] / 'examples' / 'datasets' / 'two_layer_film.ort').resolve().as_uri()
    backend = backend_module.PyBackend()
    project = backend._project
    assert project.hasCustomContent() is False

    # The name, description and location are what a new project replaces anyway.
    project.setName('Renamed')
    project.setDescription('Described')
    project.setLocation(str(tmp_path / 'anything'))
    project.create()
    assert project.hasCustomContent() is False

    backend._experiment.load([url])
    assert project.hasCustomContent() is True

    project.reset()
    assert project.hasCustomContent() is False

    project.sampleLoad(url, False)
    assert project.hasCustomContent() is True

    project.reset()
    backend._analysis.setMinimizerCurrentIndex(backend._analysis.minimizerCurrentIndex + 1)
    assert project.hasCustomContent() is True
