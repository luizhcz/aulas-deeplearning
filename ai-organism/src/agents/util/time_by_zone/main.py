import os

from agents.base.model_provider import ModelProvider, ModelConfig
from agent_host.application.host_factory import build_agent_http_host
from agents.util.time_by_zone.agent import TimeByZoneAgent


PROVIDER = os.getenv("MODEL_PROVIDER", "ollama").strip().lower()
MODEL_NAME = os.getenv("MODEL_NAME") or os.getenv("OLLAMA_MODEL", "llama3.1:8b")

provider = ModelProvider(ModelConfig(
    provider=PROVIDER,  # "ollama" | "openai"
    model=MODEL_NAME,
    temperature=0.0,
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
    openai_base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY"),
))

agent = TimeByZoneAgent(provider)

app = build_agent_http_host(
    agent,
    registry_url=os.getenv("REGISTRY_URL"),
    agent_base_url=os.getenv("AGENT_BASE_URL"),
    heartbeat_interval_s=int(os.getenv("HEARTBEAT_INTERVAL_S", "10")),
)