"""USD文件操作服务."""

from pathlib import Path
from string import Template

from pxr import Sdf, Usd
from rich.console import Console

from services.file_service import FileService
from utils.utils import ComponentInfo, ComponentType, get_template_dir

console = Console()


class UsdServiceError(Exception):
    """USD服务错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class UsdService:
    """USD文件操作服务.

    负责所有的USD文件创建和操作，包括assembly文件、组件文件等。
    """

    def __init__(self) -> None:
        """初始化USD服务."""
        self.file_service = FileService()

    def create_assembly_main(
        self,
        output_path: str,
        assembly_name: str,
        components: list[ComponentInfo],
    ) -> None:
        """从模板创建assembly主入口文件.

        Args:
            output_path: 输出文件路径
            assembly_name: 装配名称
            components: 组件信息列表

        Raises
        ------
            UsdServiceError: 当创建失败时
        """
        if not components:
            msg = "组件列表为空"
            raise UsdServiceError(msg)

        # 所有组件应该是同一类型
        component_type = components[0].component_type

        # TODO: 重构，看看是否将以下从模板创建的部分逻辑，归纳到 template_service.TemplateService中
        template_path = (
            get_template_dir()
            / "{$assembly_or_component_name}"
            / "{$assembly_or_component_name}.usda"
        )

        try:
            # 读取模板
            template_content = self.file_service.read_file(template_path)

            # 先进行基础替换
            template = Template(template_content)
            content = template.safe_substitute(assembly_name=assembly_name)

            # 使用USD API来正确添加多个组件引用
            # 创建临时文件
            temp_file = Path(output_path).with_suffix(".temp.usda")
            self.file_service.write_file(temp_file, content)

            # 用USD API加载并修改
            stage = Usd.Stage.Open(str(temp_file))
            if not stage:
                msg = f"无法打开临时USD文件: {temp_file}"
                # FIXME: Abstract `raise` to an inner function (RuffTRY301)
                raise UsdServiceError(msg)

            # 获取assembly prim
            assembly_prim = stage.GetPrimAtPath(f"/{assembly_name}")
            if not assembly_prim:
                msg = f"未找到assembly prim: /{assembly_name}"
                # FIXME: Abstract `raise` to an inner function (RuffTRY301)
                raise UsdServiceError(msg)

            # 为每个组件创建引用
            for component_info in components:
                component_ref_path = (
                    f"./{component_type.directory}/{component_info.name}/{component_info.name}.usd"
                )
                component_prim = stage.OverridePrim(
                    Sdf.Path(f"/{assembly_name}/{component_info.name}"),
                )
                component_prim.SetTypeName("Xform")
                component_prim.GetReferences().AddReference(component_ref_path)

            # 保存到最终路径
            stage.GetRootLayer().Export(output_path)

            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()

            console.print(f"[green]✓ 生成assembly文件: {Path(output_path).name}[/green]")
            console.print(f"[blue]✓ 包含 {len(components)} 个{component_type.kind}引用[/blue]")

        except Exception as e:
            # 清理临时文件
            if "temp_file" in locals() and temp_file.exists():
                temp_file.unlink()
            if not isinstance(e, UsdServiceError):
                msg = f"创建assembly文件失败: {e}"
                raise UsdServiceError(msg) from e
            raise

    def create_component_main_simple(
        self,
        output_path: str,
        component_name: str,
        component_type: ComponentType,
    ) -> None:
        """创建简单的组件主文件（无变体）.

        Args:
            output_path: 输出文件路径
            component_name: 组件名称
            component_type: 组件类型

        Raises
        ------
            UsdServiceError: 当创建失败时
        """
        try:
            # TODO: 重构，看看是否将以下从模板创建的部分逻辑，归纳到 template_service.TemplateService中
            # 获取模板路径
            template_path = (
                get_template_dir()
                / "{$assembly_or_component_name}"
                / "components_or_subcomponents"
                / "{$component_or_subcomponent_name}"
                / "{$component_or_subcomponent_name}.usd"
            )

            if not template_path.exists():
                msg = f"模板文件不存在: {template_path}"
                # FIXME: Abstract `raise` to an inner function (RuffTRY301)
                raise UsdServiceError(msg)

            # 读取模板内容
            template_content = self.file_service.read_file(template_path)

            # 进行替换
            template = Template(template_content)
            content = template.safe_substitute(component_name=component_name)

            # 写入文件
            self.file_service.write_file(Path(output_path), content)

            # 设置kind值
            self._set_component_kind(output_path, component_name, component_type.kind)

            console.print(f"[green]✓ 生成文件: {Path(output_path).name}[/green]")

        except Exception as e:
            if not isinstance(e, UsdServiceError):
                msg = f"创建组件主文件失败: {e}"
                raise UsdServiceError(msg) from e
            raise

    def _set_component_kind(self, file_path: str, component_name: str, kind: str) -> None:
        """设置组件的kind值.

        Args:
            file_path: USD文件路径
            component_name: 组件名称
            kind: kind值
        """
        try:
            stage = Usd.Stage.Open(file_path)
            if stage:
                component_prim = stage.GetPrimAtPath(f"/{component_name}")
                if component_prim:
                    model_api = Usd.ModelAPI(component_prim)
                    model_api.SetKind(kind)
                    stage.Save()

                    console.print(
                        f"[blue]✓ 设置组件 {component_name} 的kind为: {kind}[/blue]",
                    )
        except Exception as e:
            # 这里不抛出异常，只是警告，因为kind设置失败不应该阻止整个流程
            console.print(f"[yellow]⚠ 设置kind失败: {e}[/yellow]")
