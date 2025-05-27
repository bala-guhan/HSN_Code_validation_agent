from google.adk.agents import BaseAgent
from google.adk.events import Event, EventActions
from google.adk.agents.invocation_context import InvocationContext
from typing import AsyncGenerator

class HelloWorldAgent(BaseAgent):
    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        yield Event(
            action=EventActions.TOOL_RESULT,
            name=self.name,
            output={"message": "Hello, World!"}
        )
import asyncio
from google.adk.agents.invocation_context import InvocationContext

async def run_agent():
    agent = HelloWorldAgent(name="GreeterAgent")
    ctx = InvocationContext(state={})  # No inputs needed

    async for event in agent.run_async(ctx):
        print(event.output)

asyncio.run(run_agent())
