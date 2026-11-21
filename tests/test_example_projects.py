"""The example projects on the Project page: the shipped files, loading one, and keeping it.

An example is loaded as the content of a project that is not created yet. These tests pin what
that guarantees: every shipped example loads with its models and data, nothing can be written
back into the installation, and "Create a new project" turns it into a project of the user's.
"""

import json
from pathlib import Path

import pytest
from easyreflectometry import Project as ProjectLib
from easyscience import global_object

from EasyReflectometryApp.Backends.Py import py_backend as backend_module
from EasyReflectometryApp.Backends.Py.logic.project import EXAMPLES_DIR
from EasyReflectometryApp.Backends.Py.logic.project import available_examples

ROOT = Path(__file__).resolve().parents[1]
GUI = ROOT / 'EasyReflectometryApp' / 'Gui'

#: index path -> (models, experiments, calculator) each example must load with.
EXPECTED = {
    'PolymerFilm/project.json': (1, 1, 'refnx'),
    'DspcMonolayer/project.json': (1, 1, 'refnx'),
    'NiTiMultilayer/project.json': (1, 1, 'refnx'),
    'FilmContrasts/project.json': (3, 3, 'refnx'),
    'DspcContrasts/project.json': (3, 3, 'refnx'),
    'LinkedFilmContrasts/project.json': (3, 3, 'refnx'),
    'TwoLayerFilmConstraints/project.json': (1, 1, 'refnx'),
    'FePolarized/project.json': (1, 1, 'refl1d'),
}


@pytest.fixture(autouse=True)
def clear_global_map():
    global_object.registry.clear()
    yield
    global_object.registry.clear()


def _index() -> list[dict]:
    return json.loads((EXAMPLES_DIR / 'index.json').read_text(encoding='utf-8'))


def test_every_shipped_example_is_listed_in_index_order():
    examples = available_examples()

    assert [entry['path'] for entry in _index()] == list(EXPECTED)
    assert [Path(example['path']) for example in examples] == [EXAMPLES_DIR / path for path in EXPECTED]
    assert all(example['name'] and example['description'] for example in examples)


def test_shipped_examples_are_in_the_current_file_format():
    """A format bump must come with regenerated examples (examples/make_example_projects.py)."""
    for path in EXPECTED:
        project_dict = json.loads((EXAMPLES_DIR / path).read_text(encoding='utf-8'))
        assert project_dict['file_format'] == ProjectLib.FILE_FORMAT, path


def test_a_broken_installation_lists_what_it_can(tmp_path):
    assert available_examples(tmp_path) == []

    (tmp_path / 'index.json').write_text('not json', encoding='utf-8')
    assert available_examples(tmp_path) == []

    (tmp_path / 'Present').mkdir()
    (tmp_path / 'Present' / 'project.json').write_text('{}', encoding='utf-8')
    index = [
        {'path': 'Missing/project.json', 'name': 'Missing', 'description': ''},
        {'name': 'No path'},
        {'path': 'Present/project.json', 'name': 'Present', 'description': 'here'},
    ]
    (tmp_path / 'index.json').write_text(json.dumps(index), encoding='utf-8')
    assert [example['name'] for example in available_examples(tmp_path)] == ['Present']


@pytest.mark.parametrize('relative_path', list(EXPECTED))
def test_each_example_loads_as_a_project_not_created_yet(qcore_application, relative_path):
    backend = backend_module.PyBackend()
    project = backend._project
    errors, saved = [], []
    project.projectLoadError.connect(errors.append)
    project.projectSaveError.connect(errors.append)
    project.projectSaved.connect(saved.append)
    path = EXAMPLES_DIR / relative_path
    shipped = path.read_bytes()

    project.loadExample(str(path))

    assert errors == []
    models, experiments, calculator = EXPECTED[relative_path]
    assert len(backend._project_lib.models) == models
    assert len(backend._project_lib.experiments) == experiments
    assert backend._project_lib.calculator == calculator
    assert project.isExample is True
    assert project.created is False
    assert project.hasUnsavedChanges is False
    assert project.name == next(entry['name'] for entry in _index() if entry['path'] == relative_path)
    # The content is the user's to keep: "Create a new project" asks whether to keep it.
    assert project.hasCustomContent() is True

    # Nothing is written back into the installation, by hand or automatically.
    project.markDirty()
    assert project.autosave('test') is False
    project.save()
    assert saved == []
    assert len(errors) == 1 and 'No project has been created yet' in errors[0]
    assert path.read_bytes() == shipped
    assert not (EXAMPLES_DIR / relative_path).with_name('project.json.bak').exists()


