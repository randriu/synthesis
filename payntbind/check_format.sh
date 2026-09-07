#!/usr/bin/env bash
# Reports which payntbind C++ sources are not clang-formatted, without changing anything.
#
# This is a starter check: nothing under payntbind/src/ has ever been reformatted against
# payntbind/.clang-format, so a first run is expected to flag most files. That cleanup is its own
# separately-scheduled PR, not something this script does on its own.
#
# Usage: payntbind/check_format.sh          (report only, exit 0 even if files would change)
#        payntbind/check_format.sh --strict (exit 1 if any file would change -- for CI)

set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"

if ! command -v clang-format &> /dev/null; then
    echo "clang-format not found on PATH" >&2
    exit 2
fi

# payntbind/src/synthesis/decpomdp/madp/ is the vendored MADP Toolbox (upstream GPL code with its own
# formatting) -- excluded, since payntbind/.clang-format only applies to payntbind's own sources.
mapfile -t files < <(find src -type f \( -name '*.cpp' -o -name '*.h' \) -not -path 'src/synthesis/decpomdp/madp/*' | sort)

violations=()
for f in "${files[@]}"; do
    if ! clang-format --style=file:.clang-format --dry-run --Werror "$f" &> /dev/null; then
        violations+=("$f")
    fi
done

total=${#files[@]}
bad=${#violations[@]}
echo "checked $total files, $bad would be reformatted"
if [ "$bad" -gt 0 ]; then
    printf '  %s\n' "${violations[@]}"
fi

if [ "${1:-}" = "--strict" ] && [ "$bad" -gt 0 ]; then
    exit 1
fi
