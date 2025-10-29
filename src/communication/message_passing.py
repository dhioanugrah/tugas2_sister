import asyncio, json
from aiohttp import web
from src.utils.config import Config
from src.utils.metrics import metrics_app_handler, locks_acquire_total, queue_enqueued_total, queue_consume_latency
from src.consensus.raft import RaftNode
from src.nodes.lock_manager import LockTable
from src.nodes.queue_node import HashRing, DistQueue
from src.nodes.cache_node import CacheNode

cfg = Config()
lock_table = LockTable()
raft = RaftNode(cfg.NODE_ID, cfg.PEERS)
raft.apply_entry_cb = lock_table.apply_cmd
hash_ring = HashRing(cfg.PEERS)
queue = DistQueue(cfg.NODE_ID, hash_ring, redis_url=cfg.REDIS_URL)
cache = CacheNode(cfg.NODE_ID)

async def health(request): return web.json_response({"ok":True, "node": cfg.NODE_ID, "leader": raft.is_leader()})
async def acquire_lock(request):
    body = await request.json()
    if not raft.is_leader(): return web.json_response({"ok":False,"err":"not-leader"}, status=409)
    res = await raft.append_and_replicate({"type":"acquire", **body})
    locks_acquire_total.labels(mode=body.get("mode","?"), result="ok" if res.get("committed") else "fail").inc()
    return web.json_response(res)
async def release_lock(request):
    body = await request.json()
    if not raft.is_leader(): return web.json_response({"ok":False,"err":"not-leader"}, status=409)
    res = await raft.append_and_replicate({"type":"release", **body})
    return web.json_response(res)
async def q_enqueue(request):
    body = await request.json(); topic = body.get("topic","default")
    queue_enqueued_total.labels(topic=topic).inc(); res = await queue.enqueue(topic, body.get("msg", {}))
    return web.json_response(res)
async def q_consume(request):
    body = await request.json(); topic = body.get("topic","default")
    with queue_consume_latency.labels(topic=topic).time(): res = await queue.consume(topic, body.get("consumer_id","c1"))
    return web.json_response(res or {"data": None})
async def cache_get(request):
    key = request.query.get("key","k1")
    async def dummy_loader(k): await asyncio.sleep(0.01); return f"value_of_{k}"
    res = await cache.get(key, dummy_loader); return web.json_response(res)
async def cache_put(request):
    body = await request.json(); res = await cache.put_exclusive(body["key"], body["value"]); return web.json_response(res)

def create_app():
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_post("/locks/acquire", acquire_lock)
    app.router.add_post("/locks/release", release_lock)
    app.router.add_post("/queue/enqueue", q_enqueue)
    app.router.add_post("/queue/consume", q_consume)
    app.router.add_get("/cache/get", cache_get)
    app.router.add_post("/cache/put", cache_put)
    app.router.add_get("/metrics", metrics_app_handler)
    return app

if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host=cfg.HTTP_BIND, port=cfg.HTTP_PORT)
