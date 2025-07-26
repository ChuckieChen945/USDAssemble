#!/usr/bin/env python3
"""USDAssemble 主入口文件.

用法:
    python -m src.main [command] [options]

或者直接运行:
    python src/main.py [command] [options]
"""

from usdassemble.cli import app

if __name__ == "__main__":
    app()
