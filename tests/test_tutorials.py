"""The interactive tutorials as written in the documentation (MD/INTERACTIVE_TUTORIALS_DESIGN.md).

The grammar of the step blocks (tools/tutorial_steps.py), the generated files being in sync
with the Markdown (tools/make_tutorials.py), and everything a shipped tutorial refers to
existing in the app: controls, parameter aliases, backend slots and documentation anchors.
"""

import json
import re
import sys
from pathlib import Path

import pytest
from easyscience import global_object

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

import make_tutorials  # noqa: E402
from tutorial_steps import TutorialFormatError  # noqa: E402
from tutorial_steps import parse_actions  # noqa: E402
from tutorial_steps import parse_page  # noqa: E402

GUI = ROOT / 'EasyReflectometryApp' / 'Gui'
TUTORIALS = ROOT / 'EasyReflectometryApp' / 'Tutorials'
DOCS = ROOT / 'docs' / 'src'


@pytest.fixture
def clear_global_map():
    """A real backend registers its objects by name; another one in the same process collides."""
    global_object.registry.clear()
    yield
    global_object.registry.clear()


PAGE = """# A page

```{tutorial} Title
:id: demo
:example: Demo/project.json
:minutes: 3
:summary: A demo.
```

```{tutorial-step} Read
:id: read
:page: project
:more: other.md#a-section

Some **bold** text.
```

```{tutorial-step} Open Analysis
:id: open
:target: appbar.analysisTab
:done: ui.page == 'analysis'
:do: goto analysis
:advance: auto

Open it.
```
"""


def _shipped():
    return [
        json.loads((TUTORIALS / f'{tutorial_id}.json').read_text(encoding='utf-8'))
        for tutorial_id in json.loads((TUTORIALS / 'index.json').read_text(encoding='utf-8'))
    ]


def _steps():
    return [step for tutorial in _shipped() for step in tutorial['steps']]


# The grammar


def test_a_page_is_parsed_into_its_tutorial():
    tutorial = parse_page(PAGE, 'tutorials/demo')

    assert {key: tutorial[key] for key in ('id', 'title', 'example', 'minutes', 'summary')} == {
        'id': 'demo',
        'title': 'Title',
        'example': 'Demo/project.json',
        'minutes': 3,
        'summary': 'A demo.',
    }
    read, open_step = tutorial['steps']
    assert read['body'] == 'Some **bold** text.'
    assert read['more'] == 'tutorials/other.html#a-section'
    assert read['done'] == '' and read['actions'] == []
    assert open_step['page'] == '' and open_step['advance'] is True
    assert open_step['actions'] == [{'verb': 'goto', 'args': ['analysis']}]
    # Without `more`, Read more opens the page the step is written in.
    assert (
        parse_page(PAGE.replace(':more: other.md#a-section\n', ''), 'tutorials/demo')['steps'][0]['more']
        == 'tutorials/demo.html'
    )


def test_a_page_without_a_tutorial_has_none():
    assert parse_page('# Just prose\n', 'tutorials/prose') is None


@pytest.mark.parametrize(
    ('change', 'message'),
    [
        ((':page: project\n', ''), 'page'),
        ((':page: project\n', ':page: nowhere\n'), 'unknown page'),
        ((':do: goto analysis\n', ''), 'needs "do"'),
        ((":done: ui.page == 'analysis'\n", ':done: fit.reduced_chi2 < 5\n'), 'advance'),
        ((":done: ui.page == 'analysis'\n", ':done: len(ui) > 0\n'), 'unknown names'),
        ((":done: ui.page == 'analysis'\n", ':done: ui.page ==\n'), 'not a Python expression'),
        ((':do: goto analysis\n', ':do: fly analysis\n'), 'unknown action'),
        ((':do: goto analysis\n', ':do: goto\n'), 'number of arguments'),
        (('Some **bold** text.', 'An image ![x](y.png)'), 'image'),
        ((':more: other.md#a-section\n', ':more: #a-section\n'), 'MyST would read'),
        ((':more: other.md#a-section\n', ':more: a-section\n'), 'page.md'),
        ((':id: read\n', ':id: read\n:colour: blue\n'), 'unknown options'),
        ((':id: read\n', ':id: read\n:id: again\n'), 'given twice'),
        ((':id: open\n', ':id: read\n'), 'used twice'),
        (('Some **bold** text.\n```', 'Some text.\n```python\nx = 1\n```'), 'fenced block'),
        (('\nOpen it.\n```\n', '\nOpen it.\n'), 'not closed'),
    ],
)
def test_the_grammar_is_enforced(change, message):
    old, new = change
    assert old in PAGE
    with pytest.raises(TutorialFormatError, match=message):
        parse_page(PAGE.replace(old, new, 1), 'tutorials/demo')


