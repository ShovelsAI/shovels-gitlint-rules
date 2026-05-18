from pathlib import Path

from ruamel.yaml import YAML

import scripts.inject_gitlint_rules as inj


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _load_repos(target: Path) -> list:
    yaml = YAML()
    return yaml.load(target / ".pre-commit-config.yaml")["repos"]


def test_replaces_old_gitlint_entry(tmp_path: Path):
    _write(
        tmp_path / ".pre-commit-config.yaml",
        "repos:\n"
        "  - repo: https://github.com/jorisroovers/gitlint\n"
        "    rev: v0.19.1\n"
        "    hooks:\n"
        "      - id: gitlint\n"
        "        stages: [commit-msg]\n",
    )

    inj.main([str(tmp_path)])

    repos = _load_repos(tmp_path)
    assert len(repos) == 1
    assert repos[0]["repo"] == inj.SHOVELS_REPO
    assert repos[0]["hooks"][0]["id"] == "shovels-gitlint"
    assert "commit-msg" in repos[0]["hooks"][0]["stages"]


def test_adds_new_entry_when_no_gitlint_present(tmp_path: Path):
    _write(
        tmp_path / ".pre-commit-config.yaml",
        "repos:\n"
        "  - repo: https://github.com/astral-sh/ruff-pre-commit\n"
        "    rev: v0.14.14\n"
        "    hooks:\n"
        "      - id: ruff\n",
    )

    inj.main([str(tmp_path)])

    repos = _load_repos(tmp_path)
    assert len(repos) == 2
    assert repos[-1]["repo"] == inj.SHOVELS_REPO


def test_idempotent_on_second_run(tmp_path: Path):
    _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")
    inj.main([str(tmp_path)])
    first = (tmp_path / ".pre-commit-config.yaml").read_text()
    inj.main([str(tmp_path)])
    second = (tmp_path / ".pre-commit-config.yaml").read_text()
    assert first == second


def test_bumps_rev_when_version_changes(tmp_path: Path):
    _write(
        tmp_path / ".pre-commit-config.yaml",
        f"repos:\n"
        f"  - repo: {inj.SHOVELS_REPO}\n"
        f"    rev: v0.0.1\n"
        f"    hooks:\n"
        f"      - id: shovels-gitlint\n"
        f"        stages: [commit-msg]\n",
    )

    inj.main([str(tmp_path)])

    repos = _load_repos(tmp_path)
    assert repos[0]["rev"] != "v0.0.1"
    assert repos[0]["rev"].startswith("v")


def test_cleans_legacy_vendored_dir(tmp_path: Path):
    _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")
    legacy = tmp_path / "gitlint_rules"
    legacy.mkdir()
    (legacy / "body_no_ticket_id.py").write_text("# old vendored file\n")

    inj.main([str(tmp_path)])

    assert not legacy.exists()


def test_strips_extra_path_from_gitlint(tmp_path: Path):
    _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")
    _write(
        tmp_path / ".gitlint",
        "[general]\nextra-path=gitlint_rules\nignore=body-is-missing\n",
    )

    inj.main([str(tmp_path)])

    gitlint = (tmp_path / ".gitlint").read_text()
    assert "extra-path" not in gitlint
    assert "ignore=body-is-missing" in gitlint


def test_creates_default_gitlint_when_missing(tmp_path: Path):
    _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")
    inj.main([str(tmp_path)])
    assert (tmp_path / ".gitlint").exists()
    assert "[title-max-length]" in (tmp_path / ".gitlint").read_text()


def test_preserves_existing_populated_gitlint(tmp_path: Path):
    _write(tmp_path / ".pre-commit-config.yaml", "repos: []\n")
    original = "[general]\nignore=body-is-missing\n\n[title-max-length]\nline-length=42\n"
    _write(tmp_path / ".gitlint", original)
    inj.main([str(tmp_path)])
    assert (tmp_path / ".gitlint").read_text() == original
