"""Inject shovels-gitlint-rules into a target repo.

Idempotent. Run from the shovels-gitlint-rules repo root:

    uv run python scripts/inject_gitlint_rules.py /path/to/target-repo

Performs three changes on the target:

1. Copies rule files into ``<target>/.gitlint-rules/`` with an AUTO-GENERATED header.
2. Ensures ``<target>/.gitlint`` has ``[general] extra-path=.gitlint-rules`` (and
   creates a minimal ``.gitlint`` if missing).
3. Ensures ``<target>/.pre-commit-config.yaml`` has the gitlint hook on the
   ``commit-msg`` stage. Adds the hook block if the repo entry is missing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

GITLINT_REPO = "https://github.com/jorisroovers/gitlint"
GITLINT_REV = "v0.19.1"
RULE_FILES = (
    "body_no_ticket_id.py",
    "title_starts_capitalized.py",
    "title_no_conventional_commits_prefix.py",
)
AUTO_HEADER_TEMPLATE = (
    "# AUTO-GENERATED from shovels-gitlint-rules@{version}. DO NOT EDIT.\n"
    "# Source: https://github.com/ShovelsAI/shovels-gitlint-rules\n"
    "# Re-run scripts/inject_gitlint_rules.py to update.\n\n"
)


def _read_version(repo_root: Path) -> str:
    pyproject = (repo_root / "pyproject.toml").read_text()
    for line in pyproject.splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Could not find version in pyproject.toml")


def copy_rules(source_root: Path, target_root: Path, version: str) -> None:
    target_dir = target_root / "gitlint_rules"
    target_dir.mkdir(exist_ok=True)
    header = AUTO_HEADER_TEMPLATE.format(version=version)
    for name in RULE_FILES:
        src = source_root / "gitlint_rules" / name
        dst = target_dir / name
        dst.write_text(header + src.read_text())
        print(f"  wrote {dst.relative_to(target_root)}")
    init = target_dir / "__init__.py"
    if not init.exists():
        init.write_text("")


def update_gitlint(target_root: Path) -> None:
    path = target_root / ".gitlint"
    existing = path.read_text() if path.exists() else ""
    if "extra-path=gitlint_rules" in existing:
        print(f"  .gitlint already references extra-path; leaving as-is")
        return

    if not existing.strip():
        path.write_text(
            "[general]\n"
            "extra-path=gitlint_rules\n"
            "ignore=body-is-missing\n"
            "\n"
            "[title-max-length]\n"
            "line-length=50\n"
            "\n"
            "[body-max-line-length]\n"
            "line-length=72\n"
        )
        print(f"  created .gitlint")
        return

    lines = existing.splitlines(keepends=True)
    out: list[str] = []
    inserted = False
    in_general = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if in_general and not inserted:
                out.append("extra-path=gitlint_rules\n")
                inserted = True
            in_general = stripped == "[general]"
        out.append(line)
    if in_general and not inserted:
        if not out[-1].endswith("\n"):
            out.append("\n")
        out.append("extra-path=gitlint_rules\n")
        inserted = True
    if not inserted:
        prefix = "" if not out or out[-1].endswith("\n") else "\n"
        out.append(f"{prefix}[general]\nextra-path=gitlint_rules\n")
    path.write_text("".join(out))
    print(f"  updated .gitlint with extra-path=.gitlint-rules")


def update_precommit_config(target_root: Path) -> None:
    path = target_root / ".pre-commit-config.yaml"
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; cannot inject gitlint hook")

    config = yaml.load(path)
    repos = config.setdefault("repos", CommentedSeq())

    gitlint_entry = next(
        (r for r in repos if isinstance(r, dict) and r.get("repo") == GITLINT_REPO), None
    )
    if gitlint_entry is None:
        hook = CommentedMap()
        hook["id"] = "gitlint"
        hook["stages"] = ["commit-msg"]
        entry = CommentedMap()
        entry["repo"] = GITLINT_REPO
        entry["rev"] = GITLINT_REV
        entry["hooks"] = [hook]
        repos.append(entry)
        print(f"  added gitlint hook to .pre-commit-config.yaml")
    else:
        hooks = gitlint_entry.get("hooks", [])
        gitlint_hook = next((h for h in hooks if h.get("id") == "gitlint"), None)
        if gitlint_hook is None:
            hooks.append(
                CommentedMap([("id", "gitlint"), ("stages", ["commit-msg"])])
            )
            print(f"  added gitlint hook to existing gitlint repo entry")
        else:
            stages = gitlint_hook.get("stages")
            if not stages or "commit-msg" not in stages:
                gitlint_hook["stages"] = ["commit-msg"]
                print(f"  set stages: [commit-msg] on gitlint hook")
            else:
                print(f"  gitlint hook already configured; leaving as-is")

    yaml.dump(config, path)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", type=Path, help="Path to the target repo root")
    args = parser.parse_args(argv)

    target_root = args.target.expanduser().resolve()
    source_root = Path(__file__).resolve().parent.parent

    if not target_root.is_dir():
        print(f"error: {target_root} is not a directory", file=sys.stderr)
        return 2

    version = _read_version(source_root)
    print(f"Injecting shovels-gitlint-rules@{version} into {target_root}")
    copy_rules(source_root, target_root, version)
    update_gitlint(target_root)
    update_precommit_config(target_root)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
