import os, asyncio
import httpx
from shared.observability.logging import get_logger

log = get_logger("agent.heartbeat")

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:9100")
AGENT_NAME = os.getenv("AGENT_NAME")         # ex: order_extraction
AGENT_VERSION = os.getenv("AGENT_VERSION")   # ex: 1.0.0
AGENT_BASE_URL = os.getenv("AGENT_BASE_URL") # ex: http://localhost:9001

async def heartbeat_loop():
    if not (AGENT_NAME and AGENT_VERSION and AGENT_BASE_URL):
        log.info("heartbeat disabled (missing env vars)")
        return

    async with httpx.AsyncClient(timeout=3.0) as client:
        while True:
            try:
                await client.post(f"{REGISTRY_URL}/heartbeat", json={
                    "name": AGENT_NAME,
                    "version": AGENT_VERSION,
                    "base_url": AGENT_BASE_URL,
                    "meta": {"kind": "agent-http"}
                })
            except Exception:
                log.exception("heartbeat failed")
            await asyncio.sleep(10)

# Para rodar junto do uvicorn, use lifespan events no FastAPI (próximo passo).