@pytest.mark.parametrize('relative_path', list(EXPECTED))
def test_every_page_can_show_each_example(qcore_application, relative_path):
    """Read every property the pages bind to. A getter that raises shows in QML only as
    "Error: <NULL>" and leaves the page broken (DSPC once put its solvated materials
    into the materials palette, whose rows need Parameter SLDs)."""
    backend = backend_module.PyBackend()
    backend._project.loadExample(str(EXAMPLES_DIR / relative_path))

    failures = []
    for part in ('_project', '_sample', '_experiment', '_analysis', '_summary', '_status'):
        page = getattr(backend, part)
        meta = page.metaObject()
        # From 1, after QObject's objectName: Sample and Analysis declare their
        # properties in mixins, which propertyOffset() does not count as their own.
        for i in range(1, meta.propertyCount()):
            name = meta.property(i).name()
            try:
                getattr(page, name)
            except Exception as error:  # noqa: BLE001 - every failure is reported
                failures.append(f'{part}.{name}: {error!r}')
    assert failures == []
    materials = backend._project_lib._materials
    assert all(hasattr(material.sld, 'value') for material in materials), [m.name for m in materials]


def test_the_linked_contrasts_example_lists_its_links_and_constraints(qcore_application):
    """The Constraints list shows what a user would have made with Link models and Add constraint."""
    backend = backend_module.PyBackend()
    backend._project.loadExample(str(EXAMPLES_DIR / 'LinkedFilmContrasts' / 'project.json'))

    rows = {(row['type'], row['dependentName'], row['expression']) for row in backend._sample.constraintsList}

    assert rows == {
        ('link', 'Film in H2O', 'linked to Film in D2O (5 tied parameter(s))'),
        ('link', 'Film in CMSi', 'linked to Film in D2O (5 tied parameter(s))'),
        ('dynamic', 'Film in H2O scale', 'Film in D2O scale'),
        ('dynamic', 'Film in CMSi scale', 'Film in D2O scale'),
        ('dynamic', 'CMSi sld', '0.38 * D2O sld + 0.62 * H2O sld'),
    }
    d2o, h2o, cmsi = (backend._project_lib._materials[i].sld for i in (3, 4, 5))
    d2o.value = 6.2
    assert cmsi.value == pytest.approx(0.38 * 6.2 + 0.62 * h2o.value)


def test_creating_a_project_from_an_example_keeps_its_content(qcore_application, tmp_path):
    backend = backend_module.PyBackend()
    project = backend._project
    project.loadExample(str(EXAMPLES_DIR / 'FilmContrasts' / 'project.json'))

    # What the description dialog does on OK after "Keep sample and data".
    project.setName('My film')
    project.setLocation(str(tmp_path / 'My film'))
    project.create()

    assert project.created is True
    assert project.isExample is False
    saved = json.loads((tmp_path / 'My film' / 'project.json').read_text(encoding='utf-8'))
    assert saved['info']['name'] == 'My film'
    assert len(saved['experiments']) == 3
    assert len(saved['models']['data']) == 3


def test_loading_a_project_or_resetting_ends_the_example(qcore_application, tmp_path):
    backend = backend_module.PyBackend()
    project = backend._project
    example = str(EXAMPLES_DIR / 'PolymerFilm' / 'project.json')

    project.loadExample(example)
    project.reset()
    assert project.isExample is False

    project.loadExample(example)
    project.setLocation(str(tmp_path / 'Saved'))
    project.setName('Saved')
    project.create()
    project.loadExample(example)
    project.load(str(tmp_path / 'Saved' / 'project.json'))
    assert project.isExample is False
    assert project.created is True


def test_qml_lists_the_examples_and_loads_them_as_examples():
    wrapper_qml = (GUI / 'Globals' / 'BackendWrapper.qml').read_text(encoding='utf-8')
    mock_qml = (ROOT / 'EasyReflectometryApp' / 'Backends' / 'Mock' / 'Project.qml').read_text(encoding='utf-8')
    sidebar_qml = (GUI / 'Pages' / 'Project' / 'Sidebar' / 'Basic' / 'Layout.qml').read_text(encoding='utf-8')
    examples_qml = (GUI / 'Pages' / 'Project' / 'Sidebar' / 'Basic' / 'Groups' / 'Examples.qml').read_text(encoding='utf-8')
    page_qml = (GUI / 'Pages' / 'Project' / 'Layout.qml').read_text(encoding='utf-8')

    assert 'readonly property var projectExamples: activeBackend.project.examples' in wrapper_qml
    assert 'readonly property bool projectIsExample: activeBackend.project.isExample' in wrapper_qml
    assert 'activeBackend.project.loadExample(path)' in wrapper_qml
    for member in ('readonly property var examples', 'property bool isExample', 'function loadExample(path)'):
        assert member in mock_qml
    assert "title: qsTr('Examples')" in sidebar_qml
    assert "Loader { source: 'Groups/Examples.qml' }" in sidebar_qml
    assert 'model: Globals.BackendWrapper.projectExamples' in examples_qml
    assert 'Globals.BackendWrapper.projectLoadExample(example.path)' in examples_qml
    # Unsaved work is not discarded without asking.
    assert 'replaceDialog.open()' in examples_qml
    # A loaded example shows its description instead of "No project defined".
    assert 'projectIsExample' in page_qml
