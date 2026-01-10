from parliament.agents.llm_base import LLMFactionAgent

class EfficiencyAgent(LLMFactionAgent):
    def __init__(self, ideology):
        super().__init__("Efficiency", ideology, weight=1.0)
