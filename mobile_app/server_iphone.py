import http.server
import socketserver
import os
import socket
import mimetypes

import sys

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build", "web")

# Ensure proper MIME types for Flutter Web & CanvasKit WebAssembly
mimetypes.init()
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/wasm", ".wasm")
mimetypes.add_type("application/json", ".json")
mimetypes.add_type("image/svg+xml", ".svg")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

class RobustHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Disable caching for instant updates and add CORS
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def guess_type(self, path):
        if path.endswith(".js"):
            return "application/javascript"
        if path.endswith(".wasm"):
            return "application/wasm"
        return super().guess_type(path)

    def copyfile(self, source, outputfile):
        try:
            super().copyfile(source, outputfile)
        except (ConnectionResetError, BrokenPipeError):
            pass

    def log_message(self, format, *args):
        # Clean logging for mobile requests
        print(f"[iPhone Web Server] {self.address_string()} - {args[0]}")

class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def handle_error(self, request, client_address):
        # Suppress noisy socket disconnect logs when mobile browser changes tabs or aborts early
        pass

if __name__ == "__main__":
    if not os.path.exists(DIRECTORY):
        print(f"[ERROR] Direktori build/web tidak ditemukan di: {DIRECTORY}")
        print("Jalankan 'flutter build web --release' terlebih dahulu!")
        exit(1)

    local_ip = get_local_ip()
    print("=" * 60)
    print("   XAU/USD RADAR - INSTITUTIONAL ENGINE WEB SERVER")
    print("=" * 60)
    print(f"[*] Melayani folder : {DIRECTORY}")
    print(f"[*] Port            : {PORT}")
    print(f"[*] Akses dari PC   : http://localhost:{PORT}")
    print(f"[*] Akses iPhone/HP : http://{local_ip}:{PORT}")
    print("=" * 60)
    print("Silakan buka tautan di Safari iPhone Anda sekarang!")
    print("Tekan Ctrl+C untuk menghentikan server.\n")

    with ThreadingHTTPServer(("0.0.0.0", PORT), RobustHTTPRequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer dihentikan.")
