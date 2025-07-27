"""USD Assembly 枚举定义."""

from enum import Enum
from pathlib import Path
from typing import Optional


class ComponentType(Enum):
    """组件类型枚举."""

    COMPONENT = ("component", "components")
    SUBCOMPONENT = ("subcomponent", "subcomponents")

    def __init__(self, kind: str, directory: str) -> None:
        self.kind = kind
        self.directory = directory

    @classmethod
    def from_directory(cls, directory_name: str) -> "ComponentType":
        """从目录名获取组件类型."""
        for component_type in cls:
            if component_type.directory == directory_name:
                return component_type
        msg = f"不支持的组件目录类型: {directory_name}"
        raise ValueError(msg)

    @classmethod
    def detect_from_path(cls, base_path: Path) -> Optional["ComponentType"]:
        """从基础路径检测组件类型."""
        for component_type in cls:
            if (base_path / component_type.directory).exists():
                return component_type
        return None
