# Distributed Synchronization System
**Nama:** Dhio Anugrah Prakasa Putro  
**NIM:** 11221004  
**Mata Kuliah:** Sistem Terdistribusi  
**Judul Proyek:** Distributed Synchronization System (Lock–Queue–Cache)

## Deskripsi Singkat
Proyek ini mengimplementasikan sistem sinkronisasi terdistribusi yang mensimulasikan skenario real-world di mana beberapa node saling berkomunikasi dan menjaga konsistensi data bersama. Fokus utama ada pada tiga komponen penting:

| Komponen | Tujuan | Algoritma |
|-----------|---------|-----------|
| Distributed Lock Manager | Menyediakan koordinasi akses terhadap resource bersama antar-node | Raft Consensus (stub leader) |
| Distributed Queue System | Menangani pengiriman pesan antar-producer/consumer dengan konsistensi | Consistent Hashing + At-least-once Delivery |
| Distributed Cache Coherence | Menyinkronkan cache antar-node | MESI Protocol + LRU Replacement |

## Spesifikasi Teknis

### 1. Core Components
#### A. Distributed Lock Manager (DLM)
- Shared (S) dan Exclusive (X) lock didukung.
- Lock disepakati melalui Raft leader (stub).
- Implementasi deadlock detection berbasis wait-for graph.
- Network partition disimulasikan dengan log konsensus (leader–follower).

#### B. Distributed Queue System
- Menggunakan Consistent Hashing untuk distribusi topic antar-node.
- At-least-once delivery dijamin dengan inflight TTL dan requeue otomatis.
- Persistensi via Redis AOF (Append Only File).
- Mendukung multiple producers & consumers.

#### C. Distributed Cache Coherence
- MESI (Modified–Exclusive–Shared–Invalid) protocol disimulasikan antar-node.
- Saat node melakukan PUT, node lain menerima invalidation.
- LRU (Least Recently Used) digunakan sebagai cache replacement policy.
- Metrik performa tersedia di /metrics endpoint.

#### D. Containerization
- Setiap node dikemas dalam Docker container.
- docker-compose mengatur orkestrasi multi-node.
- Redis digunakan sebagai shared state backend.
- Konfigurasi environment didefinisikan dalam file .env.

## Struktur Proyek
```
distributed-sync-system/
├── src/
│   ├── nodes/
│   │   ├── base_node.py
│   │   ├── lock_manager.py
│   │   ├── queue_node.py
│   │   └── cache_node.py
│   ├── consensus/
│   │   ├── raft.py
│   │   └── pbft.py (opsional)
│   ├── communication/
│   │   ├── message_passing.py
│   │   └── failure_detector.py
│   └── utils/
│       ├── config.py
│       └── metrics.py
├── docker/
│   ├── Dockerfile.node
│   └── docker-compose.yml
├── benchmarks/
│   └── load_test_scenarios.py
├── docs/
│   ├── architecture.md
│   ├── api_spec.yaml
│   └── deployment_guide.md
├── tests/
│   ├── unit/
│   ├── integration/
│   └── performance/
├── requirements.txt
├── .env.example
├── README.md
└── report.pdf
```

## Arsitektur Sistem
- Node Leader (node1) menerima request, mereplikasi ke follower (node2, node3).
- Redis menyimpan state global (locks, queues, cache directory).
- AIOHTTP menangani REST API.
- Prometheus Client menyediakan /metrics.

## API Endpoint

| Komponen | Endpoint | Method | Deskripsi |
|-----------|-----------|--------|------------|
| Lock | /locks/acquire | POST | Request lock (S/X) |
| Lock | /locks/release | POST | Melepaskan lock |
| Lock | /locks/state | GET | (Debug) lihat tabel lock |
| Queue | /queue/enqueue | POST | Masukkan pesan ke topic |
| Queue | /queue/consume | POST | Ambil pesan dari topic |
| Cache | /cache/get | GET | Ambil data dari cache |
| Cache | /cache/put | POST | Menyimpan data + invalidation |
| System | /metrics | GET | Export Prometheus metrics |
| System | /health | GET | Cek status node |

## Langkah Eksperimen

### 1. Jalankan Cluster
```
cd docker
docker compose build --no-cache
docker compose up -d
```
Cek container:
```
docker ps --format "table {{.Names}}	{{.Status}}	{{.Ports}}"
```

### 2. Health Check
```
(Invoke-WebRequest -Uri http://localhost:8081/health).Content
(Invoke-WebRequest -Uri http://localhost:8082/health).Content
(Invoke-WebRequest -Uri http://localhost:8083/health).Content
```

### 3. Test Lock Manager
```
Invoke-WebRequest -Uri http://localhost:8081/locks/acquire -Method POST `
  -Body '{"key":"doc1","client_id":"c1","mode":"S"}' -ContentType 'application/json'
Invoke-WebRequest -Uri http://localhost:8081/locks/acquire -Method POST `
  -Body '{"key":"doc1","client_id":"c2","mode":"S"}' -ContentType 'application/json'
Invoke-WebRequest -Uri http://localhost:8081/locks/acquire -Method POST `
  -Body '{"key":"doc1","client_id":"c3","mode":"X"}' -ContentType 'application/json'
Invoke-WebRequest -Uri http://localhost:8081/locks/release -Method POST `
  -Body '{"key":"doc1","client_id":"c1"}' -ContentType 'application/json'
Invoke-WebRequest -Uri http://localhost:8081/locks/release -Method POST `
  -Body '{"key":"doc1","client_id":"c2"}' -ContentType 'application/json'
Invoke-WebRequest -Uri http://localhost:8081/locks/acquire -Method POST `
  -Body '{"key":"doc1","client_id":"c3","mode":"X"}' -ContentType 'application/json'
```

### 4. Deadlock Simulation
```
Invoke-WebRequest -Uri http://localhost:8081/locks/acquire -Method POST `
  -Body '{"key":"a","client_id":"c1","mode":"X"}' -ContentType 'application/json'
Invoke-WebRequest -Uri http://localhost:8081/locks/acquire -Method POST `
  -Body '{"key":"b","client_id":"c2","mode":"X"}' -ContentType 'application/json'
Invoke-WebRequest -Uri http://localhost:8081/locks/acquire -Method POST `
  -Body '{"key":"b","client_id":"c1","mode":"X"}' -ContentType 'application/json'
Invoke-WebRequest -Uri http://localhost:8081/locks/acquire -Method POST `
  -Body '{"key":"a","client_id":"c2","mode":"X"}' -ContentType 'application/json'
```
Cek state:
```
(Invoke-WebRequest -Uri http://localhost:8081/locks/state).Content
```

## Monitoring dan Metrics
```
(Invoke-WebRequest -Uri http://localhost:8081/metrics).Content
```
Contoh metrik:
```
locks_acquire_total{mode="S",result="ok"} 2
locks_acquire_total{mode="X",result="wait"} 1
queue_enqueued_total{topic="alpha"} 4
cache_invalidation_total{reason="write"} 2
```

## Teknologi yang Digunakan
- Python 3.11
- AIOHTTP (Async HTTP Server)
- Redis (State Backend)
- Docker & Docker Compose
- Prometheus Client
- Locust (Load Testing)

## Dokumentasi Pendukung
- docs/architecture.md – Diagram arsitektur sistem
- docs/api_spec.yaml – Spesifikasi OpenAPI

