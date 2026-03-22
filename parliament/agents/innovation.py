from parliament.agents.llm_base import LLMFactionAgent
from parliament.llm.client import LLMClient


class InnovationAgent(LLMFactionAgent):
    def __init__(self, ideology, llm: LLMClient | None = None):
        super().__init__("Innovation", ideology, weight=0.8, llm=llm)
