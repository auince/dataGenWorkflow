"""Base tool class for LangChain tools."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from utils.logger import get_logger


class BaseToolInput(BaseModel):
    """Input schema for BaseTool."""

    pass


class BaseTool(ABC):
    """Base class for all tools in the system."""

    name: str = Field(default="", description="Tool name")
    description: str = Field(default="", description="Tool description")

    def __init__(self, name: str = "", description: str = ""):
        """Initialize BaseTool.

        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name or self.__class__.__name__
        self.description = description
        self.logger = get_logger(f"tools.{self.name}")

    @abstractmethod
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Internal method to execute the tool. Must be implemented by subclasses."""
        pass

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool with logging.

        Returns:
            Result from _run implementation
        """
        self.logger.info(f"Running tool: {self.name}")
        try:
            result = self._run(*args, **kwargs)
            self.logger.info(f"Tool {self.name} completed successfully")
            return result
        except Exception as e:
            self.logger.error(f"Tool {self.name} failed: {e}")
            raise
