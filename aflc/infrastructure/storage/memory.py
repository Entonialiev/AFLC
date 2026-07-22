"""
In-memory storage implementation
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class MemoryStorage:
    """
    In-memory key-value storage.
    Used for testing and development.
    """

    _data: Dict[str, Any] = field(default_factory=dict)

    def save(self, key: str, value: Any) -> None:
        """Save value by key."""
        self._data[key] = value

    def load(self, key: str) -> Optional[Any]:
        """Load value by key."""
        return self._data.get(key)

    def delete(self, key: str) -> None:
        """Delete value by key."""
        if key in self._data:
            del self._data[key]

    def list_keys(self, prefix: str = "") -> List[str]:
        """List all keys with given prefix."""
        return [k for k in self._data.keys() if k.startswith(prefix)]

    def clear(self) -> None:
        """Clear all data."""
        self._data.clear()

    def count(self) -> int:
        """Return number of items."""
        return len(self._data)
