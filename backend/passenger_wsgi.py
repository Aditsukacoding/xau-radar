# passenger_wsgi.py — Entry point untuk cPanel "Setup Python App" (Phusion Passenger WSGI)
import sys
import os

# 1. Tandai environment sebagai WSGI
os.environ["IS_WSGI"] = "true"

# 2. Pastikan direktori project berada di sys.path paling depan
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# 3. Muat environment variables dari file .env
try:
    from dotenv import load_dotenv
    env_file = os.path.join(BASE_DIR, ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)
except ImportError:
    pass

# 4. Inisialisasi ASGI-to-WSGI Middleware dengan Diagnostic Fallback
try:
    from a2wsgi import ASGIMiddleware
    from app.main import app
    application = ASGIMiddleware(app)
except Exception as e:
    import traceback
    err_trace = traceback.format_exc()
    
    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/html; charset=utf-8')])
        html = f"""<!DOCTYPE html>
<html>
<head><title>Backend Startup Error</title></head>
<body style="font-family: monospace; background: #0A0D14; color: #F87171; padding: 24px;">
  <h2 style="color: #FBBF24;">XAU/USD RADAR — Passenger Startup Diagnostic</h2>
  <p style="color: #94A3B8;">Aplikasi backend FastAPI mengalami kendala saat dimuat oleh Passenger:</p>
  <pre style="background: #161F33; padding: 16px; border-radius: 8px; border: 1px solid #334155; overflow: auto; color: #FCA5A5;">{err_trace}</pre>
</body>
</html>"""
        return [html.encode('utf-8')]
