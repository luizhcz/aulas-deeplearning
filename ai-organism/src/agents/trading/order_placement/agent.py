from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel
from langchain_core.tools import tool

from shared.contracts.http import AgentContext
from agents.base.contracts import AgentSpec
from agents.base.structured_agent import StructuredAgent

class OrderPlacementInput(BaseModel):
    side: str
    asset: str
    quantity: int
    price: Optional[float] = None

class OrderPlacementOutput(BaseModel):
    status: str
    order_id: str
    received: Dict[str, Any]

@tool
def place_order(side: str, asset: str, quantity: int, price: float | None = None) -> dict:
    """Envia uma ordem para a corretora (mock). Retorna status, order_id e payload recebido."""
    return {
        "status": "ACCEPTED",
        "order_id": "ORD-123456",
        "received": {"side": side, "asset": asset, "quantity": quantity, "price": price},
    }

class OrderPlacementAgent(StructuredAgent):
    @classmethod
    def spec(cls) -> AgentSpec:
        return AgentSpec(
            name="order_placement",
            version="1.0.0",
            description="Executa boleta via tool place_order.",
            input_model=OrderPlacementInput,
            output_model=OrderPlacementOutput,
            timeout_s=6.0,
            tags=["trading", "execution", "tools"],
        )

    def build_tools(self) -> list:
        return [place_order]

    def user_message(self, inp: OrderPlacementInput, ctx: AgentContext) -> str:
        print("DEBUG user_message CALLED", inp, ctx.session_id)
        return (
            "Use a ferramenta place_order com os parâmetros fornecidos.\n"
            f"side={inp.side}\nasset={inp.asset}\nquantity={inp.quantity}\nprice={inp.price}"
        )