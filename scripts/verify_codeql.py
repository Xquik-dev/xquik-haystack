# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

EXTRACTED_FILES = "py/diagnostics/successfully-extracted-files"
HARMLESS_LEVELS = ("none", "note")


def _items(value: Any, name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value or not all(isinstance(item, dict) for item in value):
        message = f"CodeQL report lacks {name}."
        raise ValueError(message)
    return value


def _describe(finding: dict[str, Any]) -> str:
    location = (finding.get("locations") or [{}])[0].get("physicalLocation", {})
    file = location.get("artifactLocation", {}).get("uri", "unknown file")
    line = location.get("region", {}).get("startLine", 0)
    return f"{finding.get('ruleId')} {file}:{line} {finding.get('message', {}).get('text', '')}".strip()


def validate(report: Any) -> str:
    """Return a summary of a clean report, or raise with the reason it is not clean."""
    runs = _items(report.get("runs") if isinstance(report, dict) else None, "runs")
    if report.get("version") != "2.1.0" or len(runs) != 1:
        message = "Expected 1 SARIF 2.1.0 run."
        raise ValueError(message)
    findings = runs[0].get("results")
    if not isinstance(findings, list):
        message = "CodeQL report lacks results."
        raise ValueError(message)
    if findings:
        places = "\n".join(_describe(finding) for finding in findings)
        message = f"{places}\nCodeQL found {len(findings)} finding(s). Fix each one."
        raise ValueError(message)
    extracted = 0
    for invocation in _items(runs[0].get("invocations"), "invocations"):
        if invocation.get("executionSuccessful") is not True:
            message = "CodeQL invocation failed."
            raise ValueError(message)
        for notification in _items(invocation.get("toolExecutionNotifications"), "diagnostics"):
            if notification.get("level") not in HARMLESS_LEVELS:
                message = "CodeQL diagnostic needs review."
                raise ValueError(message)
            extracted += (notification.get("descriptor") or {}).get("id") == EXTRACTED_FILES
    if not extracted:
        message = "CodeQL did not confirm extracted Python files."
        raise ValueError(message)
    return f"CodeQL finished with no findings. Extracted Python entries {extracted}."


if __name__ == "__main__":
    try:
        sys.stdout.write(validate(json.loads(Path(sys.argv[1]).read_text())) + "\n")
    except ValueError as error:
        sys.exit(str(error))
