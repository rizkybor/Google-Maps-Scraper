# Google Maps Scraper + Telegram Scrapper BOT AI Professional

Python scraper berbasis Playwright untuk mengambil data bisnis dari Google Maps, dengan mode CLI dan mode Telegram Bot yang dibuat untuk penggunaan profesional (command-based, output terstruktur, dan file hasil langsung dikirim lewat Telegram).

## Fitur

- Scraping Google Maps: auto-scroll hasil, ekstraksi data bisnis secara robust
- Anti-detection: custom user-agent, random delay, dan stealth init script
- Enrichment kontak: phone/email dari sumber web (jika tersedia) + prioritas divisi (Marketing/Business Development/Humas)
- Kategori AI (opsional): LOCATION_CATEGORY + FACILITY_CATEGORY memakai Groq LLM
- Export profesional:
  - XLSX (header uppercase, styling, wrap, auto-width, freeze header, autofilter)
  - Summary DOCX (untuk laporan ringkas)
- Telegram Bot mode:
  - Input dibatasi command (/start, /help, /scrape) supaya user tidak mengetik sembarang
  - “Typing…” saat proses scraping berjalan, dan status upload saat kirim dokumen
  - Output hasil otomatis dikirim sebagai dokumen Telegram (XLSX + DOCX)

## Instalasi

```bash
python3 -m pip install -r requirements.txt
python3 -m playwright install chromium
```

## Konfigurasi (.env)

Buat file `.env` di root project (jangan commit ke git). Contoh variabel yang dipakai:

- `OUTPUT_DIRECTORY=output`
- `DEFAULT_MAX_RESULTS=50`
- `DEFAULT_DELAY_MIN=1`
- `DEFAULT_DELAY_MAX=3`
- `HEADLESS=true`
- `GROQ_API_KEY=...` (wajib kalau memakai AI categorize)
- `TELEGRAM_BOT_TOKEN=...` (wajib untuk mode Telegram)
- `TELEGRAM_ALLOWED_CHAT_IDS=` (opsional; kosong = allow semua)

## Cara Menjalankan

## Perintah di Terminal

```bash
# Install dependency Python
python3 -m pip install -r requirements.txt

# Install browser Playwright
python3 -m playwright install chromium

# Jalankan Telegram Bot
python3 main.py --telegram-bot

# Jalankan Mode CLI (XLSX)
python3 main.py "Universitas di Jakarta Selatan" --max-results 50 --headless --output-format excel

# Jalankan Mode CLI (XLSX + AI categorize)
python3 main.py "Apartemen di Jakarta Selatan" --max-results 50 --headless --output-format excel --ai-categorize
```

Utility:

```bash
# Cek proses bot yang sedang berjalan (hindari Conflict 409 karena dobel polling)
ps aux | grep "main.py --telegram-bot"
```

### Mode Telegram Bot (Recommended)

Jalankan bot:

```bash
python3 main.py --telegram-bot
```

Perintah di Telegram:

- `/start` atau `/help` untuk instruksi
- `/scrape <query> | max=50 | headless=1 | ai=1`

Contoh:

```
/scrape Universitas di Jakarta Selatan | max=10 | ai=1
```

Output yang diterima user di Telegram:
- `google_maps_results_YYYYMMDD_HHMMSS.xlsx`
- `summary_YYYYMMDD_HHMMSS.docx`

Catatan opsi:
- Opsi yang diizinkan hanya: `max`, `headless`, `ai`
- CSV tidak tersedia di mode Telegram

### Mode CLI

Scrape via terminal:

```bash
python3 main.py "Universitas di Jakarta Selatan" --max-results 50 --headless --output-format excel
```

## Data yang Diekstrak

Field utama yang diekspor (tergantung ketersediaan data):
- NAME, RATING, REVIEWS_COUNT
- LOCATION_CATEGORY, FACILITY_CATEGORY
- ADDRESS, WEBSITE
- EMAIL, PHONE, NUMBER_DIVISION
- PIC

## Troubleshooting

### Telegram Conflict (409): “terminated by other getUpdates request”

Artinya ada lebih dari satu proses bot yang polling bersamaan.
- Pastikan hanya satu terminal/mesin yang menjalankan `python3 main.py --telegram-bot`
- Jika perlu, matikan proses duplikat lalu jalankan ulang

### Playwright tidak jalan / browser error

```bash
python3 -m playwright install chromium
```

### Disk penuh saat menyimpan file

Kosongkan storage (output/caches) lalu coba lagi.

## Legal Notice

Tool ini dibuat untuk tujuan edukasi dan riset. Pengguna bertanggung jawab untuk mematuhi Terms of Service Google dan hukum yang berlaku.
