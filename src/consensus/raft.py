# src/consensus/raft.py
import asyncio
from typing import Any, Dict, Optional, Callable

class RaftNode:
    def __init__(self, node_id: str, peers: list[str]):
        self.id = node_id
        self.peers = [p for p in peers if p != node_id]
        self.state = "leader" if node_id == "node1" else "follower"
        self.apply_entry_cb: Optional[Callable[[Dict[str,Any]], asyncio.Future]] = None

    def is_leader(self) -> bool:
        return self.state == "leader"

    async def append_and_replicate(self, cmd: Dict[str,Any]):
        result = None
        if self.apply_entry_cb:
            result = await self.apply_entry_cb(cmd)
        # ACK commit + bawa hasil apply (granted/wait/deadlock)
        return {"ok": True, "committed": True, "result": result}
