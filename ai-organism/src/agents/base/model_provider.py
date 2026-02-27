from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Literal
import os

from langchain_ollama import ChatOllama

# LangChain OpenAI (pacote separado). Instale se necessário:
#   pip install langchain-openai
from langchain_openai import ChatOpenAI


Provider = Literal["ollama", "openai"]


@dataclass(frozen=True)
class ModelConfig:
    provider: Provider = "ollama"

    # Nome do modelo (Ollama: "llama3.1:8b"; OpenAI: "gpt-4o-mini", "gpt-4.1-mini", etc.)
    model: str = "llama3.1:8b"

    temperature: float = 0.0

    # Ollama
    base_url: Optional[str] = None  # ex.: http://localhost:11434

    # OpenAI
    api_key: Optional[str] = None

    # Se você usa endpoint compatível (Azure OpenAI / gateway), pode mapear via env/base_url,
    # mas aqui deixo explícito para evitar confusão:
    openai_base_url: Optional[str] = None  # opcional (env OPENAI_BASE_URL)


class ModelProvider:
    def __init__(self, cfg: ModelConfig):
        self.cfg = cfg

    def get_chat_model(self):
        provider = self.cfg.provider.lower()

        if provider == "ollama":
            return ChatOllama(
                model=self.cfg.model,
                temperature=self.cfg.temperature,
                base_url=self.cfg.base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            )

        if provider == "openai":
            # Resolve credenciais via config ou env
            api_key = self.cfg.api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError(
                    "OpenAI provider requer api_key ou env OPENAI_API_KEY."
                )

            return ChatOpenAI(
                model=self.cfg.model,
                temperature=self.cfg.temperature,
                api_key=api_key,
                base_url=self.cfg.openai_base_url or os.getenv("OPENAI_BASE_URL"),
            )

        raise ValueError(f"Unsupported provider: {self.cfg.provider}")