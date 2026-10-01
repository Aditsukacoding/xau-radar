#!/bin/bash
# ============================================================
# deploy_cpanel.sh — Auto-deploy XAU/USD RADAR ke cPanel SSH
# Jalankan dari PC: bash deploy_cpanel.sh
# ============================================================

# ⚙️  KONFIGURASI — EDIT BAGIAN INI SESUAI HOSTING ANDA
SSH_USER="username"           # Username SSH cPanel Anda
SSH_HOST="your-domain.com"    # Domain atau IP server Anda
SSH_PORT="22"                 # Port SSH (biasanya 22)
BACKEND_PORT="8001"           # Port untuk FastAPI (tanya hosting Anda)
REMOTE_DIR="~/xauusd-backend" # Folder backend di server
PUBLIC_HTML="~/public_html/radar" # Folder frontend di server
# ============================================================

BACKEND_URL="http://${SSH_HOST}:${BACKEND_PORT}/api/v1"

echo "=========================================================="
echo "  XAU/USD RADAR — Deploy to cPanel"
echo "  Server : $SSH_USER@$SSH_HOST:$SSH_PORT"
echo "  Backend: $BACKEND_URL"
echo "=========================================================="

# Step 1: Build Flutter Web dengan URL backend production
echo ""
echo "[1/5] Building Flutter Web Release..."
cd "$(dirname "$0")/../mobile_app"
flutter build web --release --no-web-resources-cdn \
  --dart-define="BACKEND_URL=${BACKEND_URL}"

if [ $? -ne 0 ]; then
  echo "[ERROR] Flutter build gagal!"
  exit 1
fi
echo "[OK] Flutter build selesai."

# Step 2: Upload Backend
echo ""
echo "[2/5] Uploading Backend ke server..."
ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "mkdir -p $REMOTE_DIR/app $REMOTE_DIR/data"
scp -P "$SSH_PORT" -r "$(dirname "$0")/../backend/app" "$SSH_USER@$SSH_HOST:$REMOTE_DIR/"
scp -P "$SSH_PORT" "$(dirname "$0")/../backend/requirements.txt" "$SSH_USER@$SSH_HOST:$REMOTE_DIR/"
echo "[OK] Backend terupload."

# Step 3: Upload .env (TANPA API Key sensitif, set manual di server!)
echo ""
echo "[3/5] Membuat .env di server..."
ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "cat > $REMOTE_DIR/.env << 'EOF'
APP_NAME=Trading Bias Analysis Engine
APP_ENV=production
DEBUG=False
HOST=0.0.0.0
PORT=${BACKEND_PORT}
DATABASE_URL=sqlite:///./data/trading_analytics.db
USE_MOCK_DATA=False
ANTHROPIC_API_KEY=GANTI_DENGAN_API_KEY_ANDA
GEMINI_API_KEY=
FOREX_NEWS_API_KEY=
FINNHUB_API_KEY=
EOF"
echo "[OK] .env dibuat di server (ingat: ganti ANTHROPIC_API_KEY secara manual di server!)"

# Step 4: Setup Python venv & Install dependencies
echo ""
echo "[4/5] Setup Python environment di server..."
ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "
  cd $REMOTE_DIR
  python3 -m venv .venv 2>/dev/null || python -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt -q
  # Stop existing process kalau ada
  pkill -f 'uvicorn app.main:app' 2>/dev/null || true
  sleep 1
  # Jalankan backend dengan nohup
  nohup .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > uvicorn.log 2>&1 &
  echo \"Backend berjalan dengan PID: \$!\"
  sleep 2
  curl -s http://localhost:$BACKEND_PORT/health && echo ' [Backend ONLINE]' || echo ' [WARNING: Backend belum merespons, cek uvicorn.log]'
"

# Step 5: Upload Frontend Flutter Web
echo ""
echo "[5/5] Uploading Frontend ke public_html..."
ssh -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "mkdir -p $PUBLIC_HTML"
scp -P "$SSH_PORT" -r "$(dirname "$0")/../mobile_app/build/web/"* "$SSH_USER@$SSH_HOST:$PUBLIC_HTML/"
echo "[OK] Frontend terupload."

echo ""
echo "=========================================================="
echo "  ✅ DEPLOY SELESAI!"
echo ""
echo "  Backend API : http://$SSH_HOST:$BACKEND_PORT/api/v1"
echo "  Frontend PWA: http://$SSH_HOST/radar/"
echo ""  
echo "  Untuk install di iPhone:"
echo "  1. Buka Safari: http://$SSH_HOST/radar/"
echo "  2. Tap Share → Tambahkan ke Layar Utama"
echo "  3. Selesai! App berjalan fullscreen seperti native."
echo "=========================================================="
