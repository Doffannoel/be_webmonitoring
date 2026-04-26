# Energy Monitoring Backend (Django REST Framework)

## 📌 Overview

Backend ini merupakan sistem **Energy Monitoring berbasis IoT** yang dibangun menggunakan **Django + Django REST Framework**.

Tujuan utama backend ini:

* Menyediakan **API yang rapi, konsisten, dan scalable** untuk frontend
* Mengelola data **gedung, ruangan, device IoT, energy reading**
* Menghasilkan **carbon footprint harian** secara otomatis
* Mengelola **alert berbasis threshold**
* Menjadi fondasi untuk **AI / forecasting energi** di tahap selanjutnya

Backend ini dirancang agar **mudah dipahami oleh Frontend Developer**, Data/AI Engineer, dan stakeholder non-backend.

---

## 🎯 Demo Data / Seed

Untuk kebutuhan development frontend, backend ini menyediakan management command untuk mengisi data dummy secara otomatis.

### Jalankan seed

```bash
python manage.py seed_demo_data --reset
```

Perintah di atas akan membuat data dummy untuk:

* Building
* Room
* Device
* ThresholdSettings
* ThresholdRule
* EnergyReading
* CarbonFootprint
* Alert
* EnergyPrediction

### Opsi tambahan

```bash
python manage.py seed_demo_data --reset --days 30 --readings-per-device 3
```

Keterangan:

* `--reset` menghapus data demo lama lalu membuat ulang dari awal
* `--days` menentukan jumlah hari histori reading yang digenerate
* `--readings-per-device` menentukan jumlah reading per device per hari

### Catatan

* Jika data demo sudah ada, command akan berhenti aman dan meminta `--reset`
* Seed ini dibuat supaya frontend tidak perlu hit API satu per satu untuk mengisi state awal dashboard

---

## 🧱 Tech Stack

* Python 3.x
* Django
* Django REST Framework (DRF)
* drf-spectacular (Swagger / OpenAPI)
* SQLite (dev, bisa diganti PostgreSQL)

---

## 📂 Struktur Project

```
be/
├── be/                 # Django project config
├── core/               # Master data (static / reference)
│   ├── models.py       # Building, Room, Device, ThresholdRule
│   ├── views.py        # CRUD API
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── monitoring/         # Time-series & monitoring logic
│   ├── models.py       # EnergyReading, CarbonFootprint, Alert, EnergyPrediction
│   ├── services.py     # Business logic (carbon + alert)
│   ├── views.py        # API endpoints
│   ├── serializers.py
│   ├── urls.py
│   └── admin.py
│
├── manage.py
└── README.md
```

---

## 🏗️ Data Model & Konsep

### 1️⃣ Building

Representasi gedung.

| Field | Description                   |
| ----- | ----------------------------- |
| name  | Nama gedung (human readable)  |
| code  | Kode unik gedung (misal: CSL) |

**Contoh:**

* name: Campus Smart Lab
* code: CSL

---

### 2️⃣ Room

Ruangan di dalam gedung.

| Field    | Description                      |
| -------- | -------------------------------- |
| building | Relasi ke Building               |
| name     | Nama ruangan                     |
| code     | Kode ruangan (unik per building) |

**Full identifier otomatis:** `CSL/3025`

---

### 3️⃣ Device

Representasi device IoT (sensor energi).

| Field         | Description                       |
| ------------- | --------------------------------- |
| device_id     | ID unik IoT (dipakai saat ingest) |
| name          | Nama device                       |
| device_type   | meter / ac / light / other        |
| room          | Lokasi device                     |
| brand         | Brand device                      |
| model         | Model device                      |
| capacity_watt | Kapasitas daya maksimum           |
| is_active     | Status aktif                      |

⚠️ **device_id adalah kunci utama integrasi IoT**

---

### 4️⃣ EnergyReading (Time-Series)

Data yang dikirim langsung dari IoT.

| Field      | Description      |
| ---------- | ---------------- |
| device     | Relasi ke Device |
| timestamp  | Waktu data       |
| voltage    | Tegangan (V)     |
| current    | Arus (A)         |
| power_watt | Daya (W)         |
| energy_kwh | Energi (kWh)     |

---

### 5️⃣ CarbonFootprint

Agregasi harian konsumsi energi & emisi karbon.

