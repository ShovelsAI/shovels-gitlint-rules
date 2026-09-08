import re

from gitlint.rules import CommitRule, RuleViolation

PROVENANCE_TRAILER_RE = re.compile(r"^\s*(claude-session|generated-(with|by))\s*:", re.IGNORECASE)
CO_AUTHORED_BY_RE = re.compile(r"^\s*co-authored-by\s*:(?P<value>.*)$", re.IGNORECASE)
BOT_CO_AUTHOR_RE = re.compile(r"\bbot\b|\[bot\]|noreply@anthropic|claude", re.IGNORECASE)


class BodyNoToolProvenanceTrailer(CommitRule):
    name = "body-no-tool-provenance-trailer"
    id = "UC101"

    def validate(self, commit):
        violations = []
        for idx, line in enumerate(commit.message.body, start=1):
            trailer = self._offending_trailer(line)
            if trailer:
                violations.append(
                    RuleViolation(
                        self.id,
                        (
                            f"Body must not contain tool-provenance trailers (found '{trailer}'). "
                            "History must be self-contained; a session link or agent "
                            "attribution points at something no reader of the repo can open. "
                            "Remove the trailer rather than rewording it."
                        ),
                        line_nr=idx,
                    )
                )
        return violations

    @staticmethod
    def _offending_trailer(line: str) -> str | None:
        match = PROVENANCE_TRAILER_RE.match(line)
        if match:
            return match.group(0).strip()
        match = CO_AUTHORED_BY_RE.match(line)
        if match and BOT_CO_AUTHOR_RE.search(match.group("value")):
            return line.strip()
        return None
