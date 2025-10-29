from typing import Dict, Set, Tuple, Optional
class LockTable:
    def __init__(self):
        self.table: Dict[str, Tuple[Set[str], Optional[str]]] = {}
        self.wfg: Dict[str, Set[str]] = {}
    async def apply_cmd(self, cmd):
        t = cmd.get("type")
        if t == "acquire":
            return await self._acquire(cmd["key"], cmd["client_id"], cmd["mode"])
        elif t == "release":
            return await self._release(cmd["key"], cmd["client_id"])
        return {"ok": False, "err": "unknown-cmd"}
    async def _acquire(self, key: str, cid: str, mode: str):
        holders, cur = self.table.get(key, (set(), None))
        if cur is None:
            self.table[key] = ({cid}, mode); return {"ok": True, "granted": True}
        if mode == "S" and cur == "S":
            holders.add(cid); self.table[key]=(holders,"S"); return {"ok": True, "granted": True}
        if len(holders)==0:
            self.table[key]=({cid}, mode); return {"ok": True, "granted": True}
        self.wfg.setdefault(cid, set()).update(holders)
        if self._detect_cycle(): return {"ok": False, "err": "deadlock"}
        return {"ok": False, "err": "wait"}
    async def _release(self, key: str, cid: str):
        if key not in self.table: return {"ok": True}
        holders, mode = self.table[key]
        holders.discard(cid)
        if not holders: del self.table[key]
        self.wfg.pop(cid, None)
        for k in list(self.wfg.keys()): self.wfg[k].discard(cid)
        return {"ok": True}
    def _detect_cycle(self) -> bool:
        visited, stack = set(), set()
        def dfs(u):
            visited.add(u); stack.add(u)
            for v in self.wfg.get(u, set()):
                if v not in visited and dfs(v): return True
                if v in stack: return True
            stack.remove(u); return False
        for n in list(self.wfg.keys()):
            if n not in visited and dfs(n): return True
        return False
