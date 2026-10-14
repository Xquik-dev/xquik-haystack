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
STUB = r"""record() { printf '%s\n' "$1" >> "$RELEASE_EVENTS"; }
git() {
 case "$1" in
  remote) echo git@github.com:Xquik-dev/xquik-haystack.git;;
  status) [ "$RELEASE_CASE" != dirty ] || echo ' M README.md';;
  symbolic-ref) if [ "$RELEASE_CASE" = branch ]; then echo topic; else echo main; fi;;
  fetch) :;;
  rev-parse)
   case "$*" in
    *refs/tags/*) return 1;;
    *origin/main*) if [ "$RELEASE_CASE" = behind ]; then echo def; else echo abc; fi;;
    *) echo abc;;
   esac;;
  ls-remote) [ "$RELEASE_CASE" = tagged ] || return 2;;
  tag) record "tag $3 $6";;
  push) record "push $3";;
  *) exit 99;;
 esac
}
uv() {
 case "$1 $2 $3 $4 $5 $6" in
  'tool run --from hatch==1.18.0 hatch build')
   record "build $SETUPTOOLS_SCM_PRETEND_VERSION"
   mkdir -p "$7"
   for suffix in -py3-none-any.whl .tar.gz; do echo fixture > "$7/xquik_haystack-1.2.3$suffix"; done;;
  'tool run --from twine==7.0.0 twine check') record metadata;;
  publish*)
   [ "$UV_PUBLISH_TOKEN" = isolated-fixture-token ] && [ "$#" = 7 ] || exit 99
   [ "$2 $3 $4 $5" = '--publish-url https://upload.pypi.org/legacy/ --check-url https://pypi.org/simple/' ] || exit 99
   record publish;;
  *) exit 99;;
 esac
}
gh() {
 case "$1 $2" in
  'auth status') :;;
  'release create')
   [ "$*" = "release create v1.2.3 --repo $REPOSITORY --verify-tag --title v1.2.3 --generate-notes" ] || exit 99
   record "release $3";;
  *) exit 99;;
 esac
}
curl() {
 case "$*" in
  *--write-out*) printf '%s' "$RELEASE_PYPI";;
  *)
   record verify
   digest=$(echo "$RELEASE_UPLOADED" | shasum -a 256 | cut -d ' ' -f 1)
   echo "{\"sha256\":\"$digest\"}";;
 esac
 while [ "$#" -gt 1 ]; do shift; done
 [ "$1" = https://pypi.org/pypi/xquik-haystack/1.2.3/json ] || exit 99
}
security() {
 [ -n "${PYPI_KEYCHAIN_SERVICE:-}" ] && [ "$1 $2 $3" = "find-generic-password -s $PYPI_KEYCHAIN_SERVICE" ] || exit 99
 [ "$RELEASE_CASE" != keychain ] || return 44
 [ "${4:-}" != -w ] || echo isolated-fixture-token
}
sleep() { record "sleep $1"; }
export -f record git uv gh curl security sleep
runner=$1; shift
bash "$runner" "$@"
"""
CHECKED = ["checks", "build 1.2.3", "metadata"]
RELEASED = ["tag v1.2.3 abc", "push refs/tags/v1.2.3", "release v1.2.3"]
NO_KEYCHAIN_ITEM = (
    "release-local: The Keychain has no item named by PYPI_KEYCHAIN_SERVICE. "
    "Add the PyPI token under that name, then run bin/release-local again."
)
DRY_RUN_END = "Dry run finished for xquik-haystack 1.2.3. Nothing was uploaded, tagged, or released."


