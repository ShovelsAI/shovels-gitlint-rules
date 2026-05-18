import pytest

from gitlint_rules.title_no_conventional_commits_prefix import TitleNoConventionalCommitsPrefix


@pytest.fixture
def rule():
    return TitleNoConventionalCommitsPrefix()


@pytest.mark.parametrize(
    "title",
    [
        "fix: login redirect",
        "feat: add retry logic",
        "chore: bump deps",
        "fix(auth): login redirect",
        "feat(api): add retry logic",
        "chore(ci): bump action versions",
        # case-insensitive
        "Fix: login",
        "FIX: login",
        "Feat(API): something",
        "CHORE(CI): something",
        # arbitrary type word, not just the canonical three
        "refactor: clean up",
        "docs(readme): explain x",
        "perf(query): speed up join",
        "wibble(zorp): nonsense",
    ],
)
def test_fails_on_conv_commits_prefix(rule, title):
    violations = rule.validate(title, _commit=None)
    assert len(violations) == 1, f"expected violation for: {title}"
    assert violations[0].rule_id == "UL101"


@pytest.mark.parametrize(
    "title",
    [
        "Fix login redirect",
        "Add retry logic",
        "Refactor adapter base class",
        # colon present, but not in conv-commits position
        "Title with: a colon mid-sentence",
        # parens but no colon
        "Refactor (again)",
        # numbers/symbols at start — caught by UL100 capital rule, not this one
        "123 numeric start",
        # scope with disallowed char (digits) — per spec, scope is letters only
        "fix(api2): scoped digits",
        # multi-word type — per spec, type is contiguous letters
        "fix it: broken thing",
    ],
)
def test_passes_when_no_conv_commits_prefix(rule, title):
    assert rule.validate(title, _commit=None) == []


def test_passes_on_empty_title(rule):
    assert rule.validate("", _commit=None) == []
