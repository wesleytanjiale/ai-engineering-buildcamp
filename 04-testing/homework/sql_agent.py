from dataclasses import dataclass

from jaxn import JSONParserHandler, StreamingJSONParser
from pydantic_ai import Agent, AgentRunResult
from pydantic_ai.messages import FunctionToolCallEvent
from pydantic_ai.run import AgentRun
from pydantic_ai._agent_graph import UserPromptNode, ModelRequestNode, CallToolsNode
from pydantic import BaseModel, Field

from sql_tools import SQLTools

DEFAULT_INSTRUCTIONS = """
You are a database assistant.

Answer the user's question by using the available database to run queries and gather information necessary to formulate a response.

Always fetch the schema of the database before running the user's query.
""".strip()

@dataclass
class SQLAgentConfig:
    model: str = 'openai:gpt-4o-mini'
    name: str = 'query'
    instructions: str = DEFAULT_INSTRUCTIONS


def create_agent(
        config: SQLAgentConfig,
        search_tools: SQLTools
    ) -> Agent:
    tools = [search_tools.get_schema, search_tools.run_sql]
    
    search_agent = Agent(
        name=config.name,
        model=config.model,
        instructions=config.instructions,
        tools=tools
    )

    return search_agent


class NamedCallback:

    def __init__(self, agent):
        self.agent_name = agent.name

    async def print_function_calls(self, ctx, event):
        # Detect nested streams
        if hasattr(event, "__aiter__"):
            async for sub in event:
                await self.print_function_calls(ctx, sub)
            return

        if isinstance(event, FunctionToolCallEvent):
            tool_name = event.part.tool_name
            args = event.part.args
            print(f"TOOL CALL ({self.agent_name}): {tool_name}({args})")

    async def __call__(self, ctx, event):
        return await self.print_function_calls(ctx, event)


async def run_agent(
        agent: Agent,
        user_prompt: str,
        message_history=None
    ) -> AgentRunResult:
    callback = NamedCallback(agent)

    if message_history is None:
        message_history = []

    result = await agent.run(
        user_prompt,
        event_stream_handler=callback,
        message_history=message_history,
        output_type=SQLResult
    )

    return result

class SQLResult(BaseModel):
    """
    This model provides a structured answer with metadata about the response,
    including confidence, categorization, and follow-up suggestions.
    """
    # answer: str = Field(description="The main answer to the user's question")
    sql_query: str = Field(description="The SQL query that was executed")
    result_text: str = Field(description="The rows fetched after executing the query")
    row_count: str = Field(description="Number of rows fetched from the database after executing the SQL query")

    # def to_string(self):
    #     parts = []

    #     parts.append(self.answer)
    #     parts.append("")
    #     parts.append(f"found_answer: {self.found_answer}")
    #     parts.append(f"confidence: {self.confidence}")
    #     parts.append(f"confidence_explanation: {self.confidence_explanation}")
    #     parts.append(f"answer_type: {self.answer_type}")

    #     for ref in self.references:
    #         parts.append(f"reference: {ref.file_path} — {ref.explanation}")

    #     for q in self.followup_questions:
    #         parts.append(f"follow_up_question: {q}")

    #     for check in self.checks:
    #         parts.append(f"self_check: [{'+' if check.passed else '-'}] {check.rule} — {check.explanation}")

    #     return "\n".join(parts)

    # def __str__(self):
    #     return self.to_string()

class AgentStreamRunner:

    def __init__(self, agent: Agent, handler: JSONParserHandler):
        self.agent = agent
        self.handler = handler
    
    async def run(self, user_prompt: str, message_history=None):
        if message_history is None:
            message_history = []

        async with self.agent.iter(
            user_prompt,
            message_history=message_history,
            output_type=SQLResult
        ) as agent_run:
            async for node in agent_run:
                if Agent.is_user_prompt_node(node):
                    await self.process_user_node(node, agent_run)
                elif Agent.is_model_request_node(node):
                    await self.process_model_request_node(node, agent_run)
                elif Agent.is_call_tools_node(node):
                    await self.process_call_tools_node(node, agent_run)

            return agent_run.result
    
    async def process_user_node(self, node: UserPromptNode, agent_run: AgentRun):
        print(f"USER PROMPT ({self.agent.name}): {node.user_prompt}")

    async def process_model_request_node(self, node: ModelRequestNode, agent_run: AgentRun):
        args_so_far = ""

        parser = StreamingJSONParser(self.handler)

        async with node.stream(agent_run.ctx) as stream:
            async for response in stream.stream_responses():
                for part in response.parts:
                    if part.part_kind != 'tool-call':
                        continue
                    if part.tool_name != 'final_result':
                        continue

                    args_new = part.args
                    args_new_chunk = args_new[len(args_so_far):]
                    args_so_far = args_new

                    parser.parse_incremental(args_new_chunk)

    async def process_call_tools_node(self, node: CallToolsNode, agent_run: AgentRun):
        async with node.stream(agent_run.ctx) as events:
            async for event in events:
                if not isinstance(event, FunctionToolCallEvent):
                    continue

                tool_name = event.part.tool_name
                args = event.part.args
                print(f"TOOL CALL ({self.agent.name}): {tool_name}({args})")
