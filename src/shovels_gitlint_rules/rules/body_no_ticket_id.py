import re

from gitlint.rules import CommitRule, RuleViolation

TICKET_RE = re.compile(r"\b[A-Z]+-\d+\b")


class BodyNoTicketId(CommitRule):
    name = "body-no-ticket-id"
    id = "UC100"

    def validate(self, commit):
        violations = []
        for idx, line in enumerate(commit.message.body, start=1):
            match = TICKET_RE.search(line)
            if match:
                violations.append(
                    RuleViolation(
                        self.id,
                        (
                            f"Body must not contain ticket IDs (found '{match.group(0)}'). "
                            "Linear linkage comes from the branch name; restating it in the "
                            "commit body is duplication. Remove 'Closes ENG-XXXX', "
                            "'Part of ENG-XXXX', JIRA-123, GH-456, etc."
                        ),
                        line_nr=idx,
                    )
                )
        return violations
