"""USDAssemble CLI."""

from pathlib import Path

import typer
from rich import print as rprint

from usdassemble.core.process import list_usd_dependencies

app = typer.Typer()


@app.command()
def list_usd_files(usd_path: Path) -> None:
    """列出usd文件的所有依赖项，包括子层和外部引用."""
    deps = list_usd_dependencies(usd_path)
    rprint(f"[bold blue]USD dependencies for {usd_path}:[/bold blue]")
    for dep in deps:
        rprint(f" - {dep}")


if __name__ == "__main__":
    app()
