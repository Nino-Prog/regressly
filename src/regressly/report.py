"""Terminal output for a run."""

from __future__ import annotations

from itertools import groupby

from rich.console import Console
from rich.markup import escape

from regressly.runner import RunResult, Status

_ICON = {
    Status.PASSED: "[green]✓[/]",
    Status.FAILED: "[red]✗[/]",
    Status.ERROR: "[yellow]![/]",
}


def _duration(ms: float) -> str:
    return f"{ms:.0f} ms" if ms < 1000 else f"{ms / 1000:.1f} s"


def print_run(run: RunResult, console: Console | None = None, verbose: bool = False) -> None:
    console = console or Console()
    for provider, results in groupby(run.results, key=lambda r: r.provider):
        console.print(f"\n [bold]{run.suite}[/] · [cyan]{provider}[/]")
        for r in results:
            console.print(f" {_ICON[r.status]} {escape(r.test)}  [dim]{_duration(r.latency_ms)}[/]")
            if r.status is Status.ERROR:
                console.print(f"     [yellow]{escape(str(r.error))}[/]")
            for a in r.assertions:
                if not a.passed:
                    console.print(f"     [red]{a.type}[/]: {escape(a.message)}", highlight=False)
            if r.output and (verbose or r.status is Status.FAILED):
                preview = escape(repr(r.output.strip()[:300]))
                console.print(f"     [dim]output: {preview}[/]", highlight=False)

    parts = [f"[green]{run.count(Status.PASSED)} passed[/]"]
    if failed := run.count(Status.FAILED):
        parts.append(f"[red]{failed} failed[/]")
    if errors := run.count(Status.ERROR):
        parts.append(f"[yellow]{errors} errored[/]")
    console.print(f" {' · '.join(parts)} · {_duration(run.duration_ms)}\n")
