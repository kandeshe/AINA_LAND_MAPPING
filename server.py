from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
import threading
import os

PORT = 8000

def start_server():

    os.chdir("resources")

    server = ThreadingHTTPServer(
        ("127.0.0.1", PORT),
        SimpleHTTPRequestHandler
    )

    threading.Thread(
        target=server.serve_forever,
        daemon=True
    ).start()

    return server
