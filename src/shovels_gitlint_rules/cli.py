"""Thin wrapper that invokes gitlint with our packaged rules pre-loaded.

gitlint discovers user-defined rules exclusively via ``--extra-path``. To avoid
forcing every target repo to vendor rule files, we ship them inside this
package and inject the path at runtime so pre-commit configs only need a single
hook reference.
"""

from __future__ import annotations

import sys
from pathlib import Path

from gitlint.cli import cli


def main() -> None:
    rules_dir = Path(__file__).resolve().parent / "rules"
    sys.argv = [sys.argv[0], "--extra-path", str(rules_dir), *sys.argv[1:]]
    cli()  # click; exits via SystemExit


if __name__ == "__main__":
    main()
