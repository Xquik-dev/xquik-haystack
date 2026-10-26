# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from typing import NoReturn

Setup: Callable[[Sequence[str], Callable[[bytes], None]], list[str]]
Fuzz: Callable[[], NoReturn]

def instrument_imports() -> AbstractContextManager[object]: ...
