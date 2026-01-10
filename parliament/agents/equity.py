from parliament.agents.llm_base import LLMFactionAgent

class EquityAgent(LLMFactionAgent):
    def __init__(self, ideology):
        super().__init__("Equity", ideology, weight=1.0)
