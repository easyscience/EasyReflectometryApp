"""Reads the interactive tutorial blocks of a documentation page (MD/INTERACTIVE_TUTORIALS_DESIGN.md).

A page holds one ```{tutorial}``` block and a sequence of ```{tutorial-step}``` blocks. The
grammar is deliberately small, so that this parser and MyST read a block the same way:

    ```{tutorial-step} Title
    :key: value          one option per line, split at the first ': '
    :key: value          (MyST reads the options as YAML, so a value cannot start with a
                         YAML indicator such as # * ' " [ or contain ' #' or ': ')
                         a blank line
    Body in plain Markdown, without nested fences, directives or images.
    ```

No Sphinx or Qt dependency: the generator (make_tutorials.py), the Sphinx extension and the
tests all use this module.
"""

import ast
import json
import posixpath
import re
import shlex

PAGES = ('home', 'project', 'sample', 'experiment', 'analysis', 'summary')
SIDEBAR_TABS = ('basic', 'advanced')
# The symbols a condition may use (logic/tutorial.py provides them).
FACT_NAMESPACES = frozenset(
    {'ui', 'project', 'models', 'sample', 'experiments', 'params', 'fit', 'plot', 'step', 'abs', 'len'}
)

TUTORIAL_OPTIONS = {'id', 'example', 'data', 'minutes', 'summary'}
STEP_OPTIONS = {'id', 'page', 'sidebar-tab', 'target', 'done', 'do', 'advance', 'requires', 'hint', 'more'}

# Action verb -> number of arguments (None: one or more)
VERBS = {'goto': 1, 'sidebar-tab': 1, 'click': 1, 'set': 2, 'call': None}

# Starts of a value that YAML would not read as a plain string
_YAML_INDICATORS = tuple('#\'"[]{}&*!|>%@,`-?:')
_OPENING = re.compile(r'^```\{(tutorial|tutorial-step)\}\s*(.*?)\s*$')
_OPTION = re.compile(r'^:([a-z][a-z-]*):(?: (.*))?$')
_CLOSING = '```'


class TutorialFormatError(ValueError):
    """A tutorial block that does not follow the grammar; the message names the file and line."""


def read_blocks(text: str, source: str = '<text>') -> list[dict]:
    """Every tutorial block of a page, in order: {kind, title, options, body, line}."""
    blocks = []
    lines = text.splitlines()
    number = 0
    while number < len(lines):
        opening = _OPENING.match(lines[number])
        number += 1
        if opening is None:
            continue
        block = {'kind': opening.group(1), 'title': opening.group(2), 'options': {}, 'line': number}
        body = []
        in_options = True
        while True:
            if number >= len(lines):
                raise TutorialFormatError(f'{source}:{block["line"]}: the block is not closed')
            line = lines[number]
            number += 1
            if line.strip() == _CLOSING:
                break
            if line.lstrip().startswith('```'):
                raise TutorialFormatError(f'{source}:{number}: a tutorial block cannot hold a fenced block')
            option = _OPTION.match(line) if in_options else None
            if option is not None:
                key, value = option.group(1), (option.group(2) or '').strip()
                if key in block['options']:
                    raise TutorialFormatError(f'{source}:{number}: option "{key}" given twice')
                if value.startswith(_YAML_INDICATORS) or ' #' in value or ': ' in value:
                    raise TutorialFormatError(
                        f'{source}:{number}: MyST would read the value of "{key}" differently '
                        "(it cannot start with # * ' \" [ and the like, or contain ' #' or ': ')"
                    )
                block['options'][key] = value
                continue
            in_options = False
            body.append(line)
        block['body'] = '\n'.join(body).strip()
        blocks.append(block)
    return blocks


def parse_actions(text: str) -> list[dict]:
    """`do` option -> [{verb, args}]. Actions are separated by ';', arguments by spaces;
    a value with spaces is put in double quotes. `call` arguments after the slot are JSON
    values where they parse as JSON, strings otherwise."""
    actions = []
    for part in text.split(';'):
        words = shlex.split(part)
        if not words:
            raise TutorialFormatError(f'empty action in "{text}"')
        verb, args = words[0], words[1:]
        if verb not in VERBS:
            raise TutorialFormatError(f'unknown action "{verb}"')
        arity = VERBS[verb]
        if (arity is None and not args) or (arity is not None and len(args) != arity):
            raise TutorialFormatError(f'wrong number of arguments for "{verb}" in "{part.strip()}"')
        if verb == 'goto' and args[0] not in PAGES:
            raise TutorialFormatError(f'unknown page "{args[0]}"')
        if verb == 'sidebar-tab' and args[0] not in SIDEBAR_TABS:
            raise TutorialFormatError(f'unknown sidebar tab "{args[0]}"')
        if verb == 'call':
            if not re.fullmatch(r'[a-z]\w*\.[a-zA-Z]\w*', args[0]):
                raise TutorialFormatError(f'"call" needs <part>.<slot>, not "{args[0]}"')
            args = [args[0], *(_json_or_string(arg) for arg in args[1:])]
        actions.append({'verb': verb, 'args': args})
    return actions


