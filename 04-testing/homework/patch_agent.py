from pydantic_ai import Agent
from cost_tracker import capture_usage

original_run = Agent.run

async def patched_run(self, *args, **kwargs):
    result = await original_run(self, *args, **kwargs)
    model = f"{self.model.system}:{self.model.model_name}"
    capture_usage(model, result)
    return result

Agent.run = patched_run