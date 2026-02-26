from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel

from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy

from shared.contracts.http import AgentContext


class StructuredAgent:
    """
    Base para agentes que retornam Pydantic via ToolStrategy.

    Importante: diferentes versões do LangChain podem retornar o resultado em chaves diferentes.
    Esta base tenta, na ordem:
      1) structured_response
      2) output
      3) messages (última mensagem)

    Se ctx.verbose=True, guarda informações adicionais em ctx.vars["_debug"].
    """

    def __init__(self, model_provider):
        self._provider = model_provider
        self._agent = None

    @classmethod
    def spec(cls):
        raise NotImplementedError

    def build_tools(self) -> list:
        return []

    def user_message(self, inp: BaseModel, ctx: AgentContext) -> str:
        raise NotImplementedError

    def _lazy_init(self):
        if self._agent is not None:
            return
        sp = self.spec()
        llm = self._provider.get_chat_model()
        self._agent = create_agent(
            model=llm,
            tools=self.build_tools(),
            response_format=ToolStrategy(sp.output_model),
        )

    def _extract_structured(self, result: Any) -> Any:
        if isinstance(result, dict) and "structured_response" in result:
            return result["structured_response"]

        if isinstance(result, dict) and "output" in result and result["output"] is not None:
            return result["output"]

        if isinstance(result, dict) and "messages" in result and result["messages"]:
            last = result["messages"][-1]
            content = getattr(last, "content", None) or (last.get("content") if isinstance(last, dict) else None)
            return {"text": content}

        return None

    def _truncate(self, x: Any, limit: int = 4000) -> Any:
        try:
            s = str(x)
            return s[:limit] + ("…(truncated)" if len(s) > limit else "")
        except Exception:
            return "<unserializable>"

    async def run(self, inp: BaseModel, ctx: AgentContext) -> BaseModel:
        self._lazy_init()
        sp = self.spec()

        msg = self.user_message(inp, ctx)
        result = await self._agent.ainvoke({
            "messages": [{"role": "user", "content": msg}]
        })

        # ✅ verbose: guarda dados úteis para debug
        if getattr(ctx, "verbose", False):
            ctx.vars.setdefault("_debug", {})
            ctx.vars["_debug"].update({
                "user_message": self._truncate(msg),
                "raw_result": self._truncate(result),
            })

        structured = self._extract_structured(result)
        if structured is None:
            raise KeyError("Agent result missing structured output (structured_response/output/messages)")

        if isinstance(structured, BaseModel):
            return structured

        if isinstance(structured, dict):
            return sp.output_model.model_validate(structured)

        return sp.output_model.model_validate(structured)