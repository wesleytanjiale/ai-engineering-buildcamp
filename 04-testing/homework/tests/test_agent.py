## Usage uv run pytest 04-testing/homework/tests/test_agent.py -v -s
## -s displays all stdout, -v prints out each test name and its pass/fail status

import pytest
from tests.utils import collect_tools, run_agent_test

# @pytest.mark.asyncio
# @pytest.mark.skip(reason='testing other functionalities')
async def test_agent_runs(agent):
    user_prompt = 'How many trips had more than 5 passengers'
    result = await run_agent_test(agent, user_prompt)

    search_result = result.output
    print(f"\nresult_text: {search_result.result_text}")

    ## sql_query is a non-empty string
    assert search_result.sql_query is not None
    ## result_text contains the actual count
    assert '22413' in search_result.result_text


async def test_agent_tool_call_order(agent):
    user_prompt = 'What is the most common payment type?'
    result = await run_agent_test(agent, user_prompt)
    message_history = result.all_messages()
    tool_calls = collect_tools(message_history)

    ## first tool call should be get_schema
    assert tool_calls[0].name.lower() == 'get_schema'
    ## run_sql should also be called
    assert 'run_sql' in [call.name.lower() for call in tool_calls]
