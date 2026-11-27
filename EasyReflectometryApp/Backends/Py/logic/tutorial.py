"""Interactive tutorials: the step state machine and the facts its conditions read.

See MD/INTERACTIVE_TUTORIALS_DESIGN.md. Plain Python: the Qt wrapper (Backends/Py/tutorial.py)
supplies the facts and calls in when something the conditions depend on changes.
"""

import io
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Callable

from asteval import Interpreter

logger = logging.getLogger(__name__)

#: Written by tools/make_tutorials.py from the documentation.
TUTORIALS_DIR = Path(__file__).resolve().parents[3] / 'Tutorials'
EXAMPLES_DIR = Path(__file__).resolve().parents[3] / 'Examples'
FORMAT = 1

# How a fit ended, as the `step.*` counters count it.
FIT_OUTCOMES = ('finished', 'cancelled', 'failed', 'refused')

FIT_NOT_DONE = 'The fit did not complete this step.'
BLOCKED = 'The app is no longer in the state this step needs. Restart the tutorial to start again.'
INVALID = 'This step cannot be checked. Skip it to go on.'


def available_tutorials(directory: Path = TUTORIALS_DIR, examples_dir: Path = EXAMPLES_DIR) -> list[dict]:
    """The shipped tutorials in the order of `index.json`, each with the absolute path of its example.

    A missing or unreadable file, or one of another format, is left out: a packaging fault
    must not stop the app from starting.
    """
    try:
        ids = json.loads((directory / 'index.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        logger.warning('Cannot read the index of the tutorials in %s', directory, exc_info=True)
        return []
    tutorials = []
    for tutorial_id in ids:
        try:
            definition = json.loads((directory / f'{tutorial_id}.json').read_text(encoding='utf-8'))
        except (OSError, ValueError):
            logger.warning('Cannot read the tutorial %s', tutorial_id, exc_info=True)
            continue
        if definition.get('format') != FORMAT:
            logger.warning('Tutorial %s has format %s, not %s', tutorial_id, definition.get('format'), FORMAT)
            continue
        definition['examplePath'] = (examples_dir / definition['example']).as_posix()
        tutorials.append(definition)
    return tutorials


class ParameterFacts:
    """`params.*`: the parameters by alias, read from the unfiltered table rows."""

    def __init__(self, free: int, rows: Callable[[], list[dict]]):
        self.free = free
        self._rows = rows
        self._by_alias = None

    def value(self, alias: str) -> float:
        return self._row(alias)['value']

    def is_free(self, alias: str) -> bool:
        return bool(self._row(alias)['fit'])

    def _row(self, alias: str) -> dict:
        if self._by_alias is None:
            self._by_alias = {row['alias']: row for row in self._rows()}
        # An unknown alias raises, so that the condition is reported as invalid rather than false.
        return self._by_alias[alias]


class TutorialRun:
    """One run through a tutorial, from its first step to `finished` or `stopped`.

    `read_facts()` returns the fact namespaces (`ui`, `project`, `params`, `fit`, ...) as they
    are now; the run adds `step`, its own counters since the current step was entered.
    """

    def __init__(self, definition: dict, read_facts: Callable[[], dict]):
        self.definition = definition
        self._read_facts = read_facts
        self.state = 'active'  # active | finished | stopped
        self.stop_reason = ''
        self.index = 0
        self._done = set()  # ids of the steps done once in this run: they stay done
        self._skipped = set()
        self._enter()

    @property
    def steps(self) -> list[dict]:
        return self.definition['steps']

    @property
    def step(self) -> dict:
        return self.steps[self.index]

    @property
    def completed(self) -> bool:
        """Finished without skipping a step: what is saved as completed."""
        return self.state == 'finished' and not self._skipped

    @property
    def can_next(self) -> bool:
        return self.state == 'active' and (not self.step['done'] or self.step_state == 'done')

    @property
    def auto_advance(self) -> bool:
        """The step became done during this visit and moves on by itself (`advance: auto`)."""
        return self.state == 'active' and self.step['advance'] and self._just_done

    def evaluate(self) -> None:
        """Check the current step against the facts as they are now."""
        if self.state != 'active' or self.step['id'] in self._done:
            return
        if self.message in (BLOCKED, INVALID):
            self.message = ''  # re-established below if it still applies
        requires = self.step['requires']
        if requires:
            holds = self._check(requires)
            if not holds:
                self.step_state, self.message = ('invalid', INVALID) if holds is None else ('blocked', BLOCKED)
                return
        if not self.step['done']:
            self.step_state = 'waiting'
            return
        done = self._check(self.step['done'])
        if done is None:
            self.step_state, self.message = 'invalid', INVALID
        elif done:
            self._done.add(self.step['id'])
            self.step_state, self.message = 'done', ''
            self._just_done = True
        else:
            self.step_state = 'waiting'

    def fit_ended(self, outcome: str) -> None:
        """A fit ended (one of FIT_OUTCOMES); explain when it did not complete the step."""
        if self.state != 'active':
            return
        self._counters[outcome] += 1
        self.evaluate()
        if self.step['done'] and self.step_state == 'waiting':
            self.message = self.step['hint'] or FIT_NOT_DONE

    def next(self) -> bool:
        if not self.can_next:
            return False
        self._move_on()
        return True

    def skip(self) -> None:
        if self.state == 'active':
            self._skipped.add(self.step['id'])
            self._move_on()

    def previous(self) -> None:
        if self.state == 'active' and self.index > 0:
            self.index -= 1
            self._enter()

    def stop(self, reason: str) -> None:
        if self.state == 'active':
            self.state, self.stop_reason = 'stopped', reason

    def _move_on(self) -> None:
        if self.index == len(self.steps) - 1:
            self.state = 'finished'
        else:
            self.index += 1
            self._enter()

    def _enter(self) -> None:
        self._counters = dict.fromkeys(FIT_OUTCOMES, 0)
        self._just_done = False
        self.message = ''
        self.step_state = 'done' if self.step['id'] in self._done else 'waiting'
        self.evaluate()

    def _check(self, expression: str) -> bool | None:
        """The condition's truth, or None when it cannot be evaluated (logged)."""
        counters = {f'fits_{outcome}': count for outcome, count in self._counters.items()}
        symbols = {**self._read_facts(), 'step': SimpleNamespace(**counters), 'abs': abs}
        # Given a symbol table, asteval uses it alone: no builtins beyond `abs`.
        interpreter = Interpreter(symtable=symbols, writer=io.StringIO(), err_writer=io.StringIO())
        result = interpreter(expression)
        if interpreter.error:
            logger.warning(
                'Tutorial %s, step %s: cannot evaluate "%s": %s',
                self.definition['id'],
                self.step['id'],
                expression,
                interpreter.error[0].get_error()[1].splitlines()[-1],
            )
            return None
        return bool(result)
