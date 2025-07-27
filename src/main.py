#!/usr/bin/env python3
"""USDAssemble 主入口文件.

用法:
    python -m src.main [command] [options]

或者直接运行:
    python src/main.py [command] [options]
"""

import typer

from core.assembly import AssemblyBuilder, AssemblyError

app = typer.Typer(help="USD资产自动组装工具")


@app.command()
def assemble(
    base_path: str = typer.Argument("./", help="资产目录路径"),
    # TODO：这个verbose参数是 Typer 包 注入的吗，没用的话删除
    verbose: bool = typer.Option(False, "--verbose", "-v", help="显示详细信息"),
) -> None:
    """装配USD assembly，支持components和subcomponents目录，以及变体."""
    try:
        builder = AssemblyBuilder()

        # TODO：这个verbose参数是 Typer 包 注入的吗，没用的话删除
        builder.build_assembly(base_path, verbose)
    except AssemblyError as e:
        typer.echo(f"装配失败: {e}", err=True)
        raise typer.Exit(1) from e
    except Exception as e:
        typer.echo(f"未知错误: {e}", err=True)
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
