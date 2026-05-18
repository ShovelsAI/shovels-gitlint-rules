import re

from gitlint.rules import LineRule, RuleViolation, CommitMessageTitle

CAPITAL_RE = re.compile(r"^[A-Z]")


class TitleStartsCapitalized(LineRule):
    name = "title-starts-capitalized"
    id = "UL100"
    target = CommitMessageTitle

    def validate(self, line, _commit):
        if not line:
            return []
        if CAPITAL_RE.match(line):
            return []
        return [
            RuleViolation(
                self.id,
                (
                    "Title must start with a capital letter (A-Z). "
                    "Use a capitalized imperative like 'Fix login redirect' or 'Add retry logic'. "
                    "Common offenders: lowercase first word, leading whitespace, leading digits or symbols."
                ),
                line,
            )
        ]
