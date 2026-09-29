#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
PY=.venv-cliptrail/bin/python
if [[ ! -x "$PY" ]]; then
  echo 'Missing .venv-cliptrail. Run bash experiments/cliptrail/provision_reference.sh first.' >&2
  exit 1
fi
SAVED=experiments/cliptrail_app/results/persistent-demo/index.sqlite3
LOCAL=.cliptrail/demo.sqlite3
if [[ -n "${CLIPTRAIL_DEMO_DB:-}" ]]; then
  DB=$CLIPTRAIL_DEMO_DB
elif [[ -f "$SAVED" && -f experiments/cliptrail_app/validation_library/sintel_trailer-480p.mp4 ]]; then
  DB=$SAVED
else
  DB=$LOCAL
fi
if [[ ! -f "$DB" ]]; then
  echo "No demo index at $DB. Run bash final_submission/demo/reset-demo.sh first." >&2
  exit 1
fi
echo "Using persisted local index: $DB"
exec "$PY" -m cliptrail_app --db "$DB" serve --backend cpu
