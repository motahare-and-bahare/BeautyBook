"""BeautyBook administrative command line.

These commands run with direct database access and are deliberately never mounted on the
HTTP application. The first administrator bootstrap command is added in F-001 Step 10.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence


def build_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser(
        prog="python -m app.cli",
        description=(
            "BeautyBook administrative tools. They require database access, are run by an "
            "operator, and are never exposed over HTTP."
        ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
