import os
from smolagents import DuckDuckGoSearchTool, InferenceClientModel, ToolCallingAgent


def run_web_only(question: str) -> str:
    model = InferenceClientModel(
        model_id="Qwen/Qwen2.5-72B-Instruct",
        token=os.environ["HF_TOKEN"],
    )
    agent = ToolCallingAgent(
        tools=[DuckDuckGoSearchTool()],
        model=model,
    )
    return agent.run(question)
