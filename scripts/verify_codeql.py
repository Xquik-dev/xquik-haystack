# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypeAlias

JsonValue: TypeAlias = str | int | float | bool | list["JsonValue"] | dict[str, "JsonValue"] | None

EXTRACTED_FILES = "py/diagnostics/successfully-extracted-files"
HARMLESS_LEVELS = ("none", "note")

_decode_json: Callable[[str], JsonValue] = json.loads


def _items(value: JsonValue, name: str) -> list[dict[str, JsonValue]]:
    if isinstance(value, list):
        items = [item for item in value if isinstance(item, dict)]
        if items and len(items) == len(value):
            return items
    message = f"CodeQL report lacks {name}."
    raise ValueError(message)


def _field(value: JsonValue, key: str, default: JsonValue) -> JsonValue:
    return value.get(key, default) if isinstance(value, dict) else default


def _describe(finding: JsonValue) -> str:
    locations = _field(finding, "locations", None)
    first = locations[0] if isinstance(locations, list) and locations else {}
    location = _field(first, "physicalLocation", {})
    file = _field(_field(location, "artifactLocation", {}), "uri", "unknown file")
    line = _field(_field(location, "region", {}), "startLine", 0)
    text = _field(_field(finding, "message", {}), "text", "")
    return f"{_field(finding, 'ruleId', None)} {file}:{line} {text}".strip()


def validate(report: JsonValue) -> str:
    """Return a summary of a clean report, or raise with the reason it is not clean."""
    runs = _items(report.get("runs") if isinstance(report, dict) else None, "runs")
    if not isinstance(report, dict) or report.get("version") != "2.1.0" or len(runs) != 1:
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
            extracted += _field(notification.get("descriptor") or {}, "id", None) == EXTRACTED_FILES
    if not extracted:
        message = "CodeQL did not confirm extracted Python files."
        raise ValueError(message)
    return f"CodeQL finished with no findings. Extracted Python entries {extracted}."


if __name__ == "__main__":
    try:
        sys.stdout.write(validate(_decode_json(Path(sys.argv[1]).read_text())) + "\n")
    except ValueError as error:
        sys.exit(str(error))
