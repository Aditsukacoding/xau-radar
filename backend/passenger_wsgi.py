# passenger_wsgi.py — Wajib ada untuk cPanel "Setup Python App" (Passenger/WSGI)
# cPanel akan otomatis memanggil file ini sebagai entry point aplikasi.
# Tidak perlu menentukan port — cPanel yang handle routing HTTP via subdomain.

import sys
import os

# Tambahkan direktori project ke Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables dari .env jika python-dotenv tersedia
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
except ImportError:
    pass

# Import FastAPI app — Passenger memanggil objek 'application' ini
from app.main import app

# WSGI adapter untuk Passenger (cPanel) yang menjalankan ASGI FastAPI
# Menggunakan a2wsgi agar FastAPI bisa jalan di Passenger WSGI
try:
    from a2wsgi import ASGIMiddleware
    application = ASGIMiddleware(app)
except ImportError:
    # Fallback: coba pakai asgiref
    try:
        from asgiref.wsgi import WsgiToAsgi
        # Ini tidak langsung, tapi bisa sebagai fallback
        application = app
    except ImportError:
        application = app
