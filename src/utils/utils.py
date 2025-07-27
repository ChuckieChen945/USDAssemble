"""USD Assembly工具函数."""

from pathlib import Path

from rich.console import Console

from domain.enums import ComponentType
from domain.exceptions import TextureValidationError, VariantError
from domain.models import ComponentInfo, VariantInfo

console = Console()

# 支持的纹理文件扩展名
SUPPORTED_TEXTURE_EXTENSIONS = [".jpg", ".png", ".exr", ".tif", ".tiff"]

# 纹理类型模式映射
# 每种纹理类型只强制使用一种命名模式，不要使用多种模式，避免混乱
TEXTURE_PATTERNS = {
    "base_color": ["*base_color*"],
    "metalness": ["*metalness*"],
    "roughness": ["*roughness*"],
    "normal": ["*normal*"],
    "specular": ["*specular*"],
    "scattering": ["*scattering*"],
    "emissive": ["*emissive*"],
    "displacement": ["*displacement*"],
    "opacity": ["*opacity*"],
    "occlusion": ["*occlusion*"],
    "reflection": ["*reflection*"],
    "refraction": ["*refraction*"],
    "sheen": ["*sheen*"],
    "transmission": ["*transmission*"],
}


def find_texture_files_by_pattern(texture_dir: Path, patterns: list[str]) -> list[Path]:
    """根据模式查找纹理文件."""
    files = []
    for pattern in patterns:
        for ext in SUPPORTED_TEXTURE_EXTENSIONS:
            files.extend(texture_dir.glob(f"{pattern}{ext}"))
    return files


def _validate_single_texture_set(
    texture_dir: Path,
    context: str = "",
) -> dict[str, str]:
    """验证单套纹理文件.

    Args:
        texture_dir: 纹理文件目录
        context: 上下文信息（用于错误提示）

    Returns
    -------
        Dict[str, str]: 纹理类型到相对路径的映射

    Raises
    ------
        TextureValidationError: 当发现重复或未知纹理文件时
    """
    if not texture_dir.exists():
        return {}

    found_textures = {}
    used_files: set[Path] = set()
    context_prefix = f"{context} " if context else ""

    # 检查每种纹理类型
    for texture_type, patterns in TEXTURE_PATTERNS.items():
        matched_files = find_texture_files_by_pattern(texture_dir, patterns)

        if not matched_files:
            continue

        # 严格检查：每种类型只能有一个文件
        if len(matched_files) > 1:
            file_list = [f.name for f in matched_files]
            msg = (
                f"{context_prefix}纹理类型 '{texture_type}' 匹配到多个文件: {file_list}。"
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
        msg = (
            f"{context_prefix}发现未识别的纹理文件: {unused_names}。"
            f"请移除这些文件或确保它们符合命名规范。"
        )
        raise TextureValidationError(msg)

    return found_textures


def detect_variants(texture_dir: Path, component_name: str) -> list[VariantInfo]:
    """检测变体信息.

    如果纹理目录中存在子目录，则将每个子目录视为一个变体。

    Args:
        texture_dir: 纹理文件目录
        component_name: 组件名称

    Returns
    -------
        List[VariantInfo]: 检测到的变体列表

    Raises
    ------
        VariantError: 当变体检测失败时
    """
    if not texture_dir.exists():
        return []

    variants = []
    variant_dirs = [d for d in texture_dir.iterdir() if d.is_dir()]

    if not variant_dirs:
        return []

    console.print(f"[blue]检测到 {len(variant_dirs)} 个变体目录[/blue]")

    for variant_dir in sorted(variant_dirs):
        variant_name = variant_dir.name

        try:
            # 验证变体的纹理文件
            variant_textures = _validate_single_texture_set(
                variant_dir,
                f"变体 '{variant_name}'",
            )

            variant_info = VariantInfo(
                name=variant_name,
                textures=variant_textures,
                description=f"{component_name} 的 {variant_name} 变体",
            )
            variants.append(variant_info)

            console.print(
                f"[green]✓ 变体 '{variant_name}': {len(variant_textures)} 个纹理[/green]",
            )

        except TextureValidationError as e:
            msg = f"变体 '{variant_name}' 验证失败: {e}"
            raise VariantError(msg) from e

    return variants


def validate_texture_files(texture_dir: Path, component_name: str) -> dict[str, str]:
    """验证纹理文件，支持变体检测.

    Args:
        texture_dir: 纹理文件目录
        component_name: 组件名称

    Returns
    -------
        Dict[str, str]: 纹理类型到相对路径的映射（仅返回直接纹理，变体需单独处理）

    Raises
    ------
        TextureValidationError: 当发现重复或未知纹理文件时
        VariantError: 当变体处理失败时
    """
    if not texture_dir.exists():
        console.print(f"[yellow]警告: 未找到纹理目录 {texture_dir}[/yellow]")
        return {}

    # 检测变体
    variants = detect_variants(texture_dir, component_name)

    # 如果有变体，则只处理变体，忽略根目录的纹理文件
    if variants:
        console.print(
            f"[blue]组件 '{component_name}' 使用变体模式，共 {len(variants)} 个变体[/blue]",
        )
        # 返回空字典，因为纹理都在变体中
        return {}

    # 没有变体，验证根目录的纹理文件
    found_textures = _validate_single_texture_set(texture_dir)

    if found_textures:
        console.print(
            f"[green]✓ 为 {component_name} 验证通过的纹理: {list(found_textures.keys())}[/green]",
        )

    return found_textures


def scan_component_info(component_path: Path, component_type: ComponentType) -> ComponentInfo:
    """扫描组件信息，包括变体.

    Args:
        component_path: 组件路径
        component_type: 组件类型

    Returns
    -------
        ComponentInfo: 组件信息

    Raises
    ------
        TextureValidationError: 纹理验证失败
        VariantError: 变体处理失败
    """
    component_name = component_path.name

    # 检查几何体文件
    geom_file = component_path / f"{component_name}_geom.usd"
    has_geometry = geom_file.exists()

    # 检查纹理目录
    texture_dir = component_path / "textures"

    variants = []
    textures = {}

    if texture_dir.exists():
        # 检测变体
        variants = detect_variants(texture_dir, component_name)

        # 如果没有变体，验证直接纹理
        if not variants:
            textures = _validate_single_texture_set(texture_dir)

    return ComponentInfo(
        name=component_name,
        component_type=component_type,
        has_geometry=has_geometry,
        variants=variants,
        textures=textures,
    )
