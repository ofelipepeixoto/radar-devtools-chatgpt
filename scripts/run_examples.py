"""Exercise the public CLI, validate known outputs and preserve source files."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = {
    "base64-encode": ("text", "T2zDoSwgUmFkYXIh"),
    "base64-decode": ("text", "Olá, Radar!"),
    "url-encode": ("text", "Radar%20%2F%20IA%20%2B%20dados"),
    "url-decode": ("text", "Radar / IA + dados"),
    "hash-sha256": ("hex", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
    "time-convert": ("utc", "2026-10-21T18:00:00Z"),
    "network-cidr": ("address_count", "256"),
    "uuid-inspect": ("version", 4),
    "url-inspect": ("host", "example.com"),
    "json-diff": ("equal", False),
    "json-format": ("text", '{\n  "portal": "Radar",\n  "valor": 9007199254740993,\n  "ativo": true\n}'),
}


def main():
    with tempfile.TemporaryDirectory() as directory:
        for name, (field, expected) in EXPECTED.items():
            source = ROOT / "examples" / (name + ".json")
            raw = source.read_bytes()
            output = Path(directory) / (name + ".json")
            process = subprocess.run(
                [sys.executable, "-m", "radar_devtools", str(source), "--output", str(output)],
                cwd=ROOT, capture_output=True, text=True, timeout=10, check=False,
            )
            assert process.returncode == 0, (name, process.stderr)
            report = json.loads(output.read_text())
            assert report["result"][field] == expected, name
            assert report["input_sha256"] == hashlib.sha256(raw).hexdigest(), name
            assert source.read_bytes() == raw, name
        rejected = Path(directory) / "rejected.json"
        process = subprocess.run(
            [sys.executable, "-m", "radar_devtools", "examples/invalid/ambiguous-time.json", "--output", str(rejected)],
            cwd=ROOT, capture_output=True, text=True, timeout=10, check=False,
        )
        assert process.returncode == 2 and not rejected.exists()
    print("11 exemplos válidos e 1 recusa por ausência de fuso: aprovados; entradas preservadas.")


if __name__ == "__main__":
    main()
