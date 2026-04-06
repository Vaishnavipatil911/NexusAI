"""
Tool Registry — central store for all registered tools.

Usage:
    @register_tool(name="weather", category="utility_tools", ...)
    class WeatherTool(BaseTool): ...

    registry = get_registry()
    tool = registry.get("weather")
    result = tool.run(city="London")
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolMeta:
    name: str
    display_name: str
    category: str
    description: str
    keywords: List[str]
    input_type: str          # "chat" | "form" | "file"
    cls: Any = None


class ToolRegistry:
    """Singleton registry that maps tool names → metadata + class."""

    _instance: Optional["ToolRegistry"] = None

    def __init__(self):
        self._tools: Dict[str, ToolMeta] = {}

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, meta: ToolMeta) -> None:
        self._tools[meta.name] = meta
        logger.debug(f"Registered tool: {meta.name} ({meta.category})")

    def get(self, name: str) -> Optional[ToolMeta]:
        return self._tools.get(name)

    def all(self) -> List[ToolMeta]:
        return list(self._tools.values())

    def by_category(self, category: str) -> List[ToolMeta]:
        return [t for t in self._tools.values() if t.category == category]

    def names(self) -> List[str]:
        return list(self._tools.keys())

    def categories(self) -> List[str]:
        return sorted(set(t.category for t in self._tools.values()))


# ── Decorator ────────────────────────────────────────────────────────────────

def register_tool(
    name: str,
    display_name: str,
    category: str,
    description: str,
    keywords: List[str],
    input_type: str = "chat",
):
    """Class decorator — registers a BaseTool subclass into the global registry."""
    def decorator(cls):
        meta = ToolMeta(
            name=name,
            display_name=display_name,
            category=category,
            description=description,
            keywords=keywords,
            input_type=input_type,
            cls=cls,
        )
        ToolRegistry.get_instance().register(meta)
        cls._tool_name = name
        return cls
    return decorator


def get_registry() -> ToolRegistry:
    return ToolRegistry.get_instance()


# ── Base class every tool inherits ───────────────────────────────────────────

class BaseTool:
    """All tools must subclass this and implement `run(**kwargs) -> dict`."""

    def run(self, **kwargs) -> dict:
        raise NotImplementedError

    def safe_run(self, **kwargs) -> dict:
        try:
            return self.run(**kwargs)
        except Exception as e:
            logger.error(f"Tool error in {self.__class__.__name__}: {e}")
            return {"success": False, "result": f"❌ Tool error: {str(e)}"}