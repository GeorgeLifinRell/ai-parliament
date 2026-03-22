from parliament.agents.llm_base import LLMFactionAgent
from parliament.llm.client import LLMClient


class SafetyAgent(LLMFactionAgent):
    def __init__(self, ideology, llm: LLMClient | None = None):
        super().__init__("Safety", ideology, weight=1.5, llm=llm)
