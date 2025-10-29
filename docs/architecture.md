# Arsitektur Ringkas
- DLM: Raft (stub leader=node1) untuk konsistensi operasi acquire/release.
- Queue: Consistent hashing + inflight store (Redis) untuk at-least-once (kerangka).
- Cache: MESI (directory-based invalidation) + LRU lokal.
- Monitoring: /metrics (Prometheus).
