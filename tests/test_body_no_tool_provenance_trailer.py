from types import SimpleNamespace

import pytest

from shovels_gitlint_rules.rules.body_no_tool_provenance_trailer import (
    BodyNoToolProvenanceTrailer,
)


def _commit(body_lines: list[str]):
    return SimpleNamespace(message=SimpleNamespace(body=body_lines))


@pytest.fixture
def rule():
    return BodyNoToolProvenanceTrailer()


def test_passes_when_body_has_no_trailer(rule):
    commit = _commit(["", "Refactor the retry logic to handle 429s cleanly."])
    assert rule.validate(commit) == []


def test_passes_on_empty_body(rule):
    assert rule.validate(_commit([])) == []


@pytest.mark.parametrize(
    "line",
    [
        "Claude-Session: https://claude.ai/code/session_01ABC",
        "claude-session: https://claude.ai/code/session_01ABC",
        "  Claude-Session : https://claude.ai/code/session_01ABC",
        "Generated-With: Claude Code",
        "Generated-By: some-tool",
        "GENERATED-BY: some-tool",
    ],
)
def test_fails_on_provenance_trailer(rule, line):
    violations = rule.validate(_commit(["", line]))
    assert len(violations) == 1
    assert violations[0].rule_id == "UC101"
    assert violations[0].line_nr == 2


@pytest.mark.parametrize(
    "line",
    [
        "Co-Authored-By: Claude <noreply@anthropic.com>",
        "co-authored-by: Claude Opus <noreply@anthropic.com>",
        "Co-Authored-By: dependabot[bot] <support@github.com>",
        "Co-Authored-By: Release Bot <release@example.com>",
    ],
)
def test_fails_on_bot_co_author(rule, line):
    violations = rule.validate(_commit(["", line]))
    assert len(violations) == 1
    assert violations[0].rule_id == "UC101"


@pytest.mark.parametrize(
    "line",
    [
        "Co-Authored-By: Jane Doe <jane@shovels.ai>",
        "Co-authored-by: Abbott Costello <abbott@example.com>",
        "Signed-off-by: Jane Doe <jane@shovels.ai>",
    ],
)
def test_passes_on_human_co_author_and_other_trailers(rule, line):
    assert rule.validate(_commit(["", line])) == []


def test_ignores_key_not_at_line_start(rule):
    assert rule.validate(_commit(["This drops the Claude-Session: trailer from history."])) == []


def test_reports_each_offending_line(rule):
    body = [
        "fine line",
        "Claude-Session: https://claude.ai/code/session_01ABC",
        "Co-Authored-By: Claude <noreply@anthropic.com>",
    ]
    assert len(rule.validate(_commit(body))) == 2
