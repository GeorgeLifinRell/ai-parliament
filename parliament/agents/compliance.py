from parliament.agents.llm_base import LLMFactionAgent
from parliament.llm.client import LLMClient


class ComplianceAgent(LLMFactionAgent):
    def __init__(self, ideology, llm: LLMClient | None = None):
        super().__init__("Compliance", ideology, weight=1.2, llm=llm)
