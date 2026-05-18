import pytest

from shovels_gitlint_rules.rules.title_starts_capitalized import TitleStartsCapitalized


@pytest.fixture
def rule():
    return TitleStartsCapitalized()


@pytest.mark.parametrize(
    "title",
    [
        "Fix login redirect",
        "Add retry logic for 429s",
        "Refactor adapter base class",
        "Update gitlint config",
    ],
)
def test_passes_when_title_capitalized(rule, title):
    assert rule.validate(title, _commit=None) == []


@pytest.mark.parametrize(
    "title",
    [
        "fix: something",  # also caught by UL101, that's fine
        "feat: add thing",
        "chore: bump deps",
        "lowercase start",
        "  indented title",
        "123 numeric start",
    ],
)
def test_fails_when_title_not_capitalized(rule, title):
    violations = rule.validate(title, _commit=None)
    assert len(violations) == 1
    assert violations[0].rule_id == "UL100"


def test_passes_on_empty_title(rule):
    # gitlint handles empty-title via built-in rules; ours just shouldn't crash.
    assert rule.validate("", _commit=None) == []
