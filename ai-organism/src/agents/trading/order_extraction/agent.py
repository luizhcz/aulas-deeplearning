from __future__ import annotations

from typing import Optional
from pydantic import BaseModel

from shared.contracts.http import AgentContext
from agents.base.contracts import AgentSpec
from agents.base.structured_agent import StructuredAgent


class OrderExtractionInput(BaseModel):
    text: str


class OrderExtractionOutput(BaseModel):
    side: str
    asset: str
    quantity: int
    price: Optional[float] = None


class OrderExtractionAgent(StructuredAgent):
    @classmethod
    def spec(cls) -> AgentSpec:
        return AgentSpec(
            name="order_extraction",
            version="1.0.0",
            description="Extrai ordem (side/asset/quantity/price) do texto do usuário.",
            input_model=OrderExtractionInput,
            output_model=OrderExtractionOutput,
            timeout_s=6.0,
            tags=["trading", "nlp", "extraction"],
        )

    def user_message(self, inp: OrderExtractionInput, ctx: AgentContext) -> str:
        return (
            "Extraia uma ordem de compra/venda do texto. Retorne JSON estrito com:\n"
            "side: BUY|SELL\nasset: string (ticker)\nquantity: int\nprice: float|null\n\n"
            f"TEXTO:\n{inp.text}"
        )