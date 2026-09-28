import asyncio

import pytest

agents = pytest.importorskip("agents")

from jevals import Eval, Gate, MockBackend, Result  # noqa: E402
from jevals.integrations.openai_agents import guard_tools  # noqa: E402


class Deny(Eval):
    name = "deny"

    def pre(self, s):
        return Result(score=0.0, passed=False, action="block")


def _deny_gate():
    return Gate(Deny(), backend=MockBackend())


def test_guard_tools_keeps_tool_settings():
    # Wrapping a tool must not re-enable a disabled tool or turn off the SDK's human approval step.
    @agents.function_tool
    def issue_refund(order_id: str) -> str:
        """Refund an order."""
        return "refunded"

    issue_refund.is_enabled = False
    if hasattr(issue_refund, "needs_approval"):  # added in later SDK versions
        issue_refund.needs_approval = True
    [wrapped] = guard_tools([issue_refund], before=_deny_gate())
    assert wrapped.is_enabled is False
    assert getattr(wrapped, "needs_approval", True) is True
    assert wrapped.params_json_schema == issue_refund.params_json_schema
    out = asyncio.run(wrapped.on_invoke_tool(None, '{"order_id": "A1"}'))
    assert out.startswith("Tool call blocked by policy")


def test_guard_tools_wraps_function_tool_subclass():
    class LookupTool(agents.FunctionTool):
        def __init__(self):
            async def run(ctx, args):
                return "found"

            super().__init__(
                name="lookup",
                description="Look up an order.",
                params_json_schema={"type": "object", "properties": {}},
                on_invoke_tool=run,
            )

    [wrapped] = guard_tools([LookupTool()], before=_deny_gate())
    assert isinstance(wrapped, LookupTool)
    assert asyncio.run(wrapped.on_invoke_tool(None, "{}")).startswith("Tool call blocked by policy")
