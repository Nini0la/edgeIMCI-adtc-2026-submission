"""Smoke-test the unchanged integrated server in stub mode."""

from __future__ import annotations

import json
from threading import Thread
from urllib.request import urlopen

from app.api import make_server


def main() -> None:
    server = make_server(port=0, extractor_mode="stub")
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        with urlopen(f"{base_url}/api/health", timeout=10) as response:
            health = json.load(response)
        with urlopen(f"{base_url}/", timeout=10) as response:
            index_status = response.status
            content_type = response.headers.get_content_type()
            index = response.read().decode("utf-8")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    if health != {"status": "ok", "mode": "Prototype / stub extraction"}:
        raise RuntimeError(f"unexpected health response: {health}")
    if index_status != 200 or content_type != "text/html" or '<div id="root"></div>' not in index:
        raise RuntimeError("built frontend was not served correctly")

    print(
        json.dumps(
            {
                "status": "PASS",
                "scope": "existing-product-stub-mode",
                "health": health,
                "frontend_http_status": index_status,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
