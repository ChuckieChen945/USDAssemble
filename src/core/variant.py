"""USD变体处理器."""

from pathlib import Path

from pxr import Usd, UsdShade
from rich.console import Console

from services.template_service import TemplateService
from services.usd_service import UsdService
from utils.utils import ComponentInfo

console = Console()


class VariantError(Exception):
    """变体处理错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class VariantProcessor:
    """USD变体处理器.

    负责处理组件的变体相关逻辑，包括变体集创建、材质绑定等。
    这个类重构了原来复杂的create_component_main_with_variants函数。
    """

    def __init__(self, usd_service: UsdService) -> None:
        """初始化变体处理器.

        Args:
            usd_service: USD服务
        """
        self.usd_service = usd_service
        self.template_service = TemplateService()

    def create_component_main_with_variants(
        self,
        component_info: ComponentInfo,
        output_path: str,
    ) -> None:
        """创建支持变体的组件主文件.

        这是原来create_component_main_with_variants的重构版本，
        将复杂逻辑分解为多个小函数。

        Args:
            component_info: 组件信息
            output_path: 输出文件路径

        Raises
        ------
            VariantError: 当创建失败时
        """
        try:
            # 1. 从模板创建基础文件
            self._create_base_file_from_template(component_info, output_path)

            # 2. 如果有变体，处理变体逻辑
            if component_info.has_variants:
                self._setup_variants(component_info, output_path)
            else:
                # 3. 没有变体，只设置kind值
                self._set_component_kind(component_info, output_path)

        except Exception as e:
            msg = f"创建组件主文件失败: {e}"
            raise VariantError(msg) from e

    def _create_base_file_from_template(
        self,
        component_info: ComponentInfo,
        output_path: str,
    ) -> None:
        """从模板创建基础文件."""
        substitutions = {"component_name": component_info.name}

        self.template_service.create_from_template(
            component_info.component_type,
            f"{component_info.name}.usd",
            Path(output_path),
            substitutions,
        )

    def _setup_variants(self, component_info: ComponentInfo, output_path: str) -> None:
        """设置变体集和变体."""
        stage = Usd.Stage.Open(output_path)
        if not stage:
            msg = f"无法打开USD文件: {output_path}"
            raise VariantError(msg)

        # 获取组件prim
        component_prim = self._get_component_prim(stage, component_info.name)

        # 设置kind值
        self._set_prim_kind(component_prim, component_info.component_type.kind)

        # 创建变体集
        variant_set = self._create_variant_set(component_prim, "material_variant")

        # 为每个变体创建变体选项
        for variant in component_info.variants:
            self._create_variant_option(
                stage,
                variant_set,
                variant,
                component_info.name,
            )

        # 设置默认变体
        if component_info.variants:
            variant_set.SetVariantSelection(component_info.variants[0].name)

        # 保存修改
        stage.Save()

        console.print(
            f"[blue]✓ 设置组件 {component_info.name} 的变体: "
            f"{[v.name for v in component_info.variants]}[/blue]",
        )

    def _get_component_prim(self, stage: Usd.Stage, component_name: str) -> Usd.Prim:
        """获取组件prim."""
        component_prim = stage.GetPrimAtPath(f"/{component_name}")
        if not component_prim:
            msg = f"未找到组件prim: /{component_name}"
            raise VariantError(msg)
        return component_prim

    def _set_prim_kind(self, prim: Usd.Prim, kind: str) -> None:
        """设置prim的kind值."""
        model_api = Usd.ModelAPI(prim)
        model_api.SetKind(kind)

    def _create_variant_set(self, prim: Usd.Prim, variant_set_name: str) -> Usd.VariantSet:
        """创建变体集."""
        variant_sets = prim.GetVariantSets()
        return variant_sets.AddVariantSet(variant_set_name)

    def _create_variant_option(
        self,
        stage: Usd.Stage,
        variant_set,
        variant,
        component_name: str,
    ) -> None:
        """创建单个变体选项."""
        # 添加变体选项
        variant_set.AddVariant(variant.name)
        variant_set.SetVariantSelection(variant.name)

        # 在变体上下文中修改材质绑定
        with variant_set.GetVariantEditContext():
            self._setup_variant_material_binding(
                stage,
                variant,
                component_name,
            )

    def _setup_variant_material_binding(
        self,
        stage: Usd.Stage,
        variant,
        component_name: str,
    ) -> None:
        """设置变体的材质绑定."""
        # 更新材质引用
        materials_scope = stage.GetPrimAtPath(f"/{component_name}/Materials")
        if materials_scope:
            # 清除默认引用，添加变体特定的引用
            materials_scope.GetReferences().ClearReferences()
            materials_scope.GetReferences().AddReference(
                f"./{component_name}_mat.mtlx",
                "/MaterialX/Materials",
            )

            # 更新材质绑定到变体特定的材质
            self._bind_variant_material(stage, variant, component_name)

    def _bind_variant_material(
        self,
        stage: Usd.Stage,
        variant,
        component_name: str,
    ) -> None:
        """绑定变体材质."""
        geom_prim = stage.GetPrimAtPath(f"/{component_name}/Geom")
        if not geom_prim:
            return

        render_prim = geom_prim.GetChild("Render")
        if not render_prim:
            return

        material_binding_api = UsdShade.MaterialBindingAPI(render_prim)
        variant_material_path = f"/{component_name}/Materials/M_{component_name}_{variant.name}"

        material_prim = stage.GetPrimAtPath(variant_material_path)
        if material_prim:
            material_binding_api.Bind(UsdShade.Material(material_prim))

    def _set_component_kind(self, component_info: ComponentInfo, output_path: str) -> None:
        """设置组件的kind值（无变体情况）."""
        stage = Usd.Stage.Open(output_path)
        if not stage:
            return

        component_prim = stage.GetPrimAtPath(f"/{component_info.name}")
        if component_prim:
            self._set_prim_kind(component_prim, component_info.component_type.kind)
            stage.Save()

            console.print(
                f"[blue]✓ 设置组件 {component_info.name} 的kind为: "
                f"{component_info.component_type.kind}[/blue]",
            )
