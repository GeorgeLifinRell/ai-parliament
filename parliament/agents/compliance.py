from parliament.agents.llm_base import LLMFactionAgent

class ComplianceAgent(LLMFactionAgent):
    def __init__(self, ideology):
        super().__init__("Compliance", ideology, weight=1.2)
