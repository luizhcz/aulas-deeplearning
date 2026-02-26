from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import os
from langchain_ollama import ChatOllama

@dataclass
class ModelConfig:
    provider: str = "ollama"
    model: str = "llama3.1:8b"
    temperature: float = 0.0
    base_url: Optional[str] = None

class ModelProvider:
    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg

    def get_chat_model(self):
        if self.cfg.provider == "ollama":
            return ChatOllama(
                model=self.cfg.model,
                temperature=self.cfg.temperature,
                base_url=self.cfg.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            )
        raise ValueError(f"Unsupported provider: {self.cfg.provider}")