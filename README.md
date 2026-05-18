# shovels-gitlint-rules

Shared custom [gitlint](https://jorisroovers.com/gitlint/) rules used across Shovels repos.

## Rules

| ID | Name | What it catches |
| --- | --- | --- |
| `UL100` | `title-starts-capitalized` | Title doesn't start with a capital letter (A-Z). |
| `UL101` | `title-no-conventional-commits-prefix` | Conventional-commits prefix at the start of the title: `<type>:` or `<type>(<scope>):` (e.g. `fix:`, `feat(api):`, `chore(ci):`). Matches any letter-only type, case-insensitive. |
| `UC100` | `body-no-ticket-id` | Ticket IDs in the commit body (`ENG-1234`, `JIRA-9`, `GH-100`, etc.). Linear linkage comes from the branch name. |

Rationale: see [`ENG-2640`](https://linear.app/shovels/issue/ENG-2640).

## Install into a target repo

Use the injector — it copies the two rule files into `gitlint_rules/`, sets `extra-path` in `.gitlint`, and adds the gitlint hook to `.pre-commit-config.yaml` if missing. It is idempotent.

```bash
uv run python scripts/inject_gitlint_rules.py /path/to/target-repo
```

After injection, in the target repo:

```bash
pre-commit install --hook-type commit-msg
```

## Development

```bash
uv sync
uv run pytest
```

End-to-end smoke test against the bundled rules:

```bash
echo "fix: lowercase" | uv run gitlint --extra-path gitlint_rules     # fails UL100
printf "Real title\n\nCloses ENG-1\n" | uv run gitlint --extra-path gitlint_rules  # fails UC100
```
