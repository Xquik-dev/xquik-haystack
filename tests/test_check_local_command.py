# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
BASH = shutil.which("bash") or "/bin/bash"
GIT = shutil.which("git") or "/usr/bin/git"
CODEQL = r"""#!/usr/bin/env bash
if [ "${1:-}" = --version ]; then [ "$CHECK_CASE" != no-codeql ] || exit 1; echo 2.27.2; exit; fi
printf 'codeql\n' >> "$CHECK_EVENTS"
[ "$CHECK_CASE" != changed ] || touch "$CHECK_DIRTY"
[ "$CHECK_CASE" != codeql ]
"""
STUB = r"""record() { printf '%s\n' "$1" >> "$CHECK_EVENTS"; [ "$CHECK_CASE" != "$1" ]; }
git() {
 case "$1 $2" in
  'rev-parse HEAD') echo abc123;;
  'status --porcelain') if [ "$CHECK_CASE" = dirty ] || [ -e "$CHECK_DIRTY" ]; then echo ' M README.md'; fi;;
  'grep -nP')
   printf 'ignores\n' >> "$CHECK_EVENTS"
   command git "$@";;
  *) exit 99;;
 esac
}
gh() {
 [ "$1 $2" = 'api --silent' ] || exit 99
 case "$3" in
  repos/Xquik-dev/xquik-haystack/commits/abc123) [ "$CHECK_CASE" != unpushed ];;
  repos/Xquik-dev/xquik-haystack/statuses/abc123)
   [ "$4 $6 $7 $8" = '-f -f context=xquik-local-checks -f' ] && [ "$#" = 9 ] || exit 99
   printf '%s: %s\n' "${5#state=}" "${9#description=}" >> "$CHECK_STATUSES";;
  *) exit 99;;
 esac
}
uv() {
 case "$1 $2" in
  'python find') echo "/python/$3";;
  'tool run')
   case "$4 $5 $6" in
    'hatch==1.18.0 hatch run')
     [ "$HATCH_DATA_DIR" != "${HATCH_DATA_DIR%/hatch-${HATCH_PYTHON#/python/}}" ] || exit 99
     [ "$7" != test:all ] || echo "===== 25 passed in 1.00s ====="
     if [ "$7" = test:types ]; then
      [ "$8" = --any-exprs-report ] || exit 99
      mkdir -p "$9"
      if [ "$CHECK_CASE" = any-exprs ]; then anys=1; else anys=0; fi
      printf 'Total %s 10 90.00%%\n' "$anys" > "$9/any-exprs.txt"
     fi
     record "$7 on $HATCH_PYTHON";;
    'reuse==6.2.0 reuse lint') record reuse;;
    *) exit 99;;
   esac;;
  *) exit 99;;
 esac
}
export -f record git gh uv
runner=$1; shift
bash "$runner" "$@"
"""
CHECKS = [
    "fmt-check on /python/3.10",
    "ignores",
    "test:types on /python/3.10",
    "test:types on /python/3.14",
    "reuse",
    "test:all on /python/3.10",
    "test:all on /python/3.14",
    "codeql",
]
PENDING = "pending: Running lint, types, licensing, tests & CodeQL."
PASSED = "lint, types, REUSE, tests (50 passed in 2 runs), CodeQL 2.27.2."


def run_checks(
    tmp_path: Path, case: str, *arguments: str, source: str = ""
) -> tuple[int, list[str], list[str], list[str]]:
    project = tmp_path / "project"
    for folder in ("bin", "scripts"):
        (project / folder).mkdir(parents=True)
    subprocess.run([GIT, "init", "-q", str(project)], check=True)
    if source:
        (project / "probe.py").write_text(source)
    runner = project / "bin/check-local"
    runner.write_bytes((ROOT / "bin/check-local").read_bytes())
    (project / "scripts/codeql-security").write_text(CODEQL)
    events, statuses = tmp_path / "events", tmp_path / "statuses"
    events.touch()
    statuses.touch()
    result = subprocess.run(
        [BASH, "-c", STUB, "check-local-test", str(runner), *arguments],
        env={
            **os.environ,
            "CHECK_CASE": case,
            "CHECK_EVENTS": str(events),
            "CHECK_STATUSES": str(statuses),
            "CHECK_DIRTY": str(tmp_path / "dirty"),
        },
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout + result.stderr).splitlines()
    return result.returncode, events.read_text().splitlines(), statuses.read_text().splitlines(), output


