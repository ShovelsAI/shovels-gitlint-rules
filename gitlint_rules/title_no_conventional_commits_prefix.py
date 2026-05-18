import re

from gitlint.rules import LineRule, RuleViolation, CommitMessageTitle

CONV_COMMITS_RE = re.compile(r"^[A-Za-z]+(?:\([A-Za-z]+\))?:", re.IGNORECASE)


class TitleNoConventionalCommitsPrefix(LineRule):
    name = "title-no-conventional-commits-prefix"
    id = "UL101"
    target = CommitMessageTitle

    def validate(self, line, _commit):
        if not line:
            return []
        match = CONV_COMMITS_RE.match(line)
        if not match:
            return []
        return [
            RuleViolation(
                self.id,
                (
                    f"Title must not use a conventional-commits prefix (found '{match.group(0)}'). "
                    "Drop the 'type:' or 'type(scope):' prefix and write a capitalized imperative, "
                    "e.g. 'Fix login redirect' instead of 'fix: login redirect' or 'fix(auth): login redirect'."
                ),
                line,
            )
        ]
