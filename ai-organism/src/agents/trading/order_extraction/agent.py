from __future__ import annotations
from typing import Optional
from enum import Enum
from pydantic import BaseModel

from shared.contracts.http import AgentContext
from agents.base.contracts import AgentSpec
from agents.base.structured_agent import StructuredAgent

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderExtractionInput(BaseModel):
    text: str

class OrderExtractionOutput(BaseModel):
    asset_name: Optional[str] = None
    quantity: Optional[int] = None
    side: Optional[OrderSide] = None
    price: Optional[float] = None

class OrderExtractionAgent(StructuredAgent):
    @classmethod
    def spec(cls) -> AgentSpec:
        return AgentSpec(
            name="order_extraction",
            version="1.0.0",
            description="Extrai ordem (ativo, qty, side, preço) do texto do usuário.",
            input_model=OrderExtractionInput,
            output_model=OrderExtractionOutput,
            timeout_s=6.0,
            tags=["trading", "extraction", "structured_output"],
        )

    def user_message(self, inp: OrderExtractionInput, ctx: AgentContext) -> str:
        return (
            "Extraia uma ordem de trading.\n"
            "Regras:\n"
            "- Não invente ticker.\n"
            "- side deve ser BUY ou SELL.\n"
            "- Se não houver preço, use null.\n\n"
            f"Texto: {inp.text}"
        )