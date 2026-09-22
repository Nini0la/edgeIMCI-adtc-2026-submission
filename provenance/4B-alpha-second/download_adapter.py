"""Fetch the exact original LoRA adapter into the ignored local adapter directory."""

import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    root = Path(__file__).resolve().parent
    record = json.loads((root / "artifact.json").read_text())
    destination = root / "adapter"
    destination.mkdir(exist_ok=True)
    for name, expected in record["adapter"]["files"].items():
        output = destination / name
        partial = destination / (name + ".partial")
        digest = hashlib.sha256()
        size = 0
        try:
            with urllib.request.urlopen(expected["url"], timeout=120) as response, partial.open("wb") as stream:
                for chunk in iter(lambda: response.read(1024 * 1024), b""):
                    size += len(chunk)
                    if size > expected["bytes"]:
                        raise ValueError(f"Oversized adapter response: {name}")
                    digest.update(chunk)
                    stream.write(chunk)
            if size != expected["bytes"] or digest.hexdigest() != expected["sha256"]:
                raise ValueError(f"Adapter checksum/size mismatch: {name}")
            partial.replace(output)
            print(f"VERIFIED {name} {size} bytes {digest.hexdigest()}")
        finally:
            partial.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
