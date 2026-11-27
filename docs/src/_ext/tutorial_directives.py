"""Sphinx extension: renders the interactive tutorial blocks on the website.

```{tutorial}``` becomes a note that the page can be followed in the app, and each
```{tutorial-step}``` a numbered box with its title and body; the option lines are not shown.
See MD/INTERACTIVE_TUTORIALS_DESIGN.md.

The app reads the same blocks with tools/tutorial_steps.py, not with MyST. So that both read a
block the same way, each step is parsed again with that module and compared with what MyST
handed the directive; a difference stops the build.
"""

from pathlib import Path

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from sphinx.errors import ExtensionError
from tutorial_steps import STEP_OPTIONS
from tutorial_steps import TUTORIAL_OPTIONS
from tutorial_steps import read_blocks


class TutorialDirective(Directive):
    required_arguments = 1
    final_argument_whitespace = True
    option_spec = {name: directives.unchanged for name in TUTORIAL_OPTIONS}

    def run(self):
        note = nodes.note()
        note += nodes.paragraph(
            text=f'This tutorial, “{self.arguments[0]}”, can be followed step by step in the app: '
            'Home › Tutorials. The steps below are the ones the app shows.'
        )
        return [note]


class TutorialStepDirective(Directive):
    required_arguments = 1
    final_argument_whitespace = True
    has_content = True
    option_spec = {name: directives.unchanged for name in STEP_OPTIONS}

    def run(self):
        env = self.state.document.settings.env
        _check_against_parser(env, self.arguments[0], self.options, '\n'.join(self.content).strip())
        numbers = env.temp_data.setdefault('tutorial_step_numbers', {})
        numbers[env.docname] = numbers.get(env.docname, 0) + 1
        box = nodes.admonition(classes=['tutorial-step'])
        box += nodes.title(text=f'Step {numbers[env.docname]}: {self.arguments[0]}')
        self.state.nested_parse(self.content, self.content_offset, box)
        return [box]


def _check_against_parser(env, title: str, options: dict, body: str) -> None:
    cache = env.temp_data.setdefault('tutorial_blocks', {})
    if env.docname not in cache:
        source = Path(env.doc2path(env.docname))
        blocks = read_blocks(source.read_text(encoding='utf-8'), str(source))
        cache[env.docname] = [block for block in blocks if block['kind'] == 'tutorial-step']
    ours = next((block for block in cache[env.docname] if block['options'].get('id') == options.get('id')), None)
    theirs = {'title': title, 'options': {key: value.strip() for key, value in options.items()}, 'body': body}
    if ours is None or {key: ours[key] for key in theirs} != theirs:
        raise ExtensionError(
            f'{env.docname}: MyST and tools/tutorial_steps.py read the tutorial step "{options.get("id")}" '
            f'differently.\nMyST: {theirs}\nparser: {ours}'
        )


def setup(app):
    app.add_directive('tutorial', TutorialDirective)
    app.add_directive('tutorial-step', TutorialStepDirective)
    return {'parallel_read_safe': True, 'parallel_write_safe': True}
