import hashlib, time, json
import redis.asyncio as redis

def _md5(s: str) -> int:
    return int(hashlib.md5(s.encode()).hexdigest(), 16)

class HashRing:
    def __init__(self, nodes: list[str], vnodes: int = 64):
        self.nodes = nodes; self.vnodes = vnodes; self._rebuild({n:1 for n in nodes})
    def _rebuild(self, weights):
        self.ring = []
        for n in self.nodes:
            w = max(1, weights.get(n,1))
            for i in range(self.vnodes*w):
                self.ring.append((_md5(f"{n}:{i}"), n))
        self.ring.sort()
    def pick(self, key: str) -> str:
        h = _md5(key)
        for k, n in self.ring:
            if h <= k: return n
        return self.ring[0][1]

class DistQueue:
    def __init__(self, node_id: str, ring: HashRing, redis_url="redis://redis:6379/0"):
        self.node_id = node_id; self.ring = ring; self.redis_url = redis_url
    async def _r(self):
        return redis.from_url(self.redis_url, decode_responses=True)
    async def enqueue(self, topic: str, msg: dict):
        owner = self.ring.pick(topic); key = f"q:{topic}:{owner}"
        r = await self._r()
        await r.rpush(key, json.dumps({"msg": msg, "ts": time.time()}))
        return {"ok": True, "owner": owner}
    async def consume(self, topic: str, consumer_id: str, visibility=30):
        owner = self.ring.pick(topic); key = f"q:{topic}:{owner}"; inflight = f"inflight:{topic}:{consumer_id}"
        r = await self._r(); data = await r.lpop(key)
        if not data: return None
        now = str(time.time()); await r.hset(inflight, now, data); await r.expire(inflight, visibility)
        import json as _j; return {"handle": now, "data": _j.loads(data)}
    async def ack(self, topic: str, consumer_id: str, handle_key: str):
        r = await self._r(); await r.hdel(f"inflight:{topic}:{consumer_id}", handle_key); return {"ok": True}
