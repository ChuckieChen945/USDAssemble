"""USD Assembly 数据模型."""

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from domain.enums import ComponentType


@dataclass
class VariantInfo:
    """变体信息."""

    name: str
    textures: dict[str, str]  # 纹理类型 -> 相对路径
    description: str | None = None


@dataclass
class ComponentInfo:
    """组件信息."""

    name: str
    component_type: "ComponentType"
    has_geometry: bool = False
    variants: list[VariantInfo] = None
    textures: dict[str, str] = None  # 非变体纹理

    def __post_init__(self) -> None:
        """初始化后处理."""
        if self.variants is None:
            self.variants = []
        if self.textures is None:
            self.textures = {}

    @property
    def has_variants(self) -> bool:
        """是否有变体."""
        return len(self.variants) > 0

    @property
    def is_valid(self) -> bool:
        """组件是否有效（有几何体文件）."""
        return self.has_geometry
