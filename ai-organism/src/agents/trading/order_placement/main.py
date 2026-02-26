import os
from agents.base.model_provider import ModelProvider, ModelConfig

from agents.trading.order_placement.agent import OrderPlacementAgent
print("LOADED OrderPlacementAgent FROM:", OrderPlacementAgent.__module__, OrderPlacementAgent)

from agent_host.application.host_factory import build_agent_http_host

provider = ModelProvider(ModelConfig(
    provider="ollama",
    model=os.getenv("OLLAMA_MODEL", "llama3.1:8b"),
    temperature=0.0,
    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
))

agent = OrderPlacementAgent(provider)

app = build_agent_http_host(
    agent,
    registry_url=os.getenv("REGISTRY_URL"),
    agent_base_url=os.getenv("AGENT_BASE_URL"),
    heartbeat_interval_s=int(os.getenv("HEARTBEAT_INTERVAL_S", "10")),
)