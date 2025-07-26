"""USD Asset Assembly Script.

使用 Pixar OpenUSD API 装配棋盘资产
"""

from pathlib import Path
from string import Template
from typing import List, Optional

import typer
from pxr import Sdf, Usd
from rich import print as rprint
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mtlx.materialx import create_materialx_file
from usdassemble.utils import (
    TextureValidationError,
    ensure_directory,
    get_template_dir,
    validate_texture_files,
)

app = typer.Typer(help="USD资产自动组装工具")
console = Console()


class AssemblyError(Exception):
    """装配过程中的错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


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

    Raises
    ------
        AssemblyError: 当模板文件不存在或处理失败时
    """
    if not template_path.exists():
        raise AssemblyError(f"模板文件不存在: {template_path}") from None

    # 确保输出目录存在
    ensure_directory(output_path)

    try:
        # 读取模板内容
        with Path.open(template_path, encoding="utf-8") as f:
            template_content = f.read()

        # 进行替换
        template = Template(template_content)
        content = template.safe_substitute(**substitutions)

        # 写入输出文件
        with Path.open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        console.print(f"[green]✓ 生成文件: {output_path.name}[/green]")
    except Exception as e:
        raise AssemblyError(f"从模板生成文件失败: {e}") from e


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
    """扫描目录中的组件.

    Returns
    -------
        List[str]: 有效组件名称列表

    Raises
    ------
        AssemblyError: 当未找到任何组件时
    """
    components_path = Path(base_path) / "components"

    if not components_path.exists():
        msg = "未找到 components 目录"
        raise AssemblyError(msg) from None

    components = []
    table = Table(title="扫描到的组件")
    table.add_column("组件名", style="cyan")
    table.add_column("状态", style="green")

    for item in components_path.iterdir():
        if item.is_dir():
            # 检查是否有几何体文件
            geom_file = item / f"{item.name}_geom.usd"
            if geom_file.exists():
                components.append(item.name)
                table.add_row(item.name, "✓ 有效")
            else:
                table.add_row(item.name, "[yellow]✗ 缺少几何体文件[/yellow]")

    if table.rows:
        console.print(table)

    if not components:
        msg = "未找到任何有效组件（需要包含*_geom.usd文件）"
        raise AssemblyError(msg)

    return components


def create_assembly_main(output_path: str, assembly_name: str, components: list[str]) -> None:
    """从模板创建 assembly 主入口文件.

    Raises
    ------
        AssemblyError: 当创建失败时
    """
    template_path = get_template_dir() / "{$assembly_name}" / "{$assembly_name}.usda"

    try:
        # 读取模板
        with Path.open(template_path, encoding="utf-8") as f:
            template_content = f.read()

        # 先进行基础替换
        template = Template(template_content)
        content = template.safe_substitute(assembly_name=assembly_name)

        # 使用USD API来正确添加多个组件引用
        # 创建临时文件
        temp_file = Path(output_path).with_suffix(".temp.usda")
        with Path.open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)

        # 用USD API加载并修改
        stage = Usd.Stage.Open(str(temp_file))
        if not stage:
            msg = f"无法打开临时USD文件: {temp_file}"

        # 获取assembly prim
        assembly_prim = stage.GetPrimAtPath(f"/{assembly_name}")
        if not assembly_prim:
            msg = f"未找到assembly prim: /{assembly_name}"

        # 为每个组件创建引用
        for component_name in components:
            component_ref_path = f"./components/{component_name}/{component_name}.usd"
            component_prim = stage.DefinePrim(Sdf.Path(f"/{assembly_name}/{component_name}"))
            component_prim.GetReferences().AddReference(component_ref_path)

        # 保存到最终路径
        stage.Export(output_path)

        # 清理临时文件
        temp_file.unlink(missing_ok=True)

        console.print(f"[green]✓ 生成assembly文件: {Path(output_path).name}[/green]")

    except Exception as e:
        if not msg:
            msg = f"创建assembly文件失败: {e}"
        raise AssemblyError(msg) from e


def process_component(component_path: str, component_name: str) -> None:
    """处理单个组件.

    Raises
    ------
        AssemblyError: 当处理失败时
    """
    with console.status(f"[bold blue]处理组件: {component_name}[/bold blue]") as status:
        try:
            # 验证纹理文件
            texture_dir = Path(component_path) / "textures"
            texture_files = validate_texture_files(texture_dir, component_name)

            # 创建 MaterialX 文件
            if texture_files:
                output_mtlx_path = Path(component_path) / f"{component_name}_mat.mtlx"
                create_materialx_file(
                    component_name,
                    texture_files,
                    str(output_mtlx_path),
                )
            else:
                console.print(
                    f"[yellow]⚠ 跳过 {component_name} 的 MaterialX 文件创建 (无纹理文件)[/yellow]",
                )

            # 创建主入口文件
            main_file = Path(component_path) / f"{component_name}.usd"
            create_component_main(str(main_file), component_name)

            # 创建 payload 文件
            payload_file = Path(component_path) / f"{component_name}_payload.usd"
            create_component_payload(str(payload_file), component_name)

            # 创建外观文件
            look_file = Path(component_path) / f"{component_name}_look.usd"
            create_component_look(str(look_file), component_name)

            console.print(f"[green]✓ 组件 {component_name} 处理完成[/green]")

        except TextureValidationError as e:
            msg = f"组件 {component_name} 纹理验证失败: {e}"
            raise AssemblyError(msg) from e
        except Exception as e:
            msg = f"处理组件 {component_name} 失败: {e}"
            raise AssemblyError(msg) from e


@app.command()
def assembly(
    base_path: str = typer.Argument("./", help="资产目录路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细信息"),
) -> None:
    """装配 USD assembly."""
    try:
        base_path_obj = Path(base_path).resolve()
        assembly_name = base_path_obj.name

        # 显示标题
        console.print(
            Panel.fit(
                f"[bold blue]USD Assembly 装配工具[/bold blue]\n"
                f"[blue]项目: {assembly_name}[/blue]\n"
                f"[blue]路径: {base_path_obj}[/blue]",
                border_style="blue",
            ),
        )

        # 扫描组件
        components = scan_components(str(base_path_obj))
        console.print(f"\n[green]找到 {len(components)} 个有效组件[/green]")

        # 处理每个组件
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("处理组件...", total=len(components))

            for component_name in components:
                component_path = base_path_obj / "components" / component_name
                process_component(str(component_path), component_name)
                progress.advance(task)

        # 创建 assembly 主文件
        console.print("\n[bold blue]生成 Assembly 主文件...[/bold blue]")
        assembly_file = base_path_obj / f"{assembly_name}.usda"
        create_assembly_main(str(assembly_file), assembly_name, components)

        # 完成
        console.print(
            Panel.fit(
                "[bold green]✅ Assembly 装配完成![/bold green]",
                border_style="green",
            ),
        )

    except AssemblyError as e:
        console.print(f"[bold red]❌ 装配失败: {e}[/bold red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[bold red]❌ 未知错误: {e}[/bold red]")
        if verbose:
            console.print_exception()
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
