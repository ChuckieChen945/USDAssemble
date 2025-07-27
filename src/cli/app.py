#!/usr/bin/env python3
"""USDAssemble 主入口文件.

用法:
    python -m src.cli.app [command] [options]

或者直接运行:
    python src/cli/app.py [command] [options]
"""

from pathlib import Path

import typer
from rich.console import Console

from core.assembly import AssemblyBuilder
from domain.exceptions import AssemblyError, ComponentError, MaterialXError, VariantError

console = Console()
app = typer.Typer(help="USD资产自动组装工具")


@app.command()
def assemble(
    base_path: str = typer.Argument("./", help="资产目录路径"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细信息"),
    dry_run: bool = typer.Option(False, "--dry-run", help="仅扫描，不生成文件"),
) -> None:
    """装配USD assembly，支持components和subcomponents目录，以及变体."""
    try:
        # 验证路径
        path_obj = Path(base_path).resolve()
        if not path_obj.exists():
            console.print(f"[red]错误: 路径不存在 {path_obj}[/red]")
            raise typer.Exit(1)

        if verbose:
            console.print(f"[blue]工作目录: {path_obj}[/blue]")

        builder = AssemblyBuilder()

        if dry_run:
            # 仅扫描模式
            components = builder.scan_components(str(path_obj))
            console.print(f"[green]扫描完成，找到 {len(components)} 个组件[/green]")
        else:
            # 正常装配模式
            builder.build_assembly(str(path_obj))

    except AssemblyError as e:
        console.print(f"[red]装配失败: {e}[/red]")
        raise typer.Exit(1) from e
    except ComponentError as e:
        console.print(f"[red]组件处理失败: {e}[/red]")
        raise typer.Exit(1) from e
    except VariantError as e:
        console.print(f"[red]变体处理失败: {e}[/red]")
        raise typer.Exit(1) from e
    except MaterialXError as e:
        console.print(f"[red]MaterialX处理失败: {e}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]未知错误: {e}[/red]")
        if verbose:
            import traceback

            console.print(f"[red]{traceback.format_exc()}[/red]")
        raise typer.Exit(1) from e


@app.command()
def scan(
    base_path: str = typer.Argument("./", help="资产目录路径"),
    show_details: bool = typer.Option(False, "--details", "-d", help="显示详细信息"),
) -> None:
    """扫描目录结构，显示组件信息."""
    try:
        path_obj = Path(base_path).resolve()
        if not path_obj.exists():
            console.print(f"[red]错误: 路径不存在 {path_obj}[/red]")
            raise typer.Exit(1)

        builder = AssemblyBuilder()
        components = builder.scan_components(str(path_obj))

        if show_details:
            console.print("\n[bold blue]详细组件信息:[/bold blue]")
            for i, comp in enumerate(components, 1):
                console.print(f"\n[cyan]{i}. {comp.name}[/cyan]")
                console.print(f"   类型: {comp.component_type.kind}")
                console.print(f"   几何体: {'✓' if comp.has_geometry else '✗'}")
                console.print(f"   变体数: {len(comp.variants) if comp.has_variants else 0}")
                if comp.has_variants:
                    for variant in comp.variants:
                        console.print(f"     - {variant.name}: {len(variant.textures)} 个纹理")
                elif comp.textures:
                    console.print(f"   纹理数: {len(comp.textures)}")

    except AssemblyError as e:
        console.print(f"[red]扫描失败: {e}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]未知错误: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def validate(
    base_path: str = typer.Argument("./", help="资产目录路径"),
) -> None:
    """验证目录结构是否符合USD装配要求."""
    try:
        path_obj = Path(base_path).resolve()
        if not path_obj.exists():
            console.print(f"[red]错误: 路径不存在 {path_obj}[/red]")
            raise typer.Exit(1)

        # 检查目录结构
        has_components = (path_obj / "components").exists()
        has_subcomponents = (path_obj / "subcomponents").exists()

        if not has_components and not has_subcomponents:
            console.print("[red]错误: 目录中缺少 components 或 subcomponents 文件夹[/red]")
            raise typer.Exit(1)

        if has_components and has_subcomponents:
            console.print("[yellow]警告: 同时存在 components 和 subcomponents 目录[/yellow]")

        # 扫描组件
        builder = AssemblyBuilder()
        components = builder.scan_components(str(path_obj))

        console.print(f"[green]✓ 验证通过，找到 {len(components)} 个有效组件[/green]")

    except AssemblyError as e:
        console.print(f"[red]验证失败: {e}[/red]")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]未知错误: {e}[/red]")
        raise typer.Exit(1) from e


@app.command()
def info() -> None:
    """显示USDAssemble工具信息."""
    console.print("[bold blue]USDAssemble - USD资产自动组装工具[/bold blue]")
    console.print("[blue]版本: 1.0.0[/blue]")
    console.print("[blue]支持的功能:[/blue]")
    console.print("  - Assembly装配")
    console.print("  - Component组件处理")
    console.print("  - Subcomponent子组件处理")
    console.print("  - 材质变体支持")
    console.print("  - MaterialX集成")
    console.print("  - 模板驱动生成")


if __name__ == "__main__":
    app()
