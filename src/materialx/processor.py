"""MaterialX文件处理器."""

from pathlib import Path

from rich.console import Console

import MaterialX
from domain.enums import ComponentType
from domain.exceptions import MaterialXError
from domain.models import ComponentInfo, VariantInfo
from services.file_service import FileService
from services.template_service import TemplateService

console = Console()


class MaterialXProcessor:
    """MaterialX文件处理器.

    负责处理MaterialX文件的创建、纹理连接等操作。
    """

    def __init__(self) -> None:
        """初始化MaterialX处理器."""
        self.file_service = FileService()
        self.template_service = TemplateService()

    def create_materialx_from_component_info(
        self,
        component_info: ComponentInfo,
        output_mtlx_path: str,
    ) -> None:
        """根据组件信息创建MaterialX文件.

        Args:
            component_info: 组件信息
            output_mtlx_path: 输出MaterialX文件路径

        Raises
        ------
            MaterialXError: 当处理失败时
        """
        if component_info.has_variants:
            self._create_variant_materialx_file(component_info, output_mtlx_path)
        else:
            self._create_simple_materialx_file(
                component_info.name,
                component_info.textures,
                output_mtlx_path,
                component_info.component_type,
            )

    def _create_variant_materialx_file(
        self,
        component_info: ComponentInfo,
        output_mtlx_path: str,
    ) -> None:
        """创建支持变体的MaterialX文件.

        Args:
            component_info: 组件信息
            output_mtlx_path: 输出MaterialX文件路径

        Raises
        ------
            MaterialXError: 当处理失败时
        """
        try:
            # 创建基础内容
            content = self._create_base_materialx_content(
                component_info.name,
                component_info.component_type,
            )

            # 使用内存中的XML处理，避免临时文件
            doc = MaterialX.createDocument()
            self._load_xml_from_string(doc, content)

            # 查找节点图
            compound_ng = doc.getNodeGraph(f"NG_{component_info.name}")
            if not compound_ng:
                self._raise_error(f"找不到节点图: NG_{component_info.name}")

            # 为每个变体创建材质
            for variant in component_info.variants:
                self._create_variant_material(doc, compound_ng, variant)

            # 输出最终的MaterialX文件
            MaterialX.writeToXmlFile(doc, output_mtlx_path)

            console.print(
                f"[green]✓ 生成MaterialX文件: {Path(output_mtlx_path).name} "
                f"(包含{len(component_info.variants)}个变体)[/green]",
            )

        except Exception as e:
            if not isinstance(e, MaterialXError):
                self._raise_error(f"创建变体MaterialX文件失败: {e}")
            raise

    def _create_simple_materialx_file(
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
        try:
            # 创建基础内容
            content = self._create_base_materialx_content(component_name, component_type)

            # 使用内存中的XML处理，避免临时文件
            doc = MaterialX.createDocument()
            self._load_xml_from_string(doc, content)

            # 查找节点图
            compound_ng = doc.getNodeGraph(f"NG_{component_name}")
            if not compound_ng:
                self._raise_error(f"找不到节点图: NG_{component_name}")

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
                self._raise_error(f"创建MaterialX文件失败: {e}")
            raise

    def _raise_error(self, message: str) -> None:
        """统一的错误抛出函数.

        Args:
            message: 错误消息

        Raises
        ------
            MaterialXError: 统一的MaterialX错误
        """
        raise MaterialXError(message)

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
            "{$component_or_subcomponent_name}_mat.mtlx",
        )

        if not template_path.exists():
            self._raise_error(f"MaterialX模板文件不存在: {template_path}")

        # 读取模板内容
        template_content = self.file_service.read_file(template_path)

        # 使用模板替换基础变量
        from string import Template

        template = Template(template_content)
        return template.safe_substitute(component_or_subcomponent_name=component_name)

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
                console.print(f"[blue]✓ 连接纹理: {node_name} -> {texture_path}[/blue]")
            else:
                console.print(f"[yellow]⚠ 未找到图像节点: {node_name}[/yellow]")

        return added_textures

    def _create_variant_material(
        self,
        doc: MaterialX.Document,
        compound_ng: MaterialX.NodeGraph,
        variant: "VariantInfo",
    ) -> None:
        """为变体创建材质.

        Args:
            doc: MaterialX文档
            compound_ng: 复合节点图
            variant: 变体信息
        """
        # 创建变体节点图
        variant_ng = doc.addNodeGraph(f"NG_{variant.name}")
        variant_ng.setCategory("texture2d")

        # 复制基础节点图的内容
        self._copy_node_graph_content(compound_ng, variant_ng)

        # 处理变体的纹理
        self._process_texture_nodes(variant_ng, variant.textures, variant.name)

        # 创建变体着色器
        variant_shader = doc.addNode(
            "open_pbr_surface",
            f"{variant.name}_shader",
            "surfaceshader",
        )

        # 连接节点图输出到着色器输入
        self._connect_outputs_to_shader(variant_ng, variant_shader, variant_ng.getName())

        # 创建变体材质
        variant_material = doc.addNode(
            "surfacematerial",
            f"MT_{variant.name}",
            "material",
        )

        # 连接着色器到材质
        surface_input = variant_material.getInput("surfaceshader")
        if not surface_input:
            surface_input = variant_material.addInput("surfaceshader", "surfaceshader")
        surface_input.setNodeName(variant_shader.getName())

    def _copy_node_graph_content(
        self,
        source_ng: MaterialX.NodeGraph,
        target_ng: MaterialX.NodeGraph,
    ) -> None:
        """复制节点图内容.

        Args:
            source_ng: 源节点图
            target_ng: 目标节点图
        """
        # 复制所有节点
        for node in source_ng.getNodes():
            new_node = target_ng.addNode(node.getCategory(), node.getName())
            # 复制节点属性
            for input_port in node.getInputs():
                new_input = new_node.addInput(input_port.getName(), input_port.getType())
                new_input.setValueString(input_port.getValueString())

    def _cleanup_unused_image_nodes(
        self,
        node_graph: MaterialX.NodeGraph,
        used_texture_types: set[str],
    ) -> None:
        """清理未使用的图像节点.

        Args:
            node_graph: MaterialX节点图
            used_texture_types: 使用的纹理类型集合
        """
        nodes_to_remove = []
        for node in node_graph.getNodes():
            if node.getCategory() == "image" and node.getName() not in used_texture_types:
                nodes_to_remove.append(node)

        for node in nodes_to_remove:
            node_graph.removeNode(node.getName())
            console.print(f"[blue]✓ 清理未使用的图像节点: {node.getName()}[/blue]")

    def _connect_outputs_to_shader(
        self,
        node_graph: MaterialX.NodeGraph,
        shader: MaterialX.Node,
        node_graph_name: str,
    ) -> None:
        """连接节点图输出到着色器.

        Args:
            node_graph: 节点图
            shader: 着色器节点
            node_graph_name: 节点图名称
        """
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

    def _load_xml_from_string(self, doc: MaterialX.Document, xml_content: str) -> None:
        """从字符串加载XML到MaterialX文档.

        Args:
            doc: MaterialX文档
            xml_content: XML内容字符串

        Raises
        ------
            MaterialXError: 当XML解析失败时
        """
        try:
            # 尝试使用readFromXmlString（如果可用）
            if hasattr(MaterialX, "readFromXmlString"):
                MaterialX.readFromXmlString(doc, xml_content)
            else:
                # 回退到临时文件方法
                import tempfile

                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".mtlx",
                    delete=False,
                ) as temp_file:
                    temp_file.write(xml_content)
                    temp_file.flush()
                    try:
                        MaterialX.readFromXmlFile(doc, temp_file.name)
                    finally:
                        import os

                        os.unlink(temp_file.name)
        except Exception as e:
            self._raise_error(f"解析MaterialX XML失败: {e}")