def test_actions_are_split_and_call_arguments_are_json_where_they_parse():
    assert parse_actions('sidebar-tab advanced; set analysis.minimizer "LMFit leastsq"; call analysis.setX name 200 true') == [
        {'verb': 'sidebar-tab', 'args': ['advanced']},
        {'verb': 'set', 'args': ['analysis.minimizer', 'LMFit leastsq']},
        {'verb': 'call', 'args': ['analysis.setX', 'name', 200, True]},
    ]
    with pytest.raises(TutorialFormatError, match='<part>.<slot>'):
        parse_actions('call setX')


# The shipped tutorials


def test_the_generated_files_are_in_sync_with_the_documentation():
    expected = make_tutorials.build()
    committed = {path.name: path.read_text(encoding='utf-8') for path in TUTORIALS.glob('*.json')}

    assert committed == {name: make_tutorials.serialize(content) for name, content in expected.items()}, (
        'Run python tools/make_tutorials.py after editing a tutorial in docs/src'
    )


def test_every_tutorial_example_is_shipped():
    for tutorial in _shipped():
        assert (ROOT / 'EasyReflectometryApp' / 'Examples' / tutorial['example']).is_file(), tutorial['id']


def _object_names() -> list[str]:
    names = []
    for path in GUI.rglob('*.qml'):
        names += re.findall(r"objectName: '([^']+)'", path.read_text(encoding='utf-8'))
    return names


def test_every_control_a_tutorial_needs_is_named_exactly_once():
    needed = set()
    for step in _steps():
        needed |= {step['target']} if step['target'] else set()
        if step['page']:
            needed.add(f'appbar.{step["page"]}Tab')
        if step['sidebarTab']:
            needed.add(f'{step["page"]}.{step["sidebarTab"]}Tab')
        for action in step['actions']:
            if action['verb'] in ('click', 'set'):
                needed.add(action['args'][0])
            elif action['verb'] == 'goto':
                needed.add(f'appbar.{action["args"][0]}Tab')
            elif action['verb'] == 'sidebar-tab':
                needed.add(f'{step["page"]}.{action["args"][0]}Tab')
    names = _object_names()

    assert {name: names.count(name) for name in sorted(needed)} == dict.fromkeys(sorted(needed), 1)


def test_every_call_names_a_slot_of_a_backend_part():
    from EasyReflectometryApp.Backends.Py.analysis import Analysis
    from EasyReflectometryApp.Backends.Py.experiment import Experiment
    from EasyReflectometryApp.Backends.Py.plotting_1d import Plotting1d
    from EasyReflectometryApp.Backends.Py.project import Project
    from EasyReflectometryApp.Backends.Py.sample import Sample

    classes = {'analysis': Analysis, 'experiment': Experiment, 'project': Project, 'sample': Sample, 'plotting': Plotting1d}
    for step in _steps():
        for action in step['actions']:
            if action['verb'] != 'call':
                continue
            part, slot = action['args'][0].split('.')
            meta = classes[part].staticMetaObject
            methods = {bytes(meta.method(index).name()).decode() for index in range(meta.methodCount())}
            assert slot in methods, f'{step["id"]}: no slot {part}.{slot}'


def test_every_parameter_alias_exists_in_the_tutorial_example(qcore_application, clear_global_map):
    from EasyReflectometryApp.Backends.Py.py_backend import PyBackend

    for tutorial in _shipped():
        text = json.dumps(tutorial['steps'])
        aliases = set(re.findall(r"params\.(?:value|is_free)\('([^']+)'\)", text))
        for step in tutorial['steps']:
            aliases |= {
                action['args'][1]
                for action in step['actions']
                if action['verb'] == 'call' and action['args'][0] == 'analysis.setParameterValue'
            }
        global_object.registry.clear()  # one backend per tutorial
        backend = PyBackend()
        backend.project.loadExample((ROOT / 'EasyReflectometryApp' / 'Examples' / tutorial['example']).as_posix())
        known = {row['alias'] for row in backend.analysis._parameters_logic.all_parameters()}
        assert aliases <= known, f'{tutorial["id"]}: unknown aliases {sorted(aliases - known)}'


def test_every_read_more_link_points_at_a_heading_of_the_documentation():
    make_id = pytest.importorskip('docutils.nodes').make_id
    for step in _steps():
        page, _, anchor = step['more'].partition('#')
        source = DOCS / (page[: -len('.html')] + '.md')
        assert source.is_file(), step['more']
        if anchor:
            headings = [
                make_id(title) for title in re.findall(r'^#+ (.+)$', source.read_text(encoding='utf-8'), flags=re.MULTILINE)
            ]
            # A heading used twice gets another id the second time.
            assert headings.count(anchor) == 1, step['more']
