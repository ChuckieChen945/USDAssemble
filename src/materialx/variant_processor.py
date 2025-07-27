"""变体MaterialX处理器."""

from pathlib import Path

from rich.console import Console

import MaterialX
from domain.models import ComponentInfo
from services.file_service import FileService
from services.template_service import TemplateService

console = Console()


class VariantMaterialXError(Exception):
    """变体MaterialX处理错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


class VariantMaterialXProcessor:
    """变体MaterialX处理器.

    负责处理支持变体的MaterialX文件创建。
    这个类重构了原来复杂的create_variant_materialx_file函数。
    """

    def __init__(self) -> None:
        """初始化变体MaterialX处理器."""
        self.file_service = FileService()
        self.template_service = TemplateService()

    def create_variant_materialx_file(
        self,
        component_info: ComponentInfo,
        output_mtlx_path: str,
    ) -> None:
        """创建支持变体的MaterialX文件.

        这是原来create_variant_materialx_file的重构版本，
        将复杂逻辑分解为多个小函数。

        Args:
            component_info: 组件信息（包含变体）
            output_mtlx_path: 输出MaterialX文件路径

        Raises
        ------
            VariantMaterialXError: 当处理失败时
        """
        if not component_info.has_variants:
            msg = f"组件 '{component_info.name}' 没有变体，应使用简单MaterialX创建"
            raise VariantMaterialXError(msg)

        temp_file = None

        try:
            # 1. 创建基础内容
            content = self._create_base_materialx_content(component_info)

            # 2. 写入临时文件
            temp_file = Path(output_mtlx_path).with_suffix(".temp.mtlx")
            self.file_service.write_file(temp_file, content)

            # 3. 创建MaterialX文档
            doc = MaterialX.createDocument()
            MaterialX.readFromXmlFile(doc, str(temp_file))

            # 4. 为每个变体创建节点图
            self._create_variant_node_graphs(doc, component_info)

            # 5. 移除原始节点图
            self._remove_original_node_graph(doc, component_info.name)

            # 6. 创建变体材质
            self._create_variant_materials(doc, component_info)

            # 7. 移除原始材质
            self._remove_original_materials(doc, component_info.name)

            # 8. 输出最终的MaterialX文件
            MaterialX.writeToXmlFile(doc, output_mtlx_path)

            console.print(
                f"[green]✓ 生成变体MaterialX文件: {Path(output_mtlx_path).name} "
                f"(包含{len(component_info.variants)}个变体)[/green]",
            )

        except Exception as e:
            if not isinstance(e, VariantMaterialXError):
                msg = f"创建变体MaterialX文件失败: {e}"
                raise VariantMaterialXError(msg) from e
            raise
        finally:
            # 清理临时文件
            if temp_file and temp_file.exists():
                temp_file.unlink(missing_ok=True)

    def _create_base_materialx_content(self, component_info: ComponentInfo) -> str:
        """创建基础MaterialX内容."""
        template_path = self.template_service.get_template_path(
            component_info.component_type,
            "{$component_name}_mat.mtlx",
        )

        if not template_path.exists():
            msg = f"MaterialX模板文件不存在: {template_path}"
            raise VariantMaterialXError(msg)

        # 读取模板内容
        template_content = self.file_service.read_file(template_path)

        # 使用模板替换基础变量
        from string import Template

        template = Template(template_content)
        return template.safe_substitute(component_name=component_info.name)

    def _create_variant_node_graphs(
        self,
        doc: MaterialX.Document,
        component_info: ComponentInfo,
    ) -> None:
        """为每个变体创建节点图."""
        base_ng = doc.getNodeGraph(f"NG_{component_info.name}")
        if not base_ng:
            msg = f"找不到基础节点图: NG_{component_info.name}"
            raise VariantMaterialXError(msg)

        for variant in component_info.variants:
            variant_ng_name = f"NG_{component_info.name}_{variant.name}"

            # 创建变体节点图
            variant_ng = doc.addNodeGraph(variant_ng_name)

            # 复制基础节点图的节点
            self._copy_nodes_to_variant_graph(base_ng, variant_ng)

            # 复制输出
            self._copy_outputs_to_variant_graph(base_ng, variant_ng)

            # 设置变体的纹理
            self._process_variant_textures(variant_ng, variant)

            # 清理未使用的节点
            self._cleanup_unused_image_nodes(variant_ng, set(variant.textures.keys()))

    def _copy_nodes_to_variant_graph(
        self,
        source_ng: MaterialX.NodeGraph,
        target_ng: MaterialX.NodeGraph,
    ) -> None:
        """复制节点到变体节点图."""
        for node in source_ng.getNodes():
            new_node = target_ng.addNode(node.getCategory(), node.getName())
            new_node.setType(node.getType())

            # 复制输入
            for input_elem in node.getInputs():
                new_input = new_node.addInput(input_elem.getName(), input_elem.getType())
                if input_elem.hasValue():
                    new_input.setValue(input_elem.getValue())

    def _copy_outputs_to_variant_graph(
        self,
        source_ng: MaterialX.NodeGraph,
        target_ng: MaterialX.NodeGraph,
    ) -> None:
        """复制输出到变体节点图."""
        for output in source_ng.getOutputs():
            new_output = target_ng.addOutput(output.getName(), output.getType())
            if output.hasNodeName():
                new_output.setNodeName(output.getNodeName())

    def _process_variant_textures(
        self,
        variant_ng: MaterialX.NodeGraph,
        variant,
    ) -> None:
        """处理变体纹理."""
        for node_name, texture_path in variant.textures.items():
            image_node = variant_ng.getNode(node_name)
            if image_node:
                # 添加file输入
                file_input = image_node.getInput("file")
                if not file_input:
                    file_input = image_node.addInput("file", "filename")
                file_input.setValueString(texture_path)
            else:
                console.print(
                    f"[yellow]⚠ 警告: 变体 '{variant.name}' 中未找到节点 {node_name}[/yellow]",
                )

    def _cleanup_unused_image_nodes(
        self,
        node_graph: MaterialX.NodeGraph,
        used_texture_types: set[str],
    ) -> None:
        """清理未使用的图像节点."""
        # 获取所有image节点
        image_nodes = [node for node in node_graph.getNodes() if node.getType() == "image"]

        # 删除未使用的image节点
        removed_count = 0
        for node in image_nodes:
            if node.getName() not in used_texture_types:
                node_graph.removeNode(node.getName())
                removed_count += 1

        if removed_count > 0:
            console.print(f"[blue]变体清理了 {removed_count} 个未使用的图像节点[/blue]")

    def _remove_original_node_graph(self, doc: MaterialX.Document, component_name: str) -> None:
        """移除原始节点图."""
        original_ng_name = f"NG_{component_name}"
        original_ng = doc.getNodeGraph(original_ng_name)
        if original_ng:
            doc.removeNodeGraph(original_ng_name)

    def _create_variant_materials(
        self,
        doc: MaterialX.Document,
        component_info: ComponentInfo,
    ) -> None:
        """创建变体材质."""
        for variant in component_info.variants:
            variant_material_name = f"M_{component_info.name}_{variant.name}"
            variant_shader_name = f"{component_info.name}_{variant.name}"
            variant_ng_name = f"NG_{component_info.name}_{variant.name}"

            # 创建变体着色器
            self._create_variant_shader(
                doc,
                variant_shader_name,
                variant_ng_name,
            )

            # 创建变体材质
            self._create_variant_material(
                doc,
                variant_material_name,
                variant_shader_name,
            )

    def _create_variant_shader(
        self,
        doc: MaterialX.Document,
        shader_name: str,
        node_graph_name: str,
    ) -> None:
        """创建变体着色器."""
        variant_shader = doc.addNode(
            "open_pbr_surface",
            shader_name,
            "surfaceshader",
        )

        # 连接节点图输出到着色器输入
        node_graph = doc.getNodeGraph(node_graph_name)
        if node_graph:
            self._connect_outputs_to_shader(node_graph, variant_shader, node_graph_name)

    def _connect_outputs_to_shader(
        self,
        node_graph: MaterialX.NodeGraph,
        shader: MaterialX.Node,
        node_graph_name: str,
    ) -> None:
        """连接节点图输出到着色器."""
        # 输出名称到着色器输入名称的映射
        input_mapping = {
            "base_color_output": "base_color",
            "metalness_output": "base_metalness",
            "roughness_output": "specular_roughness",
            "normal_output": "geometry_normal",
        }

        for output in node_graph.getOutputs():
            output_name = output.getName()
            if output_name.endswith("_output") and output_name in input_mapping:
                shader_input_name = input_mapping[output_name]
                shader_input = shader.getInput(shader_input_name)
                if not shader_input:
                    shader_input = shader.addInput(
                        shader_input_name,
                        output.getType(),
                    )
                shader_input.setNodeGraphString(node_graph_name)
                shader_input.setOutputString(output_name)

    def _create_variant_material(
        self,
        doc: MaterialX.Document,
        material_name: str,
        shader_name: str,
    ) -> None:
        """创建变体材质."""
        variant_material = doc.addNode(
            "surfacematerial",
            material_name,
            "material",
        )

        surface_input = variant_material.getInput("surfaceshader")
        if not surface_input:
            surface_input = variant_material.addInput("surfaceshader", "surfaceshader")
        surface_input.setNodeName(shader_name)

    def _remove_original_materials(self, doc: MaterialX.Document, component_name: str) -> None:
        """移除原始材质和着色器."""
        # 移除原始着色器
        original_shader = doc.getNode(component_name)
        if original_shader:
            doc.removeNode(component_name)

        # 移除原始材质
        original_material = doc.getNode(f"M_{component_name}")
        if original_material:
            doc.removeNode(f"M_{component_name}")
