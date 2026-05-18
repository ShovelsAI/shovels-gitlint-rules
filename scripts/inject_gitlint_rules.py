"""Inject the shovels-gitlint pre-commit hook into a target repo.

Idempotent. Run from the shovels-gitlint-rules repo root:

    uv run python scripts/inject_gitlint_rules.py /path/to/target-repo

Edits `.pre-commit-config.yaml` in the target so the standard ``jorisroovers/gitlint``
hook is replaced by ``ShovelsAI/shovels-gitlint-rules`` (which runs gitlint with
our custom rules pre-loaded via ``--extra-path``). The hook reads ``.gitlint``
for built-in rules; no other config changes needed.

Also cleans up artifacts from the older vendored approach (``gitlint_rules/``
directory and ``extra-path=`` line in ``.gitlint``).
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

OLD_GITLINT_REPO = "https://github.com/jorisroovers/gitlint"
SHOVELS_REPO = "git@github.com:ShovelsAI/shovels-gitlint-rules.git"


def _read_version(repo_root: Path) -> str:
    pyproject = (repo_root / "pyproject.toml").read_text()
    for line in pyproject.splitlines():
        if line.startswith("version"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("Could not find version in pyproject.toml")


def _flow_seq(items: list[str]) -> CommentedSeq:
    seq = CommentedSeq(items)
    seq.fa.set_flow_style()
    return seq


def _new_gitlint_entry(version: str) -> CommentedMap:
    hook = CommentedMap()
    hook["id"] = "shovels-gitlint"
    hook["stages"] = _flow_seq(["commit-msg"])
    entry = CommentedMap()
    entry["repo"] = SHOVELS_REPO
    entry["rev"] = f"v{version}"
    entry["hooks"] = [hook]
    return entry


def update_precommit_config(target_root: Path, version: str) -> None:
    path = target_root / ".pre-commit-config.yaml"
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; cannot inject hook")

    config = yaml.load(path)
    repos = config.setdefault("repos", CommentedSeq())

    shovels_idx = next(
        (i for i, r in enumerate(repos) if isinstance(r, dict) and r.get("repo") == SHOVELS_REPO),
        None,
    )
    if shovels_idx is not None:
        entry = repos[shovels_idx]
        if entry.get("rev") != f"v{version}":
            entry["rev"] = f"v{version}"
            print(f"  bumped {SHOVELS_REPO} to v{version}")
        else:
            print(f"  {SHOVELS_REPO}@v{version} already present; leaving as-is")
    else:
        old_idx = next(
            (
                i
                for i, r in enumerate(repos)
                if isinstance(r, dict) and r.get("repo") == OLD_GITLINT_REPO
            ),
            None,
        )
        new_entry = _new_gitlint_entry(version)
        if old_idx is not None:
            repos[old_idx] = new_entry
            print(f"  replaced {OLD_GITLINT_REPO} with {SHOVELS_REPO}@v{version}")
        else:
            repos.append(new_entry)
            print(f"  added {SHOVELS_REPO}@v{version}")

    yaml.dump(config, path)


def cleanup_legacy_artifacts(target_root: Path) -> None:
    legacy_dir = target_root / "gitlint_rules"
    if legacy_dir.is_dir():
        shutil.rmtree(legacy_dir)
        print(f"  removed legacy {legacy_dir.relative_to(target_root)}/")

    gitlint_cfg = target_root / ".gitlint"
    if gitlint_cfg.exists():
        original = gitlint_cfg.read_text()
        kept = [
            line for line in original.splitlines() if not line.strip().startswith("extra-path=")
        ]
        cleaned = "\n".join(kept) + ("\n" if original.endswith("\n") else "")
        if cleaned != original:
            gitlint_cfg.write_text(cleaned)
            print(f"  removed extra-path line from .gitlint")


def ensure_default_gitlint(target_root: Path) -> None:
    path = target_root / ".gitlint"
    if path.exists() and path.read_text().strip():
        return
    path.write_text(
        "[general]\n"
        "ignore=body-is-missing\n"
        "\n"
        "[title-max-length]\n"
        "line-length=50\n"
        "\n"
        "[body-max-line-length]\n"
        "line-length=72\n"
    )
    print(f"  created default .gitlint")


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
    print(f"Injecting shovels-gitlint-rules@v{version} into {target_root}")
    cleanup_legacy_artifacts(target_root)
    ensure_default_gitlint(target_root)
    update_precommit_config(target_root, version)
    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
