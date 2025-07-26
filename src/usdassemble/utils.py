"""USD Assembly工具函数."""

from pathlib import Path
from typing import Dict, List, Set

from rich.console import Console

console = Console()

# 支持的纹理文件扩展名
SUPPORTED_TEXTURE_EXTENSIONS = [".jpg", ".png", ".exr"]

# 纹理类型模式映射
TEXTURE_PATTERNS = {
    "base_color": ["*base_color*"],
    "metallic": ["*metallic*"],
    "roughness": ["*roughness*"],
    "normal": ["*normal*"],
    "specular": ["*specular*"],
    "scattering": ["*scattering*"],
    "diffuse": ["*diffuse*"],
    "emissive": ["*emissive*"],
    "displacement": ["*displacement*"],
    "opacity": ["*opacity*"],
    "occlusion": ["*occlusion*"],
    "reflection": ["*reflection*"],
    "refraction": ["*refraction*"],
    "sheen": ["*sheen*"],
    "transmission": ["*transmission*"],
}


class TextureValidationError(Exception):
    """纹理文件验证错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def ensure_directory(path: Path) -> None:
    """确保目录存在."""
    if path.is_file():
        path = path.parent
    path.mkdir(parents=True, exist_ok=True)


def get_template_dir() -> Path:
    """获取模板目录路径."""
    return Path(__file__).parent.parent / "template"


def find_texture_files_by_pattern(texture_dir: Path, patterns: list[str]) -> list[Path]:
    """根据模式查找纹理文件."""
    files = []
    for pattern in patterns:
        for ext in SUPPORTED_TEXTURE_EXTENSIONS:
            files.extend(texture_dir.glob(f"{pattern}{ext}"))
    return files


def validate_texture_files(texture_dir: Path, component_name: str) -> dict[str, str]:
    """验证纹理文件，严格检查重复和未知文件.

    Args:
        texture_dir: 纹理文件目录
        component_name: 组件名称

    Returns
    -------
        Dict[str, str]: 纹理类型到相对路径的映射

    Raises
    ------
        TextureValidationError: 当发现重复或未知纹理文件时
    """
    if not texture_dir.exists():
        console.print(f"[yellow]警告: 未找到纹理目录 {texture_dir}[/yellow]")
        return {}

    found_textures = {}
    used_files: set[Path] = set()

    # 检查每种纹理类型
    for texture_type, patterns in TEXTURE_PATTERNS.items():
        matched_files = find_texture_files_by_pattern(texture_dir, patterns)

        if not matched_files:
            continue

        # 严格检查：每种类型只能有一个文件
        if len(matched_files) > 1:
            file_list = [f.name for f in matched_files]
            msg = (
                f"纹理类型 '{texture_type}' 匹配到多个文件: {file_list}。"
                f"请确保每种纹理类型只有一个文件。"
            )
            raise TextureValidationError(msg)

        # 记录找到的纹理
        texture_file = matched_files[0]
        relative_path = texture_file.relative_to(texture_dir.parent).as_posix()
        found_textures[texture_type] = relative_path
        used_files.add(texture_file)

    # 检查未使用的纹理文件
    all_texture_files = set()
    for ext in SUPPORTED_TEXTURE_EXTENSIONS:
        all_texture_files.update(texture_dir.glob(f"*{ext}"))

    unused_files = all_texture_files - used_files
    if unused_files:
        unused_names = [f.name for f in unused_files]
        msg = f"发现未识别的纹理文件: {unused_names}。请移除这些文件或确保它们符合命名规范。"
        raise TextureValidationError(
            msg,
        )

    if found_textures:
        console.print(
            f"[green]✓ 为 {component_name} 验证通过的纹理: {list(found_textures.keys())}[/green]",
        )

    return found_textures
