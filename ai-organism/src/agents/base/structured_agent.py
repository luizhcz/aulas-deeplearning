from __future__ import annotations

from typing import Any, Optional
from pydantic import BaseModel

from langchain.agents import create_agent
from langchain_core.tools import StructuredTool

from shared.contracts.http import AgentContext
from shared.observability.metrics import TOOL_CALLS_TOTAL
from shared.observability.audit import audit_event


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

    def _wrap_tools(self, tools: list) -> list:
        """Wrap tools to emit metrics + audit (without leaking payload unless DEBUG=true)."""
        sp = self.spec()
        wrapped = []

        for t in tools:
            # LangChain tools usually are StructuredTool (from @tool)
            if isinstance(t, StructuredTool):
                inner_tool = t
                tool_name = inner_tool.name

                def _make_sync(inner: StructuredTool):
                    def _sync(**kwargs):
                        TOOL_CALLS_TOTAL.labels(agent=sp.name, tool=inner.name, status="started").inc()
                        audit_event(
                            event="tool.call",
                            action=inner.name,
                            outcome="started",
                            object_={"agent": sp.name, "version": sp.version, "tool": inner.name},
                            sensitive_request={"args": kwargs},
                        )
                        try:
                            res = inner.func(**kwargs)
                            TOOL_CALLS_TOTAL.labels(agent=sp.name, tool=inner.name, status="ok").inc()
                            audit_event(
                                event="tool.call",
                                action=inner.name,
                                outcome="success",
                                object_={"agent": sp.name, "version": sp.version, "tool": inner.name},
                                sensitive_response={"result": res},
                            )
                            return res
                        except Exception as e:
                            TOOL_CALLS_TOTAL.labels(agent=sp.name, tool=inner.name, status="error").inc()
                            audit_event(
                                event="tool.call",
                                action=inner.name,
                                outcome="error",
                                object_={"agent": sp.name, "version": sp.version, "tool": inner.name},
                                error={"message": repr(e)},
                            )
                            raise

                    return _sync

                def _make_async(inner: StructuredTool):
                    async def _async(**kwargs):
                        TOOL_CALLS_TOTAL.labels(agent=sp.name, tool=inner.name, status="started").inc()
                        audit_event(
                            event="tool.call",
                            action=inner.name,
                            outcome="started",
                            object_={"agent": sp.name, "version": sp.version, "tool": inner.name},
                            sensitive_request={"args": kwargs},
                        )
                        try:
                            if inner.coroutine is not None:
                                res = await inner.coroutine(**kwargs)
                            else:
                                # fallback to sync
                                res = inner.func(**kwargs)
                            TOOL_CALLS_TOTAL.labels(agent=sp.name, tool=inner.name, status="ok").inc()
                            audit_event(
                                event="tool.call",
                                action=inner.name,
                                outcome="success",
                                object_={"agent": sp.name, "version": sp.version, "tool": inner.name},
                                sensitive_response={"result": res},
                            )
                            return res
                        except Exception as e:
                            TOOL_CALLS_TOTAL.labels(agent=sp.name, tool=inner.name, status="error").inc()
                            audit_event(
                                event="tool.call",
                                action=inner.name,
                                outcome="error",
                                object_={"agent": sp.name, "version": sp.version, "tool": inner.name},
                                error={"message": repr(e)},
                            )
                            raise

                    return _async

                wrapped.append(
                    StructuredTool.from_function(
                        name=inner_tool.name,
                        description=inner_tool.description,
                        args_schema=inner_tool.args_schema,
                        func=_make_sync(inner_tool),
                        coroutine=_make_async(inner_tool),
                    )
                )
            else:
                wrapped.append(t)

        return wrapped

    def user_message(self, inp: BaseModel, ctx: AgentContext) -> str:
        raise NotImplementedError

    def _lazy_init(self):
        if self._agent is not None:
            return
        sp = self.spec()
        llm = self._provider.get_chat_model()
        self._agent = create_agent(
            model=llm,
            tools=self._wrap_tools(self.build_tools()),
            response_format=sp.output_model,
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