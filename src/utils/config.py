"""配置管理模块."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from rich.console import Console

console = Console()


class ConfigManager:
    """配置管理器.

    负责管理USDAssemble的配置信息，包括模板路径、输出设置等。
    """

    def __init__(self, config_file: Path | None = None) -> None:
        """初始化配置管理器.

        Args:
            config_file: 配置文件路径，默认为项目根目录下的 .usdassemble.json
        """
        if config_file is None:
            config_file = Path.cwd() / ".usdassemble.json"

        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """加载配置文件."""
        default_config = {
            "template_dir": "src/template",
            "output_format": "usda",
            "verbose": False,
            "backup_files": True,
            "materialx_settings": {
                "default_format": "mtlx",
                "texture_formats": ["jpg", "png", "exr", "tga"],
                "max_texture_size": 4096,
            },
            "usd_settings": {
                "default_up_axis": "Y",
                "meters_per_unit": 1.0,
                "time_code_per_second": 24.0,
            },
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    user_config = json.load(f)
                    # 合并用户配置和默认配置
                    return self._merge_configs(default_config, user_config)
            except Exception as e:
                console.print(f"[yellow]警告: 加载配置文件失败，使用默认配置: {e}[/yellow]")
                return default_config
        else:
            # 创建默认配置文件
            self._save_config(default_config)
            return default_config

    def _merge_configs(self, default: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
        """合并默认配置和用户配置."""
        result = default.copy()

        def merge_dict(base: dict[str, Any], override: dict[str, Any]) -> None:
            for key, value in override.items():
                if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                    merge_dict(base[key], value)
                else:
                    base[key] = value

        merge_dict(result, user)
        return result

    def _save_config(self, config: dict[str, Any]) -> None:
        """保存配置到文件."""
        try:
            with Path.open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            console.print(f"[yellow]警告: 保存配置文件失败: {e}[/yellow]")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值.

        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值

        Returns
        -------
            Any: 配置值
        """
        keys = key.split(".")
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """设置配置值.

        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split(".")
        config = self.config

        # 导航到父级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # 设置值
        config[keys[-1]] = value

        # 保存到文件
        self._save_config(self.config)

    def get_template_dir(self) -> Path:
        """获取模板目录路径."""
        template_dir = self.get("template_dir", "src/template")
        return Path(template_dir)

    def get_output_format(self) -> str:
        """获取输出格式."""
        return self.get("output_format", "usda")

    def is_verbose(self) -> bool:
        """是否启用详细输出."""
        return self.get("verbose", False)

    def should_backup_files(self) -> bool:
        """是否备份文件."""
        return self.get("backup_files", True)

    def get_materialx_settings(self) -> dict[str, Any]:
        """获取MaterialX设置."""
        return self.get("materialx_settings", {})

    def get_usd_settings(self) -> dict[str, Any]:
        """获取USD设置."""
        return self.get("usd_settings", {})

    def validate_config(self) -> bool:
        """验证配置的有效性."""
        try:
            # 检查模板目录
            template_dir = self.get_template_dir()
            if not template_dir.exists():
                console.print(f"[red]错误: 模板目录不存在: {template_dir}[/red]")
                return False

            # 检查输出格式
            output_format = self.get_output_format()
            if output_format not in ["usda", "usd", "usdc"]:
                console.print(f"[red]错误: 不支持的输出格式: {output_format}[/red]")
                return False

            # 检查MaterialX设置
            mtlx_settings = self.get_materialx_settings()
            texture_formats = mtlx_settings.get("texture_formats", [])
            if not texture_formats:
                console.print("[red]错误: 未配置支持的纹理格式[/red]")
                return False

            console.print("[green]✓ 配置验证通过[/green]")
            return True

        except Exception as e:
            console.print(f"[red]配置验证失败: {e}[/red]")
            return False

    def show_config(self) -> None:
        """显示当前配置."""
        console.print("[bold blue]当前配置:[/bold blue]")
        console.print(f"  模板目录: {self.get_template_dir()}")
        console.print(f"  输出格式: {self.get_output_format()}")
        console.print(f"  详细输出: {self.is_verbose()}")
        console.print(f"  备份文件: {self.should_backup_files()}")

        mtlx_settings = self.get_materialx_settings()
        console.print(f"  MaterialX格式: {mtlx_settings.get('default_format', 'mtlx')}")
        console.print(f"  支持纹理格式: {', '.join(mtlx_settings.get('texture_formats', []))}")

        usd_settings = self.get_usd_settings()
        console.print(f"  USD上轴: {usd_settings.get('default_up_axis', 'Y')}")
        console.print(f"  单位比例: {usd_settings.get('meters_per_unit', 1.0)}")


# 全局配置实例
config = ConfigManager()
