from abc import ABC, abstractmethod
from parliament.core.bill import Bill
from parliament.core.amendment import Amendment
from parliament.core.vote import Vote


class BaseFactionAgent(ABC):
    """
    Base class for all faction agents.

    Agents:
    - have ideology
    - act only when invoked
    - cannot mutate state
    """

    def __init__(self, name: str, ideology: dict):
        self.name = name
        self.ideology = ideology

    @abstractmethod
    def statement(self, bill: Bill) -> str:
        pass

    @abstractmethod
    def propose_amendments(self, bill: Bill) -> list[Amendment]:
        pass

    @abstractmethod
    def vote(self, bill: Bill, amendments: list[Amendment]) -> Vote:
        pass
