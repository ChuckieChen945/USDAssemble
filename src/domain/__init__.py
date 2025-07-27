"""领域模型层 - 定义数据模型、枚举和异常."""

from domain.enums import ComponentType
from domain.exceptions import (
    AssemblyError,
    ComponentError,
    FileServiceError,
    MaterialXError,
    TemplateServiceError,
    TextureValidationError,
    UsdServiceError,
    VariantError,
)
from domain.models import ComponentInfo, VariantInfo

__all__ = [
    # 异常
    "AssemblyError",
    "ComponentError",
    # 模型
    "ComponentInfo",
    # 枚举
    "ComponentType",
    "FileServiceError",
    "MaterialXError",
    "TemplateServiceError",
    "TextureValidationError",
    "UsdServiceError",
    "VariantError",
    "VariantInfo",
]
