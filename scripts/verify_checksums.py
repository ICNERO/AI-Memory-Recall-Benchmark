"""Check the published file inventory before generating local outputs."""
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
errors = []
count = 0
for line in (ROOT / 'SHA256SUMS.txt').read_text(encoding='utf-8').splitlines():
    digest, name = line.split(maxsplit=1)
    path = ROOT / name.lstrip('*')
    count += 1
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
        errors.append(name)
print(f'Checked {count} files; mismatches: {errors}')
raise SystemExit(bool(errors))

