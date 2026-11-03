"""Command-line entry point: ``regressly run`` and ``regressly validate``."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from rich.console import Console

from regressly import __version__
from regressly.report import print_run
from regressly.runner import run_suite
from regressly.suite import SuiteError, load_suite

EXIT_OK, EXIT_FAILED, EXIT_USAGE = 0, 1, 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="regressly", description=__doc__)
    parser.add_argument("--version", action="version", version=f"regressly {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="run a test suite against its providers")
    run.add_argument("suite", type=Path)
    run.add_argument("-c", "--concurrency", type=int, default=8)
    run.add_argument("-p", "--provider", help="only run the provider with this id")
    run.add_argument("--json", type=Path, metavar="PATH", help="write results as JSON")
    run.add_argument("-v", "--verbose", action="store_true", help="show output for every test")

    validate = sub.add_parser("validate", help="check a suite without calling any model")
    validate.add_argument("suite", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    console = Console()
    err = Console(stderr=True)

    try:
        suite = load_suite(args.suite)
    except SuiteError as e:
        err.print(f"[red]error:[/] {e}")
        return EXIT_USAGE

    if args.command == "validate":
        console.print(
            f"[green]✓[/] {suite.name}: {len(suite.tests)} tests, "
            f"{len(suite.providers)} provider(s)"
        )
        return EXIT_OK

    try:
        run = asyncio.run(run_suite(suite, args.concurrency, args.provider))
    except (SuiteError, ValueError) as e:
        err.print(f"[red]error:[/] {e}")
        return EXIT_USAGE

    print_run(run, console, verbose=args.verbose)
    if args.json:
        args.json.write_text(json.dumps(run.to_dict(), indent=2, default=str))
    return EXIT_OK if run.ok else EXIT_FAILED


if __name__ == "__main__":
    sys.exit(main())
