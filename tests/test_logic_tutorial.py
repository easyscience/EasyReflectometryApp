"""The tutorial state machine (Backends/Py/logic/tutorial.py) with fake facts."""

import json
from types import SimpleNamespace

import pytest

from EasyReflectometryApp.Backends.Py.logic import tutorial as tutorial_logic
from EasyReflectometryApp.Backends.Py.logic.tutorial import BLOCKED
from EasyReflectometryApp.Backends.Py.logic.tutorial import FIT_NOT_DONE
from EasyReflectometryApp.Backends.Py.logic.tutorial import INVALID
from EasyReflectometryApp.Backends.Py.logic.tutorial import ParameterFacts
from EasyReflectometryApp.Backends.Py.logic.tutorial import TutorialRun
from EasyReflectometryApp.Backends.Py.logic.tutorial import available_tutorials


def _step(step_id, done='', advance=False, requires='', hint=''):
    return {'id': step_id, 'done': done, 'advance': advance, 'requires': requires, 'hint': hint}


class Facts:
    """What the Qt part would read from the app, settable by the test."""

    def __init__(self):
        self.ui = {'page': 'home'}
        self.thickness = 250.0
        self.chi2 = 0.0

    def __call__(self):
        rows = [{'alias': 'film_thickness', 'value': self.thickness, 'fit': True}]
        return {
            'ui': SimpleNamespace(**self.ui),
            'params': ParameterFacts(1, lambda: rows),
            'fit': SimpleNamespace(reduced_chi2=self.chi2),
        }


def _run(*steps):
    facts = Facts()
    return TutorialRun({'id': 'test', 'steps': list(steps)}, facts), facts


def test_a_reading_step_can_be_left_at_once_and_the_last_one_finishes_the_run():
    run, _ = _run(_step('read'), _step('last'))

    assert run.state == 'active' and run.step_state == 'waiting' and run.can_next
    assert run.next() and run.index == 1
    assert run.next() and run.state == 'finished' and run.completed


def test_a_step_with_a_condition_waits_and_then_waits_for_next():
    run, facts = _run(_step('analysis', done="ui.page == 'analysis'"), _step('last'))

    assert not run.can_next and not run.next()
    facts.ui['page'] = 'analysis'
    run.evaluate()
    assert run.step_state == 'done' and run.can_next
    # Done does not move on: only Next does (or `advance`).
    assert run.index == 0 and not run.auto_advance


def test_advance_auto_only_when_the_step_became_done_in_this_visit():
    run, facts = _run(_step('analysis', done="ui.page == 'analysis'", advance=True), _step('last'))
    facts.ui['page'] = 'analysis'
    run.evaluate()
    assert run.auto_advance

    run.next()
    run.previous()
    # Back on a done step: it shows done, and does not move on by itself again.
    assert run.step_state == 'done' and run.can_next and not run.auto_advance


def test_a_step_already_true_on_first_entry_is_done_at_once():
    run, facts = _run(_step('read'), _step('analysis', done="ui.page == 'analysis'"))
    facts.ui['page'] = 'analysis'

    run.next()

    assert run.step_state == 'done'


def test_fit_counters_start_again_on_entry_but_a_done_step_stays_done():
    fit_done = 'step.fits_finished >= 1 and fit.reduced_chi2 < 5'
    run, facts = _run(_step('fit', done=fit_done), _step('read'))
    facts.chi2 = 2.4

    # A fit before the step does not count, whatever the facts say.
    assert run.step_state == 'waiting'
    run.fit_ended('finished')
    assert run.step_state == 'done'

    run.next()
    run.previous()
    assert run.step_state == 'done' and run.can_next


@pytest.mark.parametrize('outcome', ['cancelled', 'failed', 'refused'])
def test_a_fit_that_does_not_complete_the_step_explains_with_the_hint(outcome):
    run, _ = _run(_step('fit', done='step.fits_finished >= 1', hint='Try again.'))

    run.fit_ended(outcome)

    assert run.step_state == 'waiting' and run.message == 'Try again.'


def test_a_poor_fit_gets_the_default_message_without_a_hint():
    run, facts = _run(_step('fit', done='step.fits_finished >= 1 and fit.reduced_chi2 < 5'))
    facts.chi2 = 50.0

    run.fit_ended('finished')

    assert run.step_state == 'waiting' and run.message == FIT_NOT_DONE


def test_parameters_are_read_by_alias_and_an_unknown_alias_makes_the_step_invalid():
    run, facts = _run(_step('value', done="abs(params.value('film_thickness') - 200) < 5"))
    facts.thickness = 201.0
    run.evaluate()
    assert run.step_state == 'done'

    run, _ = _run(_step('typo', done="params.value('no_such_alias') < 220"))
    assert run.step_state == 'invalid' and run.message == INVALID and not run.can_next


@pytest.mark.parametrize('expression', ['sorted([1]) == [1]', 'open("x")', 'undefined_name', 'params.value('])
def test_a_broken_condition_is_invalid_not_false(expression):
    run, _ = _run(_step('broken', done=expression))

    assert run.step_state == 'invalid'


def test_requires_blocks_the_step_until_it_holds_again():
    run, facts = _run(_step('needs-analysis', requires="ui.page == 'analysis'"))
    assert run.step_state == 'blocked' and run.message == BLOCKED

    facts.ui['page'] = 'analysis'
    run.evaluate()
    assert run.step_state == 'waiting' and run.message == ''


def test_skip_moves_on_but_the_finished_run_is_not_completed():
    run, _ = _run(_step('fit', done='step.fits_finished >= 1'), _step('last'))

    run.skip()
    run.next()

    assert run.state == 'finished' and not run.completed


def test_a_stopped_run_ignores_everything_after():
    run, _ = _run(_step('fit', done='step.fits_finished >= 1'), _step('last'))

    run.stop('replaced')
    run.fit_ended('finished')

    assert run.state == 'stopped' and run.stop_reason == 'replaced'
    assert not run.next() and run.index == 0


def test_available_tutorials_skips_what_it_cannot_read(tmp_path):
    assert available_tutorials(tmp_path) == []

    (tmp_path / 'index.json').write_text(json.dumps(['good', 'missing', 'old']), encoding='utf-8')
    (tmp_path / 'good.json').write_text(json.dumps({'format': 1, 'id': 'good', 'example': 'A/project.json'}), encoding='utf-8')
    (tmp_path / 'old.json').write_text(json.dumps({'format': 0, 'id': 'old', 'example': 'B/project.json'}), encoding='utf-8')

    [good] = available_tutorials(tmp_path, examples_dir=tmp_path / 'Examples')

    assert good['id'] == 'good'
    assert good['examplePath'] == (tmp_path / 'Examples' / 'A' / 'project.json').as_posix()


def test_the_shipped_tutorials_are_found():
    index = json.loads((tutorial_logic.TUTORIALS_DIR / 'index.json').read_text(encoding='utf-8'))
    assert [tutorial['id'] for tutorial in available_tutorials()] == index and index
    assert tutorial_logic.FORMAT == 1
