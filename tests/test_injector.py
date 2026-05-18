from pathlib import Path

from ruamel.yaml import YAML

import scripts.inject_gitlint_rules as inj


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_creates_dotgitlint_when_missing(tmp_path: Path):
    _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")

    inj.main([str(tmp_path)])

    gitlint = (tmp_path / ".gitlint").read_text()
    assert "extra-path=gitlint_rules" in gitlint
    assert (tmp_path / "gitlint_rules" / "body_no_ticket_id.py").exists()
    assert (tmp_path / "gitlint_rules" / "title_starts_capitalized.py").exists()


def test_inserts_extra_path_into_existing_general(tmp_path: Path):
    _write(
        tmp_path / ".gitlint",
        "[general]\nignore=body-is-missing\n\n[title-max-length]\nline-length=50\n",
    )
    _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")

    inj.main([str(tmp_path)])

    gitlint = (tmp_path / ".gitlint").read_text()
    assert gitlint.count("[general]") == 1
    assert "extra-path=gitlint_rules" in gitlint
    assert "ignore=body-is-missing" in gitlint  # original preserved


def test_idempotent_on_second_run(tmp_path: Path):
    _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")
    inj.main([str(tmp_path)])
    first = (tmp_path / ".gitlint").read_text()
    pre_first = (tmp_path / ".pre-commit-config.yaml").read_text()

    inj.main([str(tmp_path)])
    second = (tmp_path / ".gitlint").read_text()
    pre_second = (tmp_path / ".pre-commit-config.yaml").read_text()

    assert first == second
    assert pre_first == pre_second


def test_adds_gitlint_hook_when_missing(tmp_path: Path):
    _write(
        tmp_path / ".pre-commit-config.yaml",
        "repos:\n  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
        "    rev: v0.14.14\n    hooks:\n      - id: ruff\n",
    )

    inj.main([str(tmp_path)])

    yaml = YAML()
    config = yaml.load(tmp_path / ".pre-commit-config.yaml")
    repos = config["repos"]
    gitlint = next(r for r in repos if r["repo"] == inj.GITLINT_REPO)
    assert gitlint["rev"] == inj.GITLINT_REV
    assert gitlint["hooks"][0]["id"] == "gitlint"
    assert "commit-msg" in gitlint["hooks"][0]["stages"]


def test_preserves_existing_gitlint_hook(tmp_path: Path):
    _write(
        tmp_path / ".pre-commit-config.yaml",
        "repos:\n  - repo: https://github.com/jorisroovers/gitlint\n"
        "    rev: v0.19.1\n    hooks:\n      - id: gitlint\n"
        "        stages: [commit-msg]\n",
    )

    inj.main([str(tmp_path)])

    yaml = YAML()
    config = yaml.load(tmp_path / ".pre-commit-config.yaml")
    gitlint = next(r for r in config["repos"] if r["repo"] == inj.GITLINT_REPO)
    assert len(gitlint["hooks"]) == 1


def test_rule_files_have_autogen_header(tmp_path: Path):
    _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")
    inj.main([str(tmp_path)])

    body = (tmp_path / "gitlint_rules" / "body_no_ticket_id.py").read_text()
    assert "AUTO-GENERATED" in body
    assert "shovels-gitlint-rules@" in body
