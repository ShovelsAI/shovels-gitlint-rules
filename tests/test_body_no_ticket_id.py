from types import SimpleNamespace

import pytest

from gitlint_rules.body_no_ticket_id import BodyNoTicketId


def _commit(body_lines: list[str]):
    return SimpleNamespace(message=SimpleNamespace(body=body_lines))


@pytest.fixture
def rule():
    return BodyNoTicketId()


def test_passes_when_body_has_no_ticket(rule):
    commit = _commit(["", "Refactor the retry logic to handle 429s cleanly."])
    assert rule.validate(commit) == []


def test_passes_on_empty_body(rule):
    assert rule.validate(_commit([])) == []


@pytest.mark.parametrize(
    "line",
    [
        "Closes ENG-1234",
        "Part of ENG-42",
        "See JIRA-9 for context",
        "fixes GH-100 today",
        "ABC-1 in the middle of a sentence",
    ],
)
def test_fails_on_ticket_id(rule, line):
    violations = rule.validate(_commit(["", line]))
    assert len(violations) == 1
    assert violations[0].rule_id == "UC100"


def test_reports_each_offending_line(rule):
    violations = rule.validate(_commit(["fine line", "Closes ENG-1", "Part of JIRA-2"]))
    assert len(violations) == 2


def test_ignores_lowercase_dash_number(rule):
    # 'abc-123' is not a ticket; only uppercase-prefixed IDs match.
    assert rule.validate(_commit(["lowercase abc-123 should pass"])) == []


def test_ignores_isolated_numbers(rule):
    assert rule.validate(_commit(["bumped version to 1.2.3"])) == []