| Field           | Description                 |
| --------------- | --------------------------- |
| date            | Tanggal                     |
| total_kwh       | Total energi hari itu       |
| emission_factor | Faktor emisi (default 0.80) |
| emission_kg_co2 | Hasil perhitungan           |

⚙️ **Dihitung otomatis setiap ingest data**

---

### 6️⃣ ThresholdRule

Aturan untuk memicu Alert otomatis.

| Scope      | Cara kerja                            |
| ---------- | ------------------------------------- |
| Per Device | Berlaku untuk 1 device                |
| Per Room   | Berlaku untuk semua device di ruangan |

| Field         | Description                    |
| ------------- | ------------------------------ |
| power_watt_gt | Trigger jika power > nilai ini |
| severity      | info / warning / critical      |

---

### 7️⃣ Alert

Log peringatan otomatis.

| Field       | Description     |
| ----------- | --------------- |
| timestamp   | Waktu alert     |
| device      | Device penyebab |
| severity    | Level alert     |
| message     | Deskripsi       |
| is_resolved | Status          |

---

### 8️⃣ EnergyPrediction

Hasil forecasting (untuk tahap AI).

| Field            | Description         |
| ---------------- | ------------------- |
| date             | Tanggal prediksi    |
| predicted_kwh    | Prediksi energi     |
| ci_low / ci_high | Confidence interval |
| model_version    | Versi model         |

---

## 🔌 API Base URL

```
http://localhost:8000/api/
```

Swagger / API Docs:

```
http://localhost:8000/api/docs/
```

---

## 📡 API Endpoint (Frontend Friendly)

### 🔹 Master Data (Core)

| Method   | Endpoint              |
| -------- | --------------------- |
| GET/POST | /api/buildings/       |
| GET/POST | /api/rooms/           |
| GET/POST | /api/devices/         |
| GET/POST | /api/threshold-rules/ |

Support:

* pagination
* filtering
* search
* ordering

---

### 🔹 Energy Reading (IoT Ingest)

#### POST `/api/readings/ingest/`

Dipakai oleh IoT **dan frontend simulator**.

**Request JSON:**

```json
{
  "device_id": "PZEM001",
  "power_watt": 260,
  "energy_kwh": 0.15,
  "voltage": 220,
  "current": 1.2
}
```

**Behavior otomatis:**

* Simpan EnergyReading
* Update CarbonFootprint harian
* Evaluasi ThresholdRule → create Alert

---

### 🔹 Energy Readings (Query)

| Method | Endpoint       |
| ------ | -------------- |
| GET    | /api/readings/ |

Filter contoh:

```
/api/readings/?device=1
/api/readings/?device__room__building=1
```

---

### 🔹 Carbon Footprint

| Method | Endpoint            |
| ------ | ------------------- |
| GET    | /api/carbon/        |
| POST   | /api/carbon/recalc/ |

Recalculate manual:

```json
{ "date": "2026-01-01" }
```

---

### 🔹 Alerts

| Method | Endpoint                  |
| ------ | ------------------------- |
| GET    | /api/alerts/              |
| POST   | /api/alerts/{id}/resolve/ |

---

### 🔹 Energy Prediction

| Method   | Endpoint          |
| -------- | ----------------- |
| GET/POST | /api/predictions/ |

Digunakan oleh modul AI nanti.

---

## 🔐 Authentication & Permission

Saat ini:

* **AllowAny** (tidak ada auth)
* Cocok untuk development & integrasi awal

📌 Bisa ditambahkan JWT di tahap selanjutnya.

---

## 🧪 Alur Testing yang Disarankan

1. Tambah Building
2. Tambah Room
3. Tambah Device
4. Tambah ThresholdRule
5. POST `/readings/ingest/`
6. Cek:

   * Energy Readings
   * Carbon Footprints
   * Alerts

---

## 🤝 Panduan untuk Frontend Developer

Frontend **tidak perlu hitung apa pun**:

* Tidak perlu hitung karbon
* Tidak perlu cek threshold
* Tidak perlu create alert manual

Frontend cukup:

* Fetch API
* Render data
* Kirim ingest (jika simulasi)

Semua logic ada di backend.

---

## 🚀 Roadmap Lanjutan

* Aggregation API (daily / weekly / monthly)
* Realtime (WebSocket)
* Authentication (JWT)
* AI Forecasting Integration

---

## 👨‍💻 Author

Backend Developer: Doffannoel Sihotang & I Dewa Made Adi Kresna (DevOps)

Project: Energy Monitoring System
