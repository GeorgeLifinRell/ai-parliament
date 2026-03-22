from parliament.agents.llm_base import LLMFactionAgent
from parliament.llm.client import LLMClient


class EquityAgent(LLMFactionAgent):
    def __init__(self, ideology, llm: LLMClient | None = None):
        super().__init__("Equity", ideology, weight=1.0, llm=llm)
