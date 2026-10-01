# Trading Bias Analysis Engine (XAU/USD Gold & Forex)

Aplikasi mobile trading analytics berbasis AI yang mengumpulkan dan mensintesis data dari tiga pilar utama pasar finansial: **Fundamental** (Kalender Ekonomi), **Geopolitik** (Berita Global & Sentimen), dan **Teknikal** (Grafik OHLCV & Indikator Pasar), untuk menghasilkan kesimpulan arah bias pasar (*Bullish / Bearish / Netral*) beserta skor keyakinan (*confidence score*) secara objektif, transparan, dan terukur.

> [!IMPORTANT]
> **PENAFIAN HUKUM & RISIKO (DISCLAIMER):**
> Sistem ini dibuat murni untuk tujuan edukasi dan portofolio komputasi finansial. Sistem ini **BUKAN** saran finansial, ajakan investasi, maupun sinyal eksekusi beli/jual langsung. Trading instrumen finansial memiliki tingkat risiko kerugian modal yang tinggi.

---

## 🏛️ Arsitektur Sistem

```
┌────────────────────────────────────────────────────────┐
│             External Sources (Dual Mode)               │
│  - Mock Realistic Provider (Offline / No Key Needed)   │
│  - Claude 3.5 Sonnet / Gemini 1.5 Flash (AI Engine)    │
│  - Live ForexNewsAPI & TwelveData API (Optional)       │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│              FastAPI Backend (Python 3.11)             │
│  ├── Ingestion Service (Seeding & Data Sync)           │
│  ├── Pure Python Technical Calculator (RSI, SMA, S/R)  │
│  ├── AI Synthesizer Engine (Structured JSON Bias)      │
│  └── REST API Endpoints (/api/v1/...)                  │
└──────────────┬───────────────────────────┬─────────────┘
               │                           │
               ▼                           ▼
┌───────────────────────────┐ ┌──────────────────────────┐
│  Local SQLite Database    │ │   Flutter Mobile Client  │
│  - Instruments            │ │   - Android, iOS & Web   │
│  - Economic Events        │ │   - Dark Fintech Theme   │
│  - News Articles          │ │   - Interactive Candlestick│
│  - Price Candles (OHLCV)  │ │   - Confidence Gauge     │
│  - Analysis Reports       │ │   - 5 Navigation Modules │
└───────────────────────────┘ └──────────────────────────┘
```

---

## 🚀 Cara Menjalankan Proyek

Proyek ini terbagi menjadi dua bagian: **Backend (FastAPI)** dan **Frontend (Flutter)**.

