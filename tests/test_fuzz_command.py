# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
BASH = shutil.which("bash") or "/bin/bash"
# The uv stub records each call and builds a Python that answers the sanitizer
# question and records its fuzz call. The uname stub reports the system the test
# names, so no real fuzzer starts here. The ssh stub records the remote command.
STUB = r"""uv() {
 [ -z "${LD_PRELOAD:-}" ] || echo "uv ran with a preload" >> "$EVENTS"
 case "$1 $2" in
  'venv --quiet')
   mkdir -p "$5/bin"
   printf '#!/bin/sh\nif [ "$1" = -c ]; then echo "%s"; exit; fi\n' "$SANITIZER" > "$5/bin/python"
   printf 'echo "python with preload ${LD_PRELOAD:-none} $*" >> "%s"\n' "$EVENTS" >> "$5/bin/python"
   chmod +x "$5/bin/python"
   echo "venv $3 $4" >> "$EVENTS";;
  'pip install') shift 5; echo "install $*" >> "$EVENTS";;
  *) exit 99;;
 esac
}
uname() { if [ "$1" = -s ]; then echo "${SYSTEM%% *}"; else echo "${SYSTEM##* }"; fi; }
ssh() {
 cat > /dev/null
 echo "ssh $*" >> "$EVENTS"
}
export -f uv uname ssh
bash "$1"
"""
NOT_LINUX = "Use Linux x86_64 or set XQUIK_FUZZ_HOST to an authorized Linux SSH runner."
BAD_HOST = "Invalid SSH host. Set XQUIK_FUZZ_HOST to a host name or user@host."
FUZZ_OPTIONS = "-max_total_time=180 -max_len=4096 -rss_limit_mb=2048 -timeout=60 -artifact_prefix=<evidence>/"


def run_fuzz(tmp_path: Path, system: str, host: str) -> tuple[int, list[str], str]:
    events, sanitizer = tmp_path / "events", tmp_path / "sanitizer.so"
    events.touch()
    sanitizer.touch()
    result = subprocess.run(
        [BASH, "-c", STUB, "fuzz-test", str(ROOT / "scripts/fuzz")],
        env={
            **os.environ,
            "EVENTS": str(events),
            "SANITIZER": str(sanitizer),
            "SYSTEM": system,
            "TMPDIR": str(tmp_path),
            "XQUIK_FUZZ_HOST": host,
        },
        capture_output=True,
        text=True,
        check=False,
    )
    observed = [re.sub(r"[^\s=]+/tmp\.\w+", "<evidence>", event) for event in events.read_text().splitlines()]
    return result.returncode, observed, result.stderr


def test_fuzz_preloads_the_sanitizer_into_python_alone(tmp_path: Path) -> None:
    status, events, errors = run_fuzz(tmp_path, "Linux x86_64", "")
    fuzzed = (
        f"python with preload {tmp_path}/sanitizer.so .clusterfuzzlite/fuzz_response_helpers.py "
        f"<evidence>/corpus {FUZZ_OPTIONS}"
    )
    assert (status, errors) == (0, "")
    assert events == ["venv --python 3.13", "install atheris==3.1.0", fuzzed]


@pytest.mark.parametrize(
    ("system", "host", "expected"),
    [
        ("Darwin arm64", "", (1, NOT_LINUX)),
        ("Linux aarch64", "", (1, NOT_LINUX)),
        ("Darwin arm64", "-oProxyCommand=id", (2, BAD_HOST)),
        ("Darwin arm64", "runner;id", (2, BAD_HOST)),
    ],
)
def test_fuzz_refuses_before_it_starts(tmp_path: Path, system: str, host: str, expected: tuple[int, str]) -> None:
    status, events, errors = run_fuzz(tmp_path, system, host)
    assert (status, errors) == (expected[0], f"{expected[1]}\n")
    assert events == []


def test_fuzz_sends_the_source_to_the_runner(tmp_path: Path) -> None:
    status, events, errors = run_fuzz(tmp_path, "Darwin arm64", "fuzz@runner")
    assert (status, errors) == (0, "")
    assert len(events) == 1
    assert events[0].startswith("ssh -- fuzz@runner set -eu; umask 077; ")
    assert events[0].endswith("; unset XQUIK_FUZZ_HOST; bash scripts/fuzz")
