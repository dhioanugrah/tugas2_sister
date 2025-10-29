import os
class Config:
    NODE_ID = os.getenv("NODE_ID", "node1")
    PEERS = os.getenv("PEERS", "node1,node2,node3").split(",")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    HTTP_BIND = os.getenv("HTTP_BIND", "0.0.0.0")
    HTTP_PORT = int(os.getenv("HTTP_PORT", "8080"))