### Langkah 1: Jalankan Backend Server
Buka terminal PowerShell baru dan jalankan:
```powershell
cd backend
.\run_server.ps1
```
*(Atau klik dua kali file [`backend/run_server.bat`](file:///c:/Users/Aditya/Desktop/analitic/backend/run_server.bat))*

Backend akan aktif di:
- **API URL**: `http://127.0.0.1:8000`
- **Swagger Interactive Docs**: `http://127.0.0.1:8000/docs`

---

### Langkah 2: Jalankan Frontend Flutter
Buka terminal PowerShell kedua dan jalankan:
```powershell
cd mobile_app
.\run_app.ps1
```
*(Atau klik dua kali file [`mobile_app/run_app.bat`](file:///c:/Users/Aditya/Desktop/analitic/mobile_app/run_app.bat))*

Secara default, aplikasi akan terbuka di browser **Google Chrome** sehingga kamu bisa langsung menguji seluruh fitur antarmuka secara interaktif.

Untuk menjalankan di **Emulator Android** atau **HP Fisik**:
```powershell
cd mobile_app
flutter run
```
*Catatan:* Jika dijalankan di HP fisik via Wi-Fi lokal, kamu dapat mengetuk ikon pengaturan di pojok kanan atas aplikasi untuk mengubah URL backend ke IP lokal komputermu (misal: `http://192.168.1.X:8000/api/v1`).

---

## 📱 Fitur Layar Aplikasi Mobile (Flutter)

1. **Dashboard Utama**:
   - Header harga real-time XAU/USD (Gold vs US Dollar), perubahan harga 24 jam, dan level High/Low harian.
   - Kartu Utama **Kesimpulan Bias AI (3 Pilar)** dengan *Confidence Meter* interaktif (0-100%) dan badge warna bercahaya (*Emerald Green = Bullish*, *Ruby Red = Bearish*, *Gold = Netral*).
   - Tombol **Minta Analisis Ulang (AI Refresh)** untuk memicu sintesis baru secara on-demand.
   - Radar event High-Impact terdekat dalam 24-48 jam.
   - Cuplikan sentimen geopolitik dan snapshot tren teknikal terkini.
   - Banner penafian hukum permanen.

2. **Modul Fundamental**:
   - Kalender ekonomi lengkap (NFP, CPI, PPI, PCE, FOMC).
   - Filter instan berdasarkan dampak: `Semua`, `High Impact`, `Medium Impact`.
   - Perbandingan data: Nilai Aktual vs Prediksi (*Forecast*) vs Periode Sebelumnya (*Previous*).
   - Indikator hitung mundur waktu rilis berita.

3. **Modul Geopolitik**:
   - Feed berita global yang mempengaruhi pergerakan Dolar AS dan Emas.
   - Analisis sentimen otomatis per berita (`Positif`, `Negatif`, `Netral`) lengkap dengan skor numerik (-1.0 s/d +1.0).
   - Filter sentimen berita.

4. **Modul Teknikal**:
   - **TradingView Real-Time Live Chart** resmi (feed: `FOREXCOM:XAUUSD` Gold Spot / U.S. Dollar).
   - Timeframe ribbon instan (`1m`, `5m`, `15m`, `1h`, `4h`, `1D`).
   - Fitur analisa profesional: zoom, pan, gambar trendline, serta indikator teknikal bawaan.
   - Kartu indikator **RSI (14)** dengan deteksi kondisi *Overbought / Oversold / Netral*.
   - Tabel Moving Average (SMA 20, SMA 50, SMA 200, dan EMA 9 / 21) dan level Support/Resistance.

5. **Laporan Lengkap Sintesis AI**:
   - Rincian narasi sintesis dari ketiga pilar: Fundamental, Geopolitik, dan Teknikal.
   - Daftar **Faktor Risiko Pembatal Bias** (kondisi yang dapat menggugurkan bias pasar).
   - **Transparansi Data (*Traceable Sources*)**: menampilkan bukti sumber data yang dipakai sehingga bukan analisis *black box*.
   - Area target Support & Resistance kunci.

---

## 📡 Daftar Endpoint REST API (`/api/v1`)

| Modul | Method | Endpoint | Deskripsi |
| :--- | :--- | :--- | :--- |
| **Dashboard** | `GET` | `/api/v1/dashboard/instruments` | Daftar instrumen aktif (default: `XAUUSD`) |
| **Dashboard** | `GET` | `/api/v1/dashboard/summary/{symbol}` | Ringkasan terpadu: harga, bias, radar event, berita, dan disclaimer |
| **Fundamental**| `GET` | `/api/v1/fundamental/calendar` | Jadwal kalender ekonomi dengan filter impact & tanggal |
| **Fundamental**| `GET` | `/api/v1/fundamental/upcoming-high-impact` | Radar event High Impact dalam 24-48 jam ke depan |
| **Geopolitik** | `GET` | `/api/v1/geopolitical/news` | Feed berita geopolitik & sentimen terhadap USD / Emas |
| **Teknikal** | `GET` | `/api/v1/technical/candles/{symbol}` | Data candle OHLCV untuk grafik (timeframe: `5m`, `15m`, `1h`, `4h`, `1d`) |
| **Teknikal** | `GET` | `/api/v1/technical/indicators/{symbol}` | Hasil kalkulasi RSI(14), Moving Averages, dan Support/Resistance |
| **AI Engine** | `GET` | `/api/v1/analysis/latest/{symbol}` | Laporan bias AI terkini (BULLISH/BEARISH/NEUTRAL + confidence score) |
| **AI Engine** | `POST`| `/api/v1/analysis/generate/{symbol}` | Memicu sintesis analisis AI baru secara on-demand |
