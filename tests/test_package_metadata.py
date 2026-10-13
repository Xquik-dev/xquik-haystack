# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).parents[1]
FULL_AFFILIATION_NOTICE = (
    'Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and '
    '"X" are trademarks of X Corp.'
)
COMPACT_AFFILIATION_NOTICE = "Not affiliated with X Corp."
COPYRIGHT_NOTICE = "# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>"
# REUSE-IgnoreStart
LICENSE_NOTICE = "# SPDX-License-Identifier: Apache-2.0"
# REUSE-IgnoreEnd
SOURCE_SUFFIXES = frozenset({".py", ".sh", ".toml", ".yaml", ".yml"})
SOURCE_NAMES = frozenset({"Dockerfile"})
SOURCE_PATHS = (
    Path(".clusterfuzzlite"),
    Path(".github"),
    Path("examples"),
    Path("scripts"),
    Path("src"),
    Path("tests"),
    Path("pyproject.toml"),
)


def test_public_metadata_has_affiliation_notices() -> None:
    readme = (ROOT / "README.md").read_text()
    pyproject = (ROOT / "pyproject.toml").read_text()

    assert FULL_AFFILIATION_NOTICE in readme
    assert COMPACT_AFFILIATION_NOTICE in pyproject


def test_repository_has_no_github_actions_workflows() -> None:
    assert not (ROOT / ".github" / "workflows").exists()


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