def condition_names(expression: str) -> set[str]:
    """The top-level names a condition uses; raises TutorialFormatError if it is not an expression."""
    try:
        tree = ast.parse(expression, mode='eval')
    except SyntaxError as error:
        raise TutorialFormatError(f'not a Python expression: "{expression}" ({error.msg})') from None
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def parse_page(text: str, doc_name: str, source: str = '<text>') -> dict | None:
    """The tutorial of a page, checked and normalised, or None if the page has no tutorial.

    `doc_name` is the page's path in docs/src without the suffix ('tutorials/simple_fitting'),
    used to turn the `more` options into documentation URLs.
    """
    blocks = read_blocks(text, source)
    if not blocks:
        return None
    head, *steps = blocks
    if head['kind'] != 'tutorial' or any(step['kind'] != 'tutorial-step' for step in steps):
        raise TutorialFormatError(f'{source}: one {{tutorial}} block must come first, followed by {{tutorial-step}} blocks')
    if not steps:
        raise TutorialFormatError(f'{source}: the tutorial has no steps')
    # Without `example` the tutorial starts from a new, empty project. `data` lists files of
    # examples/datasets that the tutorial loads; they are shipped in Tutorials/data.
    _check_keys(head, TUTORIAL_OPTIONS, {'id', 'minutes', 'summary'}, source)
    try:
        minutes = int(head['options']['minutes'])
    except ValueError:
        raise TutorialFormatError(f'{source}:{head["line"]}: "minutes" must be a whole number') from None
    tutorial = {
        'id': head['options']['id'],
        'title': head['title'],
        'example': head['options'].get('example', ''),
        'data': [name.strip() for name in head['options'].get('data', '').split(',') if name.strip()],
        'minutes': minutes,
        'summary': head['options']['summary'],
        'steps': [_parse_step(block, doc_name, source) for block in steps],
    }
    ids = [step['id'] for step in tutorial['steps']]
    duplicates = sorted({step_id for step_id in ids if ids.count(step_id) > 1})
    if duplicates:
        raise TutorialFormatError(f'{source}: step ids used twice: {", ".join(duplicates)}')
    return tutorial


def _parse_step(block: dict, doc_name: str, source: str) -> dict:
    where = f'{source}:{block["line"]}'
    _check_keys(block, STEP_OPTIONS, {'id'}, source)
    options = block['options']
    target = options.get('target', '')
    page = options.get('page', '')
    if not page and not target.startswith('appbar.'):
        raise TutorialFormatError(f'{where}: "page" is needed unless the target is in the application bar')
    if page and page not in PAGES:
        raise TutorialFormatError(f'{where}: unknown page "{page}"')
    sidebar_tab = options.get('sidebar-tab', '')
    if sidebar_tab and sidebar_tab not in SIDEBAR_TABS:
        raise TutorialFormatError(f'{where}: unknown sidebar tab "{sidebar_tab}"')
    done, requires = options.get('done', ''), options.get('requires', '')
    for expression in filter(None, (done, requires)):
        try:
            unknown = condition_names(expression) - FACT_NAMESPACES
        except TutorialFormatError as error:
            raise TutorialFormatError(f'{where}: {error}') from None
        if unknown:
            raise TutorialFormatError(f'{where}: unknown names in "{expression}": {", ".join(sorted(unknown))}')
    if bool(done) != bool(options.get('do')):
        raise TutorialFormatError(f'{where}: a step with "done" needs "do", and "do" needs "done"')
    advance = options.get('advance', '')
    if advance not in ('', 'auto'):
        raise TutorialFormatError(f'{where}: "advance" can only be "auto"')
    if advance and (not done or condition_names(done) != {'ui'}):
        raise TutorialFormatError(f'{where}: "advance: auto" is only for steps whose "done" uses ui facts alone')
    if not block['title'] or not block['body']:
        raise TutorialFormatError(f'{where}: a step needs a title and a body')
    if '![' in block['body'] or '<img' in block['body']:
        raise TutorialFormatError(f'{where}: a step body cannot hold an image')
    try:
        actions = parse_actions(options['do']) if done else []
        more = _more_url(options.get('more', ''), doc_name)
    except TutorialFormatError as error:
        raise TutorialFormatError(f'{where}: {error}') from None
    return {
        'id': options['id'],
        'title': block['title'],
        'body': block['body'],
        'page': page,
        'sidebarTab': sidebar_tab,
        'target': target,
        'done': done,
        'actions': actions,
        'advance': bool(advance),
        'requires': requires,
        'hint': options.get('hint', ''),
        'more': more,
    }


def _check_keys(block: dict, allowed: set, required: set, source: str) -> None:
    keys = set(block['options'])
    if keys - allowed:
        raise TutorialFormatError(f'{source}:{block["line"]}: unknown options {", ".join(sorted(keys - allowed))}')
    if required - keys:
        raise TutorialFormatError(f'{source}:{block["line"]}: missing options {", ".join(sorted(required - keys))}')


def _more_url(more: str, doc_name: str) -> str:
    """'page.md' or 'page.md#anchor', relative to the page -> 'dir/page.html#anchor'; '' -> the page itself."""
    if not more:
        return f'{doc_name}.html'
    path, _, anchor = more.partition('#')
    if not path.endswith('.md'):
        raise TutorialFormatError(f'"more" must be page.md or page.md#anchor, not "{more}"')
    path = posixpath.normpath(posixpath.join(posixpath.dirname(doc_name), path[: -len('.md')]))
    return f'{path}.html' + (f'#{anchor}' if anchor else '')


def _json_or_string(text: str):
    try:
        return json.loads(text)
    except ValueError:
        return text
