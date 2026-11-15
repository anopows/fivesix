"""Keep the release manifest accurate as tracked files change."""
import hashlib
import json
from pathlib import Path
import subprocess


def test_release_manifest_covers_and_hashes_tracked_files():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads((root / 'SOURCE_MANIFEST.json').read_text())
    entries = {key: value for key, value in manifest.items() if isinstance(value, str)}
    for name, expected in entries.items():
        path = root / name
        assert path.is_file(), f'Manifest entry is missing: {name}'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
    if (root / '.git').exists():
        tracked = set(subprocess.check_output(['git', 'ls-files', '-z'], cwd=root).decode().split('\0'))
        tracked -= {'', 'SOURCE_MANIFEST.json'}
        assert set(entries) == tracked
