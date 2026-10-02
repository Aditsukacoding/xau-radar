import os
import zipfile
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))

def create_backend_zip():
    backend_dir = os.path.join(ROOT, "backend")
    out_zip = os.path.join(ROOT, "backend_upload.zip")
    if os.path.exists(out_zip):
        os.remove(out_zip)

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        # Add app/
        app_dir = os.path.join(backend_dir, "app")
        for root, dirs, files in os.walk(app_dir):
            if "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".pyc"):
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, backend_dir)
                z.write(file_path, arcname)

        # Add requirements.txt
        req_path = os.path.join(backend_dir, "requirements.txt")
        if os.path.exists(req_path):
            z.write(req_path, "requirements.txt")

        # Add passenger_wsgi.py
        wsgi_path = os.path.join(backend_dir, "passenger_wsgi.py")
        if os.path.exists(wsgi_path):
            z.write(wsgi_path, "passenger_wsgi.py")

        # Add bundled a2wsgi package so server never fails with ModuleNotFoundError
        a2wsgi_dir = os.path.join(backend_dir, "a2wsgi")
        if os.path.exists(a2wsgi_dir):
            for root, dirs, files in os.walk(a2wsgi_dir):
                if "__pycache__" in root:
                    continue
                for file in files:
                    if file.endswith(".pyc"):
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backend_dir)
                    z.write(file_path, arcname)

        # Add production .env
        env_path = os.path.join(backend_dir, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                env_content = f.read()
            # Ensure production settings
            env_content = env_content.replace('APP_ENV="development"', 'APP_ENV="production"')
            env_content = env_content.replace('DEBUG=True', 'DEBUG=False')
            z.writestr(".env", env_content)

        # Create empty data directory entry
        z.writestr("data/.gitkeep", "")

    size_mb = os.path.getsize(out_zip) / (1024 * 1024)
    print(f"[OK] backend_upload.zip created ({size_mb:.2f} MB)")

def create_frontend_zip():
    web_dir = os.path.join(ROOT, "mobile_app", "build", "web")
    out_zip = os.path.join(ROOT, "frontend_upload.zip")
    if not os.path.exists(web_dir):
        print("[WARN] mobile_app/build/web does not exist yet.")
        return

    if os.path.exists(out_zip):
        os.remove(out_zip)

    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(web_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, web_dir)
                z.write(file_path, arcname)

    size_mb = os.path.getsize(out_zip) / (1024 * 1024)
    print(f"[OK] frontend_upload.zip created ({size_mb:.2f} MB)")

if __name__ == "__main__":
    create_backend_zip()
    create_frontend_zip()
