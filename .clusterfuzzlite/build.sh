#!/bin/bash -eu
# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
#
# SPDX-License-Identifier: Apache-2.0


export PYTHONPATH="$SRC/xquik-haystack/src"

compile_python_fuzzer \
  "$SRC/xquik-haystack/.clusterfuzzlite/fuzz_response_helpers.py" \
  --hidden-import atheris \
  --paths "$SRC/xquik-haystack/src" \
  --exclude-module haystack \
  --exclude-module pydantic

cat > "$OUT/fuzz_response_helpers.options" <<'EOF'
[libfuzzer]
max_len = 4096
EOF
