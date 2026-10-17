#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
umask 077
mkdir -p config
if [[ ! -f config/caption.env ]]; then
  python3 - <<'PY'
from pathlib import Path
import secrets
p = Path('config/caption.env')
with p.open('x') as f:
    f.write('CAPTION_API_KEY=' + secrets.token_hex(32) + '\n')
    f.write('CAPTION_HOST=127.0.0.1\nCAPTION_PORT=8010\nOLLAMA_URL=http://127.0.0.1:11434\n')
p.chmod(0o600)
PY
fi
set -a
source config/caption.env
set +a
if [[ ! -x .venv/bin/python ]]; then python3 -m venv .venv; fi
hash="$(sha256sum requirements.txt | cut -d ' ' -f1)"
if [[ ! -f .venv/requirements.sha256 ]] || [[ "$(cat .venv/requirements.sha256)" != "$hash" ]]; then
  .venv/bin/python -m pip install -r requirements.txt
  .venv/bin/python -m pip check
  printf '%s' "$hash" > .venv/requirements.sha256
fi
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
exec .venv/bin/python -m snuwcaption
