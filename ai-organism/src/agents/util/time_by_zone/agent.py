from __future__ import annotations

from pydantic import BaseModel
from langchain_core.tools import tool
from datetime import datetime
import pytz

from shared.contracts.http import AgentContext
from agents.base.contracts import AgentSpec
from agents.base.structured_agent import StructuredAgent

class TimeByZoneInput(BaseModel):
    timezone: str

class TimeByZoneOutput(BaseModel):
    timezone: str
    now: str

@tool
def get_time_by_zone(timezone: str) -> dict:
    """Retorna o horário atual na timezone informada (IANA)."""
    tz = pytz.timezone(timezone)
    now = datetime.now(tz).isoformat()
    return {"timezone": timezone, "now": now}

class TimeByZoneAgent(StructuredAgent):
    @classmethod
    def spec(cls) -> AgentSpec:
        return AgentSpec(
            name="time_by_zone",
            version="1.0.0",
            description="Retorna o horário atual em uma timezone.",
            input_model=TimeByZoneInput,
            output_model=TimeByZoneOutput,
            timeout_s=6.0,
            tags=["utility", "time", "tools"],
        )

    def build_tools(self) -> list:
        return [get_time_by_zone]

    def user_message(self, inp: TimeByZoneInput, ctx: AgentContext) -> str:
        return (
            "Use a ferramenta get_time_by_zone para obter o horário atual.\n"
            f"timezone={inp.timezone}"
        )