import json, asyncio
import redis.asyncio as redis
from collections import OrderedDict

class LRU:
    def __init__(self, cap=256):
        self.cap = cap; self.od = OrderedDict()
    def get(self, k):
        if k in self.od: self.od.move_to_end(k); return self.od[k]
        return None
    def put(self, k, v):
        self.od[k]=v; self.od.move_to_end(k)
        if len(self.od)>self.cap: self.od.popitem(last=False)

class CacheDirectory:
    def __init__(self, redis_url="redis://redis:6379/1"): self.redis_url = redis_url
    async def _r(self): return redis.from_url(self.redis_url, decode_responses=True)
    async def read_shared(self, key: str, node: str):
        r = await self._r(); await r.sadd(f"dir:{key}:S", node); await r.delete(f"dir:{key}:E")
    async def request_exclusive(self, key: str, node: str):
        r = await self._r(); sharers = await r.smembers(f"dir:{key}:S")
        for s in sharers: await r.publish("inval", json.dumps({"key": key, "to": s}))
        await r.delete(f"dir:{key}:S"); await r.set(f"dir:{key}:E", node)

class CacheNode:
    def __init__(self, node_id: str, redis_url="redis://redis:6379/1"):
        self.node_id = node_id; self.dir = CacheDirectory(redis_url); self.lru = LRU(256)
    async def get(self, key: str, loader):
        v = self.lru.get(key)
        if v is not None: await self.dir.read_shared(key, self.node_id); return {"hit": True, "value": v}
        val = await loader(key); self.lru.put(key, val); await self.dir.read_shared(key, self.node_id)
        return {"hit": False, "value": val}
    async def put_exclusive(self, key: str, value):
        await self.dir.request_exclusive(key, self.node_id); self.lru.put(key, value); return {"ok": True}
