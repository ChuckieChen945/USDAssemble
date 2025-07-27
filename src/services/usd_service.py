"""USD文件处理服务."""

from pathlib import Path

from pxr import Sdf, Usd
from rich.console import Console

from domain.enums import ComponentType
from domain.exceptions import UsdServiceError
from domain.models import ComponentInfo
from services.file_service import FileService
from services.template_service import TemplateService

console = Console()


class UsdService:
    """USD文件处理服务.

    负责所有的USD文件操作，包括创建、修改、引用等。
    """

    def __init__(self) -> None:
        """初始化USD服务."""
        self.file_service = FileService()
        self.template_service = TemplateService()

    def create_assembly_main(
        self,
        output_path: str,
        assembly_name: str,
        components: list[ComponentInfo],
    ) -> None:
        """创建assembly主文件.

        Args:
            output_path: 输出文件路径
            assembly_name: assembly名称
            components: 组件信息列表

        Raises
        ------
            UsdServiceError: 当创建失败时
        """
        if not components:
            self._raise_error("组件列表不能为空")

        component_type = components[0].component_type

        try:
            # 使用模板服务创建基础内容
            content = self.template_service.create_assembly_main_template(
                assembly_name,
            )

            # 使用USD API来正确添加多个组件引用
            # 创建临时文件
            temp_file = Path(output_path).with_suffix(".temp.usda")
            self.file_service.write_file(temp_file, content)

            # 用USD API加载并修改
            stage = Usd.Stage.Open(str(temp_file))
            if not stage:
                self._raise_error(f"无法打开临时USD文件: {temp_file}")

            # 获取assembly prim
            assembly_prim = stage.GetPrimAtPath(f"/{assembly_name}")
            if not assembly_prim:
                self._raise_error(f"未找到assembly prim: /{assembly_name}")

            # 根据组件类型设置assembly prim的类型
            self._set_assembly_prim_type(assembly_prim, component_type)

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
                self._raise_error(f"创建assembly文件失败: {e}")
            raise

    def _set_assembly_prim_type(self, assembly_prim, component_type) -> None:
        """根据组件类型设置assembly prim的类型.

        Args:
            assembly_prim: assembly prim对象
            component_type: 组件类型
        """
        # 当 component_type 为 subcomponent 时，将 assembly_prim 的 type 由原来的 assembly 改为 component
        if component_type.kind == "subcomponent":
            model_api = Usd.ModelAPI(assembly_prim)
            model_api.SetKind("component")

    def _raise_error(self, message: str) -> None:
        """统一的错误抛出函数.

        Args:
            message: 错误消息

        Raises
        ------
            UsdServiceError: 统一的USD服务错误
        """
        raise UsdServiceError(message)

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
            # 使用模板服务创建基础内容
            content = self.template_service.create_component_main_template(
                component_name,
                component_type,
            )

            # 写入文件
            self.file_service.write_file(Path(output_path), content)

            # 设置kind值
            self._set_component_kind(output_path, component_name, component_type.kind)

            console.print(f"[green]✓ 生成文件: {Path(output_path).name}[/green]")

        except Exception as e:
            if not isinstance(e, UsdServiceError):
                self._raise_error(f"创建组件主文件失败: {e}")
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
                    # 设置kind值
                    model_api = Usd.ModelAPI(component_prim)
                    model_api.SetKind(kind)
                    stage.GetRootLayer().Save()
        except Exception as e:
            console.print(f"[yellow]⚠ 设置kind值失败: {e}[/yellow]")
