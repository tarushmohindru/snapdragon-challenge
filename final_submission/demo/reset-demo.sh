#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
PY=.venv-cliptrail/bin/python
if [[ ! -x "$PY" ]]; then
  echo 'Missing .venv-cliptrail. Run bash experiments/cliptrail/provision_reference.sh first.' >&2
  exit 1
fi
"$PY" experiments/cliptrail_app/prepare_validation_library.py
DB=.cliptrail/demo.sqlite3
mkdir -p .cliptrail
# Delete only the separate, reproducible demo index. Frozen evidence is untouched.
rm -f "$DB" "$DB-wal" "$DB-shm"
"$PY" -m cliptrail_app --db "$DB" index experiments/cliptrail_app/validation_library
echo "Prepared persisted demo index: $DB"
