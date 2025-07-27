"""MaterialX处理器."""

from pathlib import Path

from rich.console import Console

import MaterialX
from materialx.variant_processor import VariantMaterialXProcessor
from services.file_service import FileService
from services.template_service import TemplateService
from utils.utils import ComponentInfo, ComponentType

console = Console()


class MaterialXError(Exception):
    """MaterialX处理错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class MaterialXProcessor:
    """MaterialX处理器.

    负责处理USD组件的MaterialX材质文件，支持变体装配。
    这个类重构了原有的MaterialX处理逻辑，将复杂的变体处理分离到专门的处理器中。
    """

    def __init__(self) -> None:
        """初始化MaterialX处理器."""
        self.file_service = FileService()
        self.template_service = TemplateService()
        self.variant_processor = VariantMaterialXProcessor()

    def create_materialx_from_component_info(
        self,
        component_info: ComponentInfo,
        output_mtlx_path: str,
    ) -> None:
        """根据组件信息创建MaterialX文件.

        根据组件是否有变体，自动选择合适的创建方式。

        Args:
            component_info: 组件信息
            output_mtlx_path: 输出MaterialX文件路径

        Raises
        ------
            MaterialXError: 当处理失败时
        """
        if component_info.has_variants:
            self.variant_processor.create_variant_materialx_file(
                component_info,
                output_mtlx_path,
            )
        else:
            self.create_simple_materialx_file(
                component_info.name,
                component_info.textures,
                output_mtlx_path,
                component_info.component_type,
            )

    def create_simple_materialx_file(
        self,
        component_name: str,
        texture_files: dict[str, str],
        output_mtlx_path: str,
        component_type: ComponentType = ComponentType.COMPONENT,
    ) -> None:
        """创建简单MaterialX文件（无变体）.

        Args:
            component_name: 组件名称
            texture_files: 纹理文件映射 {纹理类型: 相对路径}
            output_mtlx_path: 输出MaterialX文件路径
            component_type: 组件类型

        Raises
        ------
            MaterialXError: 当处理失败时
        """
        temp_file = None

        try:
            # 创建基础内容
            content = self._create_base_materialx_content(component_name, component_type)

            # 写入临时文件用于MaterialX处理
            temp_file = Path(output_mtlx_path).with_suffix(".temp.mtlx")
            self.file_service.write_file(temp_file, content)

            # 创建MaterialX文档并处理
            doc = MaterialX.createDocument()
            MaterialX.readFromXmlFile(doc, str(temp_file))

            # 查找节点图
            compound_ng = doc.getNodeGraph(f"NG_{component_name}")
            if not compound_ng:
                msg = f"找不到节点图: NG_{component_name}"
                # FIXME:Abstract `raise` to an inner function (Ruff TRY301)
                raise MaterialXError(msg)

            # 处理纹理节点
            added_textures = self._process_texture_nodes(compound_ng, texture_files)

            # 清理未使用的图像节点
            self._cleanup_unused_image_nodes(compound_ng, set(texture_files.keys()))

            # 输出最终的MaterialX文件
            MaterialX.writeToXmlFile(doc, output_mtlx_path)

            console.print(
                f"[green]✓ 生成MaterialX文件: {Path(output_mtlx_path).name} "
                f"(包含{len(added_textures)}个纹理)[/green]",
            )

        except Exception as e:
            if not isinstance(e, MaterialXError):
                msg = f"创建MaterialX文件失败: {e}"
                raise MaterialXError(msg) from e
            raise
        finally:
            # 清理临时文件
            if temp_file and temp_file.exists():
                temp_file.unlink(missing_ok=True)

    def _create_base_materialx_content(
        self,
        component_name: str,
        component_type: ComponentType,
    ) -> str:
        """从模板创建基础MaterialX内容.

        Args:
            component_name: 组件名称
            component_type: 组件类型

        Returns
        -------
            str: 处理后的MaterialX内容

        Raises
        ------
            MaterialXError: 当模板文件不存在时
        """
        template_path = self.template_service.get_template_path(
            component_type,
            "{$component_name}_mat.mtlx",
        )

        if not template_path.exists():
            msg = f"MaterialX模板文件不存在: {template_path}"
            raise MaterialXError(msg)

        # 读取模板内容
        template_content = self.file_service.read_file(template_path)

        # 使用模板替换基础变量
        from string import Template

        template = Template(template_content)
        return template.safe_substitute(component_name=component_name)

    def _process_texture_nodes(
        self,
        node_graph: MaterialX.NodeGraph,
        texture_files: dict[str, str],
        variant_name: str | None = None,
    ) -> list[str]:
        """处理MaterialX节点图中的纹理节点.

        Args:
            node_graph: MaterialX节点图
            texture_files: 纹理文件映射
            variant_name: 变体名称（可选）

        Returns
        -------
            List[str]: 已添加纹理的节点名称列表
        """
        added_textures = []
        context = f"变体 '{variant_name}'" if variant_name else "默认材质"

        for node_name, texture_path in texture_files.items():
            image_node = node_graph.getNode(node_name)
            if image_node:
                # 添加file输入
                file_input = image_node.getInput("file")
                if not file_input:
                    file_input = image_node.addInput("file", "filename")
                file_input.setValueString(texture_path)
                added_textures.append(node_name)
            else:
                console.print(
                    f"[yellow]⚠ 警告: {context}中未找到节点 {node_name}[/yellow]",
                )

        return added_textures

    def _cleanup_unused_image_nodes(
        self,
        node_graph: MaterialX.NodeGraph,
        used_texture_types: set[str],
    ) -> None:
        """清理未使用的图像节点.

        Args:
            node_graph: MaterialX节点图
            used_texture_types: 已使用的纹理类型集合
        """
        # 获取所有image节点
        image_nodes = [node for node in node_graph.getNodes() if node.getType() == "image"]

        # 删除未使用的image节点
        removed_count = 0
        for node in image_nodes:
            if node.getName() not in used_texture_types:
                node_graph.removeNode(node.getName())
                removed_count += 1

        if removed_count > 0:
            console.print(f"[blue]清理了 {removed_count} 个未使用的图像节点[/blue]")
