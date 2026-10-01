Saya ingin membangun aplikasi mobile (Android & iOS) untuk analisis trading forex/komoditas yang mengumpulkan dan mensintesis data dari tiga kategori: fundamental (kalender ekonomi), geopolitik (berita), dan teknikal (harga & indikator), lalu menghasilkan kesimpulan bias otomatis (bullish/bearish/netral) beserta tingkat keyakinannya.

## Konteks
Saya siswa SMK jurusan RPL yang ingin belajar sekaligus membangun produk nyata. Proyek ini untuk portofolio dan penggunaan pribadi. Saya butuh arsitektur yang jelas, bisa dikembangkan bertahap (MVP dulu, lalu iterasi), dan mudah dipahami/dipelihara.

## Fitur utama yang dibutuhkan

1. **Dashboard utama**: menampilkan instrumen (mulai dari XAU/USD, bisa ditambah pair lain nanti), harga real-time, dan kesimpulan bias terkini (bullish/bearish/netral + confidence score).

2. **Modul Fundamental**:
   - Kalender ekonomi (event terjadwal: NFP, CPI, PPI, PCE, FOMC, dll) dengan forecast/previous/actual
   - Highlight event high-impact yang akan datang dalam 24-48 jam
   - Riwayat event yang sudah rilis beserta reaksi harga setelahnya (kalau memungkinkan)

3. **Modul Geopolitik**:
   - Feed berita relevan (difilter berdasarkan keyword/topik yang mempengaruhi instrumen yang dipantau)
   - Sentiment analysis sederhana per berita (positif/negatif/netral terhadap USD atau instrumen terkait)

4. **Modul Teknikal**:
   - Chart harga dengan timeframe yang bisa diganti (5m, 15m, 1H, 4H, Daily)
   - Indikator dasar: MA, RSI, support/resistance otomatis
   - Level kunci yang terdeteksi otomatis

5. **Analysis Engine (fitur inti)**:
   - Mengumpulkan data dari ketiga modul di atas
   - Mengirim data terstruktur ke LLM (Claude API) dengan prompt yang sudah dirancang untuk menghasilkan kesimpulan bias dalam format JSON terstandarisasi (bias, confidence score, ringkasan per kategori, faktor risiko, level kunci)
   - Menampilkan hasil ini di dashboard dengan visual yang jelas (badge warna, confidence meter)

6. **Notifikasi push**: alert sebelum high-impact news (15 menit dan 5 menit sebelum rilis), dan saat kesimpulan bias berubah signifikan.

## Batasan & prinsip penting
- WAJIB menampilkan disclaimer "bukan saran finansial" di setiap kesimpulan bias yang ditampilkan
- Jangan pernah menampilkan rekomendasi "beli sekarang/jual sekarang" secara eksplisit — fokus pada arah bias dan confidence level saja
- Semua kesimpulan harus bisa dilacak sumber datanya (traceable), bukan black box

## Preferensi teknis (boleh disesuaikan jika ada rekomendasi lebih baik)
- Frontend: Flutter (untuk Android & iOS dari satu codebase)
- Backend: Node.js/Express atau Python/FastAPI — tolong beri rekomendasi mana yang lebih cocok untuk proyek ini dan jelaskan alasannya
- Database: untuk menyimpan histori data kalender ekonomi, berita, dan hasil analisis
- Sumber data eksternal yang akan diintegrasikan: ForexNewsAPI (kalender ekonomi + berita), FCSAPI atau sejenisnya (data harga & teknikal), Claude API (analysis engine)

## Yang saya butuhkan dari kamu
1. Rekomendasi arsitektur sistem secara keseluruhan (diagram/penjelasan alur data dari sumber eksternal → backend → database → frontend)
2. Struktur database (skema tabel/koleksi) untuk menyimpan data kalender ekonomi, berita, harga historis, dan hasil analisis
3. Rencana pengembangan bertahap (MVP dulu — misal hanya 1 instrumen dan modul fundamental+teknikal dasar — lalu roadmap fitur berikutnya)
4. Struktur folder project untuk backend dan frontend
5. Mulai implementasi dari bagian paling fondasional terlebih dahulu (misal: setup backend dan koneksi ke satu sumber data dulu), lalu build secara bertahap

Tolong mulai dengan bertanya kepada saya jika ada hal yang perlu diklarifikasi sebelum mulai membangun, terutama terkait API key yang saya miliki/belum miliki, dan preferensi platform deployment (misal backend di-hosting di mana).