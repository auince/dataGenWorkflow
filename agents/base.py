from abc import ABC, abstractmethod
from typing import TypeVar, Generic, TypedDict

T = TypeVar("T", bound=TypedDict)


class BaseAgent(ABC, Generic[T]):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def process(self, state: T) -> T:
        """Process the state and return updated state"""
        pass