def run_release(
    tmp_path: Path,
    arguments: list[str],
    case: str,
    pypi: str,
    *,
    service: str | None = "test-publisher",
    uploaded: str = "fixture",
) -> tuple[int, list[str], str]:
    project = tmp_path / "project"
    (project / "bin").mkdir(parents=True)
    runner = project / "bin/release-local"
    runner.write_bytes((ROOT / "bin/release-local").read_bytes())
    checks = project / "bin/check-local"
    checks.write_text("#!/usr/bin/env bash\nprintf 'checks\\n' >> \"$RELEASE_EVENTS\"\n")
    checks.chmod(0o755)
    events = tmp_path / "events"
    events.touch()
    environment = {key: value for key, value in os.environ.items() if key != "PYPI_KEYCHAIN_SERVICE"}
    environment.update(
        RELEASE_CASE=case,
        RELEASE_PYPI=pypi,
        RELEASE_EVENTS=str(events),
        RELEASE_UPLOADED=uploaded,
        RELEASE_RETRY_SECONDS="0",
        REPOSITORY="Xquik-dev/xquik-haystack",
    )
    if service is not None:
        environment["PYPI_KEYCHAIN_SERVICE"] = service
    result = subprocess.run(
        [BASH, "-c", STUB, "release-local-test", str(runner), *arguments],
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert "isolated-fixture-token" not in result.stdout + result.stderr
    assert "test-publisher" not in result.stdout + result.stderr
    return result.returncode, events.read_text().splitlines(), result.stdout + result.stderr


@pytest.mark.parametrize(
    ("pypi", "events"),
    [("404", [*CHECKED, "publish", "verify", *RELEASED]), ("200", [*CHECKED, "verify", *RELEASED])],
)
def test_release_uploads_once_then_tags_and_releases(tmp_path: Path, pypi: str, events: list[str]) -> None:
    status, observed, output = run_release(tmp_path, ["1.2.3"], "ready", pypi)
    assert status == 0, output
    assert observed == events
    assert output.splitlines()[-1] == "Released xquik-haystack 1.2.3 as v1.2.3."


@pytest.mark.parametrize(
    ("case", "pypi", "events"),
    [("ready", "404", CHECKED), ("ready", "200", [*CHECKED, "verify"]), ("branch", "404", CHECKED)],
)
def test_dry_run_needs_no_token_and_releases_nothing(tmp_path: Path, case: str, pypi: str, events: list[str]) -> None:
    status, observed, output = run_release(tmp_path, ["--dry-run", "1.2.3"], case, pypi, service=None)
    assert status == 0, output
    assert observed == events
    assert output.splitlines()[-1] == DRY_RUN_END


def test_release_never_tags_files_that_differ_from_pypi(tmp_path: Path) -> None:
    status, observed, output = run_release(tmp_path, ["1.2.3"], "ready", "200", uploaded="other")
    assert status == 1
    assert observed == [*CHECKED, *["verify", "sleep 0"] * 4, "verify"]
    assert output.splitlines()[-1] == (
        "release-local: PyPI files differ from this build or are not visible yet. Compare them before tagging."
    )


@pytest.mark.parametrize(
    ("arguments", "case", "pypi", "expected"),
    [
        (["1.2.3"], "dirty", "404", (1, "release-local: Commit or remove local changes, then rerun.")),
        (["--dry-run", "1.2.3"], "dirty", "404", (1, "release-local: Commit or remove local changes, then rerun.")),
        (["1.2.3"], "branch", "404", (1, "release-local: Switch to main, then rerun.")),
        (["1.2.3"], "behind", "404", (1, "release-local: Make main equal to origin/main, then rerun.")),
        (
            ["1.2.3"],
            "tagged",
            "404",
            (1, "release-local: Tag v1.2.3 already exists on origin. Pass the next version, then rerun."),
        ),
        (
            ["1.2.3"],
            "keychain",
            "404",
            (1, NO_KEYCHAIN_ITEM),
        ),
        (["1.2.3"], "ready", "503", (1, "release-local: PyPI returned HTTP 503. Retry later.")),
        (
            ["--publish", "1.2.3"],
            "ready",
            "404",
            (2, "release-local: unknown option --publish. Use --dry-run and a version such as 1.2.3."),
        ),
        ([], "ready", "404", (2, "release-local: pass the version to release, such as 1.2.3.")),
        (["v1.2.3"], "ready", "404", (2, "release-local: pass the version to release, such as 1.2.3.")),
        (["1.2.3", "1.2.4"], "ready", "404", (2, "release-local: pass 1 version, such as 1.2.3.")),
    ],
)
def test_release_refuses_before_any_upload(
    tmp_path: Path, arguments: list[str], case: str, pypi: str, expected: tuple[int, str]
) -> None:
    status, observed, output = run_release(tmp_path, arguments, case, pypi)
    assert (status, output.splitlines()[-1]) == expected
    assert not {"publish", "verify", *RELEASED} & set(observed)


@pytest.mark.parametrize("service", [None, ""])
def test_release_stops_when_the_token_item_is_not_named(tmp_path: Path, service: str | None) -> None:
    status, observed, output = run_release(tmp_path, ["1.2.3"], "ready", "404", service=service)
    assert status == 1
    assert output.splitlines()[-1] == (
        "release-local: PYPI_KEYCHAIN_SERVICE is unset. "
        "Set it to the Keychain item that holds the PyPI token, then run bin/release-local again."
    )
    assert observed == []
