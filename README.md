# shovels-gitlint-rules

Shared custom [gitlint](https://jorisroovers.com/gitlint/) rules used across Shovels repos, packaged as a pre-commit hook.

## Rules

| ID | Name | What it catches |
| --- | --- | --- |
| `UL100` | `title-starts-capitalized` | Title doesn't start with a capital letter (A-Z). |
| `UL101` | `title-no-conventional-commits-prefix` | Conventional-commits prefix at the start of the title: `<type>:` or `<type>(<scope>):` (e.g. `fix:`, `feat(api):`, `chore(ci):`). Matches any letter-only type, case-insensitive. |
| `UC100` | `body-no-ticket-id` | Ticket IDs in the commit body (`ENG-1234`, `JIRA-9`, `GH-100`, etc.). Linear linkage comes from the branch name. |

Rationale: see [`ENG-2640`](https://linear.app/shovels/issue/ENG-2640).

## Use in a Shovels repo

Add to `.pre-commit-config.yaml` (and remove the standalone `jorisroovers/gitlint` hook if present — this hook runs gitlint itself):

```yaml
- repo: git@github.com:ShovelsAI/shovels-gitlint-rules.git
  rev: v0.3.1
  hooks:
    - id: shovels-gitlint
      stages: [commit-msg]
```

> SSH URL is required because the repo is private. All Shovels engineers already have SSH access via their existing GitHub keys.

Then:

```bash
pre-commit install --hook-type commit-msg
```

`.gitlint` is still used for built-in rules (title-max-length, body-min-length, etc.) — only the custom rules are injected by this hook.

### Automated rollout

`scripts/inject_gitlint_rules.py` does the `.pre-commit-config.yaml` edit and cleans up legacy vendored artifacts:

```bash
uv run python scripts/inject_gitlint_rules.py /path/to/target-repo
```

## How it works

gitlint discovers user-defined rules exclusively via `--extra-path`. Rather than vendoring rule files into every repo, we ship them inside this package and provide a `shovels-gitlint` console script that invokes gitlint with `--extra-path` set to the packaged rules directory. pre-commit installs the package into its hook venv from git; one rev bump in `.pre-commit-config.yaml` is the only thing each consuming repo ever changes.

## Development

```bash
uv sync
uv run pytest
```

End-to-end smoke test:

```bash
echo "fix: lowercase" | uv run shovels-gitlint            # fails UL100 + UL101
printf "Real title\n\nCloses ENG-1 here\n" | uv run shovels-gitlint  # fails UC100
```
