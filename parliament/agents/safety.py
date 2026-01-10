from parliament.agents.llm_base import LLMFactionAgent

class SafetyAgent(LLMFactionAgent):
    def __init__(self, ideology):
        super().__init__("Safety", ideology, weight=1.5)
