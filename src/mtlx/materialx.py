#!/usr/bin/env python3
"""MaterialX 材质处理器.

处理USD组件的MaterialX材质文件，支持变体装配
"""

from pathlib import Path
from string import Template

import MaterialX
from rich.console import Console

from usdassemble.utils import (
    ComponentInfo,
    ComponentType,
    get_template_dir,
)

console = Console()


class MaterialXError(Exception):
    """MaterialX 处理错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def _get_materialx_template_path(component_type: ComponentType) -> Path:
    """获取MaterialX模板文件路径.

    Args:
        component_type: 组件类型

    Returns
    -------
        Path: 模板文件路径
    """
    return (
        get_template_dir()
        / "{$assembly_name}"
        / component_type.directory
        / "{$component_name}"
        / "{$component_name}_mat.mtlx"
    )


def _create_base_materialx_content(
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
    template_path = _get_materialx_template_path(component_type)

    if not template_path.exists():
        msg = f"MaterialX模板文件不存在: {template_path}"
        raise MaterialXError(msg)

    # 使用模板替换基础变量
    with Path.open(template_path, encoding="utf-8") as f:
        template_content = f.read()

    template = Template(template_content)
    return template.safe_substitute(component_name=component_name)


def _process_texture_nodes(
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
    node_graph: MaterialX.NodeGraph,
    used_texture_types: set,
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


def create_simple_materialx_file(
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
        content = _create_base_materialx_content(component_name, component_type)

        # 写入临时文件用于MaterialX处理
        temp_file = Path(output_mtlx_path).with_suffix(".temp.mtlx")
        with Path.open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)

        # 创建MaterialX文档并处理
        doc = MaterialX.createDocument()
        MaterialX.readFromXmlFile(doc, str(temp_file))

        # 查找节点图
        compound_ng = doc.getNodeGraph(f"NG_{component_name}")
        if not compound_ng:
            msg = f"找不到节点图: NG_{component_name}"
            raise MaterialXError(msg)

        # 处理纹理节点
        added_textures = _process_texture_nodes(compound_ng, texture_files)

        # 清理未使用的图像节点
        _cleanup_unused_image_nodes(compound_ng, set(texture_files.keys()))

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


# TODO：`create_variant_materialx_file` is too complex，重构
def create_variant_materialx_file(
    component_info: ComponentInfo,
    output_mtlx_path: str,
) -> None:
    """创建支持变体的MaterialX文件.

    Args:
        component_info: 组件信息（包含变体）
        output_mtlx_path: 输出MaterialX文件路径

    Raises
    ------
        MaterialXError: 当处理失败时
    """
    if not component_info.has_variants:
        msg = f"组件 '{component_info.name}' 没有变体，应使用简单MaterialX创建"
        raise MaterialXError(msg)

    temp_file = None

    try:
        # 创建基础内容
        content = _create_base_materialx_content(
            component_info.name,
            component_info.component_type,
        )

        # 写入临时文件
        temp_file = Path(output_mtlx_path).with_suffix(".temp.mtlx")
        with Path.open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)

        # 创建MaterialX文档
        doc = MaterialX.createDocument()
        MaterialX.readFromXmlFile(doc, str(temp_file))

        # 为每个变体创建节点图
        for variant in component_info.variants:
            variant_ng_name = f"NG_{component_info.name}_{variant.name}"

            # 复制基础节点图
            base_ng = doc.getNodeGraph(f"NG_{component_info.name}")
            if not base_ng:
                msg = f"找不到基础节点图: NG_{component_info.name}"
                raise MaterialXError(msg)

            # 创建变体节点图
            variant_ng = doc.addNodeGraph(variant_ng_name)

            # 复制基础节点图的节点
            for node in base_ng.getNodes():
                new_node = variant_ng.addNode(node.getCategory(), node.getName())
                new_node.setType(node.getType())

                # 复制输入
                for input_elem in node.getInputs():
                    new_input = new_node.addInput(input_elem.getName(), input_elem.getType())
                    if input_elem.hasValue():
                        new_input.setValue(input_elem.getValue())

            # 复制输出
            for output in base_ng.getOutputs():
                new_output = variant_ng.addOutput(output.getName(), output.getType())
                if output.hasNodeName():
                    new_output.setNodeName(output.getNodeName())

            # 设置变体的纹理
            _process_texture_nodes(variant_ng, variant.textures, variant.name)

            # 清理未使用的节点
            _cleanup_unused_image_nodes(variant_ng, set(variant.textures.keys()))

        # 移除原始节点图（保留变体节点图）
        doc.removeNodeGraph(f"NG_{component_info.name}")

        # 创建变体材质
        for variant in component_info.variants:
            variant_material_name = f"M_{component_info.name}_{variant.name}"
            variant_shader_name = f"{component_info.name}_{variant.name}"
            variant_ng_name = f"NG_{component_info.name}_{variant.name}"

            # 创建变体着色器
            variant_shader = doc.addNode(
                "open_pbr_surface",
                variant_shader_name,
                "surfaceshader",
            )

            # 连接节点图输出到着色器输入
            for output in doc.getNodeGraph(variant_ng_name).getOutputs():
                output_name = output.getName()
                if output_name.endswith("_output"):
                    # 映射输出名称到着色器输入名称
                    input_mapping = {
                        "base_color_output": "base_color",
                        "metalness_output": "base_metalness",
                        "roughness_output": "specular_roughness",
                        "normal_output": "geometry_normal",
                    }

                    if output_name in input_mapping:
                        shader_input_name = input_mapping[output_name]
                        shader_input = variant_shader.getInput(shader_input_name)
                        if not shader_input:
                            shader_input = variant_shader.addInput(
                                shader_input_name,
                                output.getType(),
                            )
                        shader_input.setNodeGraphString(variant_ng_name)
                        shader_input.setOutputString(output_name)

            # 创建变体材质
            variant_material = doc.addNode(
                "surfacematerial",
                variant_material_name,
                "material",
            )

            surface_input = variant_material.getInput("surfaceshader")
            if not surface_input:
                surface_input = variant_material.addInput("surfaceshader", "surfaceshader")
            surface_input.setNodeName(variant_shader_name)

        # 移除原始材质和着色器
        original_shader = doc.getNode(component_info.name)
        if original_shader:
            doc.removeNode(component_info.name)

        original_material = doc.getNode(f"M_{component_info.name}")
        if original_material:
            doc.removeNode(f"M_{component_info.name}")

        # 输出最终的MaterialX文件
        MaterialX.writeToXmlFile(doc, output_mtlx_path)

        console.print(
            f"[green]✓ 生成变体MaterialX文件: {Path(output_mtlx_path).name} "
            f"(包含{len(component_info.variants)}个变体)[/green]",
        )

    except Exception as e:
        if not isinstance(e, MaterialXError):
            msg = f"创建变体MaterialX文件失败: {e}"
            raise MaterialXError(msg) from e
        raise
    finally:
        # 清理临时文件
        if temp_file and temp_file.exists():
            temp_file.unlink(missing_ok=True)


def create_materialx_file(
    component_name: str,
    texture_files: dict[str, str],
    output_mtlx_path: str,
    component_type: ComponentType = ComponentType.COMPONENT,
) -> None:
    """创建MaterialX文件（兼容原接口）.

    Args:
        component_name: 组件名称
        texture_files: 纹理文件映射 {纹理类型: 相对路径}
        output_mtlx_path: 输出MaterialX文件路径
        component_type: 组件类型

    Raises
    ------
        MaterialXError: 当处理失败时
    """
    # 为了保持向后兼容，委托给简单MaterialX创建函数
    create_simple_materialx_file(
        component_name,
        texture_files,
        output_mtlx_path,
        component_type,
    )


def create_materialx_from_component_info(
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
        create_variant_materialx_file(component_info, output_mtlx_path)
    else:
        create_simple_materialx_file(
            component_info.name,
            component_info.textures,
            output_mtlx_path,
            component_info.component_type,
        )
