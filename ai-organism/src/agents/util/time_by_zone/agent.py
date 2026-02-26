from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from shared.contracts.http import AgentContext
from agents.base.contracts import AgentSpec
from agents.base.structured_agent import StructuredAgent


class TimeByZoneInput(BaseModel):
    message: str = Field(..., description="Mensagem do usuário. Ex: 'Como está o tempo no brasil'.")


class TimeByZoneOutput(BaseModel):
    zone: str = Field(..., description="Timezone IANA (ex: America/Sao_Paulo)")
    time: str = Field(..., description="Horário atual nessa timezone em ISO 8601 (com offset)")


@tool
def get_time_by_zone(zone: str) -> dict:
    """Retorna o horário atual em uma timezone IANA. Ex: America/Sao_Paulo."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    now = datetime.now(ZoneInfo(zone))
    return {"zone": zone, "time": now.isoformat()}


class TimeByZoneAgent(StructuredAgent):
    @classmethod
    def spec(cls) -> AgentSpec:
        return AgentSpec(
            name="time_by_zone",
            version="1.0.0",
            description="Extrai timezone via LLM e usa tool get_time_by_zone para retornar a hora.",
            input_model=TimeByZoneInput,
            output_model=TimeByZoneOutput,
            timeout_s=6.0,
            tags=["utility", "time", "tools"],
        )

    def build_tools(self) -> list:
        return [get_time_by_zone]

    def user_message(self, inp: TimeByZoneInput, ctx: AgentContext) -> str:
        # Aqui a LLM deve inferir a timezone e chamar a tool.
        # Regra do seu exemplo: Brasil => America/Sao_Paulo
        return (
            "Você é um agente que responde hora atual por timezone.\n"
            "1) Identifique a timezone IANA correta a partir da mensagem do usuário.\n"
            "   - Se mencionar Brasil/Brazil, use America/Sao_Paulo.\n"
            "   - Se não for possível inferir, use UTC.\n"
            "2) Chame a ferramenta get_time_by_zone(zone) e retorne o resultado.\n\n"
            f"Mensagem do usuário: {inp.message}"
        )