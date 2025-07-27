"""路径相关工具函数."""

from pathlib import Path

from domain.enums import ComponentType


def get_template_dir() -> Path:
    """获取模板目录路径."""
    return Path(__file__).parent.parent / "template"


def get_component_directory_and_type(base_path: Path) -> tuple[Path, ComponentType]:
    """获取组件目录路径和类型.

    Args:
        base_path: 基础路径

    Returns
    -------
        Tuple[Path, ComponentType]: 组件目录路径和类型

    Raises
    ------
        ValueError: 当未找到支持的组件目录时
    """
    component_type = ComponentType.detect_from_path(base_path)
    if component_type is None:
        available_types = [t.directory for t in ComponentType]
        msg = f"未找到支持的组件目录 ({', '.join(available_types)}) 在路径: {base_path}"
        raise ValueError(msg)

    component_dir = base_path / component_type.directory
    return component_dir, component_type


def ensure_directory(path: Path) -> None:
    """确保目录存在.

    Args:
        path: 目录路径
    """
    # 如果路径存在且是文件，或者路径有文件扩展名（暗示这是一个文件路径）
    if (path.exists() and path.is_file()) or (not path.exists() and path.suffix):
        path = path.parent
    path.mkdir(parents=True, exist_ok=True)
