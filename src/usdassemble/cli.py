# TODO：美化所有输出

"""USD Asset Assembly Script.

使用 Pixar OpenUSD API 装配棋盘资产
"""

from pathlib import Path
from string import Template

import typer
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, Vt
from rich import print as rprint
from rich.console import Console

from mtlx.materialx import create_materialx_file
from usdassemble.utils import ensure_directory, get_template_dir

app = typer.Typer()
console = Console()


# TODO： `detect_texture_files` is too complex , 重构优化
def detect_texture_files(component_path: str, component_name: str) -> dict[str, str]:
    """检测组件目录中的纹理文件."""
    texture_dir = Path(component_path) / "textures"

    if not texture_dir.exists():
        console.print(f"[yellow]警告: 未找到纹理目录 {texture_dir}[/yellow]")
        return {}

    # 常见的纹理文件模式
    texture_patterns = {
        # 键名同时也是.mtlx文件中图像节点的名称
        # https://docs.o3de.org/docs/user-guide/assets/texture-settings/texture-presets/?utm_source=chatgpt.com
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

    found_textures = {}

    # 扫描纹理文件
    for texture_type, patterns in texture_patterns.items():
        for pattern in patterns:
            files = (
                list(texture_dir.glob(f"{pattern}.jpg"))
                + list(texture_dir.glob(f"{pattern}.png"))
                + list(texture_dir.glob(f"{pattern}.exr"))
            )

            if files:
                # 选择第一个匹配的文件
                relative_path = files[0].relative_to(component_path).as_posix()
                found_textures[texture_type] = relative_path
                break

    console.print(
        f"[green]为 {component_name} 检测到纹理文件: {list(found_textures.keys())}[/green]",
    )
    # 检查是否存在重复的纹理文件、没用上的纹理文件,显示警告

    # TODO: 严格检查贴图文件，有多的重复的就报错停止，让用户重新确认而不是警告
    # 1. 检查是否有多个文件匹配同一类型
    for texture_type, patterns in texture_patterns.items():
        matched_files = []
        for pattern in patterns:
            matched_files += (
                list(texture_dir.glob(f"{pattern}.jpg"))
                + list(texture_dir.glob(f"{pattern}.png"))
                + list(texture_dir.glob(f"{pattern}.exr"))
            )
        if len(matched_files) > 1:
            file_list = [f.relative_to(component_path).as_posix() for f in matched_files]
            console.print(
                f"[yellow]警告: 纹理类型 '{texture_type}' 匹配到多个文件: {file_list}，仅使用第一个: {file_list[0]}[/yellow]",
            )

    # 2. 检查是否有没用上的纹理文件
    # 收集所有已用到的纹理文件
    used_files = set()
    for rel_path in found_textures.values():
        used_files.add((texture_dir / rel_path).resolve())

    # 收集目录下所有纹理文件
    all_texture_files = set()
    for ext in ("*.jpg", "*.png", "*.exr"):
        all_texture_files.update(texture_dir.glob(ext))

    # 检查未被使用的文件
    unused_files = []
    for f in all_texture_files:
        # 以绝对路径比较
        if f.resolve() not in used_files:
            unused_files.append(f.relative_to(component_path).as_posix())

    if unused_files:
        console.print(
            f"[yellow]警告: 以下纹理文件未被识别和使用: {unused_files}[/yellow]",
        )

    return found_textures


def create_from_template(
    template_path: Path,
    output_path: Path,
    substitutions: dict[str, str],
) -> None:
    """从模板文件创建新文件，使用string.Template进行替换.

    Args:
        template_path: 模板文件路径
        output_path: 输出文件路径
        substitutions: 替换字典
    """
    if not template_path.exists():
        console.print(f"[red]模板文件不存在: {template_path}[/red]")
        return

    # 确保输出目录存在
    ensure_directory(output_path)

    # 读取模板内容
    with Path.open(template_path, encoding="utf-8") as f:
        template_content = f.read()

    # 进行替换
    template = Template(template_content)
    content = template.safe_substitute(**substitutions)

    # 写入输出文件
    with Path.open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    console.print(f"[green]从模板生成文件: {output_path}[/green]")


def create_component_payload(output_path: str, component_name: str) -> None:
    """从模板创建 payload 文件."""
    template_path = (
        get_template_dir()
        / "{$assembly_name}"
        / "components"
        / "{$component_name}"
        / "{$component_name}_payload.usd"
    )

    substitutions = {
        "component_name": component_name,
    }

    create_from_template(template_path, Path(output_path), substitutions)


def create_component_look(output_path: str, component_name: str) -> None:
    """从模板创建外观文件."""
    template_path = (
        get_template_dir()
        / "{$assembly_name}"
        / "components"
        / "{$component_name}"
        / "{$component_name}_look.usd"
    )

    substitutions = {
        "component_name": component_name,
    }

    create_from_template(template_path, Path(output_path), substitutions)


def create_component_main(output_path: str, component_name: str) -> None:
    """从模板创建组件主入口文件."""
    template_path = (
        get_template_dir()
        / "{$assembly_name}"
        / "components"
        / "{$component_name}"
        / "{$component_name}.usd"
    )

    substitutions = {
        "component_name": component_name,
    }

    create_from_template(template_path, Path(output_path), substitutions)


def scan_components(base_path: str) -> list[str]:
    """扫描目录中的组件."""
    components_path = Path(base_path) / "components"

    if not components_path.exists():
        console.print(f"[yellow]警告: 未找到 components 目录: {components_path}[/yellow]")
        return []

    components = []
    for item in components_path.iterdir():
        if item.is_dir():
            # 检查是否有几何体文件
            geom_file = item / f"{item.name}_geom.usd"
            if geom_file.exists():
                components.append(item.name)
                console.print(f"[green]发现组件: {item.name}[/green]")
            else:
                console.print(f"[yellow]跳过目录 {item.name} (未找到几何体文件)[/yellow]")

    return components


def create_assembly_main(output_path: str, assembly_name: str, components: list[str]) -> None:
    """从模板创建 assembly 主入口文件."""
    template_path = get_template_dir() / "{$assembly_name}" / "{$assembly_name}.usda"

    # 读取模板
    with open(template_path, encoding="utf-8") as f:
        template_content = f.read()

    # 先进行基础替换
    template = Template(template_content)
    content = template.safe_substitute(assembly_name=assembly_name)

    # 使用USD API来正确添加多个组件引用
    # 创建临时文件
    temp_file = Path(output_path).with_suffix(".temp.usda")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(content)

    # 用USD API加载并修改
    stage = Usd.Stage.Open(str(temp_file))
    if not stage:
        console.print(f"[red]无法打开临时USD文件: {temp_file}[/red]")
        return

    # 获取assembly prim
    assembly_prim = stage.GetPrimAtPath(f"/{assembly_name}")
    if not assembly_prim:
        console.print(f"[red]未找到assembly prim: /{assembly_name}[/red]")
        return

    # 为每个组件创建引用
    for component_name in components:
        component_ref_path = f"./components/{component_name}/{component_name}.usd"
        component_prim = stage.DefinePrim(Sdf.Path(f"/{assembly_name}/{component_name}"))
        component_prim.GetReferences().AddReference(component_ref_path)
        console.print(f"[green]添加组件引用: {component_name}[/green]")

    # 保存到最终路径
    stage.Export(output_path)

    # 清理临时文件
    temp_file.unlink(missing_ok=True)

    console.print(f"[green]保存assembly文件: {output_path}[/green]")


def process_component(component_path: str, component_name: str) -> None:
    """处理单个组件."""
    console.print(f"\n[bold blue]=== 处理组件: {component_name} ===[/bold blue]")

    # 检测纹理文件
    texture_files = detect_texture_files(component_path, component_name)

    # 创建 MaterialX 文件
    if texture_files:
        template_mtlx_path = (
            get_template_dir()
            / "{$assembly_name}"
            / "components"
            / "{$component_name}"
            / "{$component_name}_mat.mtlx"
        )
        output_mtlx_path = Path(component_path) / f"{component_name}_mat.mtlx"
        create_materialx_file(
            str(template_mtlx_path),
            str(output_mtlx_path),
            component_name,
            texture_files,
        )
    else:
        console.print("[yellow]跳过 MaterialX 文件创建 (无纹理文件)[/yellow]")

    # 创建主入口文件
    main_file = Path(component_path) / f"{component_name}.usd"
    create_component_main(str(main_file), component_name)

    # 创建 payload 文件
    payload_file = Path(component_path) / f"{component_name}_payload.usd"
    create_component_payload(str(payload_file), component_name)

    # 创建外观文件
    look_file = Path(component_path) / f"{component_name}_look.usd"
    create_component_look(str(look_file), component_name)


@app.command()
def assembly(base_path: str = "./") -> None:
    """装配 USD assembly."""
    base_path = Path(base_path).resolve()
    assembly_name = base_path.name

    console.print(f"[bold blue]=== 装配 USD Assembly: {assembly_name} ===[/bold blue]")
    console.print(f"[blue]路径: {base_path}[/blue]")

    # 扫描组件
    components = scan_components(str(base_path))

    if not components:
        console.print("[red]错误: 未找到任何组件[/red]")
        return

    console.print(f"[green]找到 {len(components)} 个组件: {components}[/green]")

    # 处理每个组件
    for component_name in components:
        component_path = base_path / "components" / component_name
        process_component(str(component_path), component_name)

    # 创建 assembly 主文件
    assembly_file = base_path / f"{assembly_name}.usda"
    create_assembly_main(str(assembly_file), assembly_name, components)

    console.print("\n[bold green]✓ Assembly 装配完成![/bold green]")
