from parliament.agents.llm_base import LLMFactionAgent

class InnovationAgent(LLMFactionAgent):
    def __init__(self, ideology):
        super().__init__("Innovation", ideology, weight=0.8)
