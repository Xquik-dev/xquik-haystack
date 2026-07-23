# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
FULL_AFFILIATION_NOTICE = (
    'Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and '
    '"X" are trademarks of X Corp.'
)
COMPACT_AFFILIATION_NOTICE = "Not affiliated with X Corp."
ACTION_REFERENCE = re.compile(r"[^@\s]+@[0-9a-f]{40}")
COPYRIGHT_NOTICE = "# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>"
LICENSE_NOTICE = "# SPDX-License-Identifier: Apache-2.0"
SOURCE_SUFFIXES = frozenset({".py", ".sh", ".toml", ".yaml", ".yml"})
SOURCE_NAMES = frozenset({"Dockerfile"})
SOURCE_PATHS = (
    Path(".clusterfuzzlite"),
    Path(".github"),
    Path("examples"),
    Path("src"),
    Path("tests"),
    Path("pyproject.toml"),
)


def test_public_metadata_has_affiliation_notices() -> None:
    readme = (ROOT / "README.md").read_text()
    pyproject = (ROOT / "pyproject.toml").read_text()

    assert FULL_AFFILIATION_NOTICE in readme
    assert COMPACT_AFFILIATION_NOTICE in pyproject


def test_workflow_actions_are_pinned_to_commit_shas() -> None:
    for workflow_path in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        action_lines = [
            line.strip() for line in workflow_path.read_text().splitlines() if line.strip().startswith("uses:")
        ]
        assert action_lines
        for action_line in action_lines:
            action = action_line.removeprefix("uses:").partition("#")[0].strip()
            assert ACTION_REFERENCE.fullmatch(action), f"Unpinned action in {workflow_path}: {action}"


def test_source_files_have_copyright_and_license_notices() -> None:
    candidates = (
        path
        for source_path in SOURCE_PATHS
        for path in ([ROOT / source_path] if (ROOT / source_path).is_file() else (ROOT / source_path).rglob("*"))
    )
    source_files = [
        path for path in candidates if path.is_file() and (path.suffix in SOURCE_SUFFIXES or path.name in SOURCE_NAMES)
    ]
    missing_notices = []
    for path in source_files:
        header = path.read_text(encoding="utf-8").splitlines()[:6]
        if COPYRIGHT_NOTICE not in header or LICENSE_NOTICE not in header:
            missing_notices.append(path.relative_to(ROOT))

    assert source_files
    assert missing_notices == []


def test_release_workflow_requires_exact_release_tag_on_main() -> None:
    workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text()

    assert "workflow_dispatch" not in workflow
    assert "ref: ${{ github.event.release.tag_name }}" in workflow
    assert "refs/tags/${RELEASE_TAG}^{commit}" in workflow
    assert "refs/remotes/origin/main" in workflow
    assert "default branch tip" in workflow
    assert workflow.count("id-token: write") == 1
    assert "attestations: true" in workflow
