from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading
import os
from pathlib import Path


PORT = 8000


def start_server():

    # Get the folder where server.py is located
    BASE_DIR = Path(__file__).resolve().parent

    # Locate the resources folder inside the project
    RESOURCES_DIR = BASE_DIR / "resources"

    # Check that resources exists
    if not RESOURCES_DIR.exists():

        raise FileNotFoundError(
            f"Resources folder not found:\n{RESOURCES_DIR}"
        )

    # Change to the absolute resources path
    os.chdir(RESOURCES_DIR)

    print("LARA resources directory:")
    print(RESOURCES_DIR)

    server = ThreadingHTTPServer(
        ("127.0.0.1", PORT),
        SimpleHTTPRequestHandler
    )

    threading.Thread(
        target=server.serve_forever,
        daemon=True
    ).start()

    print(f"LARA server running on http://127.0.0.1:{PORT}")

    return server