def test_success_status_lists_the_checks_that_passed(tmp_path: Path) -> None:
    status, events, statuses, output = run_checks(tmp_path, "ready")
    assert status == 0, output
    assert events == CHECKS
    assert statuses == [PENDING, f"success: Passed {PASSED}"]
    assert output[-1] == f"All local checks passed. They were {PASSED}"


@pytest.mark.parametrize(
    "comment",
    ["type: ignore[assignment]", "pyright: ignore[reportAssignmentType]", "mypy: ignore-errors", "pyright: basic"],
)
def test_type_checker_comments_fail_the_build(tmp_path: Path, comment: str) -> None:
    line = f'x: int = "a"  # {comment}'
    status, events, statuses, output = run_checks(tmp_path, "ready", source=f"{line}\n")
    assert status == 1
    assert events == CHECKS[:2]
    assert statuses == [PENDING, "failure: Failed at Type checker comments."]
    assert f"probe.py:1:{line}" in output


@pytest.mark.parametrize(
    ("case", "ran", "failed"),
    [
        ("fmt-check on /python/3.10", CHECKS[:1], "Lint with Ruff on Python 3.10"),
        ("test:types on /python/3.10", CHECKS[:3], "Type check with mypy on Python 3.10"),
        ("any-exprs", CHECKS[:3], "Type check with mypy on Python 3.10"),
        ("test:types on /python/3.14", CHECKS[:4], "Type check with mypy on Python 3.14"),
        ("reuse", CHECKS[:5], "Licensing with REUSE lint"),
        ("test:all on /python/3.10", CHECKS[:6], "Tests on Python 3.10"),
        ("test:all on /python/3.14", CHECKS[:7], "Tests on Python 3.14"),
        ("codeql", CHECKS, "Static analysis with CodeQL 2.27.2 security-extended queries"),
        ("changed", CHECKS, "Final tree check"),
    ],
)
def test_failed_check_posts_failure_and_stops(tmp_path: Path, case: str, ran: list[str], failed: str) -> None:
    status, events, statuses, _ = run_checks(tmp_path, case)
    assert status != 0
    assert events == ran
    assert statuses == [PENDING, f"failure: Failed at {failed}."]


def test_unusable_codeql_fails_before_any_check(tmp_path: Path) -> None:
    status, events, statuses, _ = run_checks(tmp_path, "no-codeql")
    assert status == 1
    assert events == []
    assert statuses == [PENDING, "failure: Failed at CodeQL CLI."]


@pytest.mark.parametrize(
    ("case", "arguments", "reason"),
    [
        ("ready", ["--no-status"], "--no-status was passed."),
        ("dirty", [], "the tree has uncommitted changes."),
        ("unpushed", [], "GitHub does not have HEAD, or gh is signed out. Push first."),
    ],
)
def test_status_is_posted_only_for_a_clean_pushed_commit(
    tmp_path: Path, case: str, arguments: list[str], reason: str
) -> None:
    status, events, statuses, output = run_checks(tmp_path, case, *arguments)
    assert status == 0, output
    assert events == CHECKS
    assert statuses == []
    assert output[0] == f"==> Commit status not posted because {reason}"


def test_unknown_option_stops_before_any_check(tmp_path: Path) -> None:
    status, events, statuses, output = run_checks(tmp_path, "ready", "--skip")
    assert status == 2
    assert events == []
    assert statuses == []
    assert output == ["check-local: unknown option --skip. Use --no-status or no option."]
