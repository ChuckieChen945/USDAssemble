#!/usr/bin/env python3
"""MaterialX Chess Board Material Processor.

加载原始MaterialX文件，连接贴图文件，并输出修改后的材质文件
"""

from pathlib import Path
from string import Template

import MaterialX
from rich.console import Console

from usdassemble.utils import get_template_dir

console = Console()


class MaterialXError(Exception):
    """MaterialX 处理错误."""

    def __init__(self, message: str) -> None:
        super().__init__(message)


def create_materialx_file(
    component_name: str,
    texture_files: dict[str, str],
    output_mtlx_path: str,
) -> None:
    """处理棋盘材质：从模板创建MaterialX文件，连接贴图，并输出新文件.

    Args:
        component_name: 组件名称
        texture_files: 纹理文件映射 {纹理类型: 相对路径}
        output_mtlx_path: 输出MaterialX文件路径

    Raises
    ------
        MaterialXError: 当处理失败时
    """
    try:
        # 获取模板路径
        template_mtlx_path = (
            get_template_dir()
            / "{$assembly_name}"
            / "components"
            / "{$component_name}"
            / "{$component_name}_mat.mtlx"
        )

        if not template_mtlx_path.exists():
            msg = f"MaterialX模板文件不存在: {template_mtlx_path}"

        # 使用模板替换基础变量
        with Path.open(template_mtlx_path, encoding="utf-8") as f:
            template_content = f.read()

        template = Template(template_content)
        content = template.safe_substitute(component_name=component_name)

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

        # 为每个image节点添加file输入
        added_textures = []
        for node_name, texture_path in texture_files.items():
            image_node = compound_ng.getNode(node_name)
            if image_node:
                # 添加file输入
                file_input = image_node.getInput("file")
                file_input.setValueString(texture_path)

                added_textures.append(node_name)
            else:
                console.print(f"[yellow]⚠ 警告: 节点图中未找到节点 {node_name}[/yellow]")

        # 清理未使用的图像节点
        _cleanup_unused_image_nodes(compound_ng, set(texture_files.keys()))

        # 输出最终的MaterialX文件
        MaterialX.writeToXmlFile(doc, output_mtlx_path)

        # 清理临时文件
        temp_file.unlink(missing_ok=True)

        console.print(
            f"[green]✓ 生成MaterialX文件: {Path(output_mtlx_path).name} (包含{len(added_textures)}个纹理)[/green]",
        )

    except Exception as e:
        # 清理临时文件
        if "temp_file" in locals():
            temp_file.unlink(missing_ok=True)
        if not msg:
            msg = f"创建MaterialX文件失败: {e}"
        raise MaterialXError(msg) from e


def _cleanup_unused_image_nodes(node_graph: MaterialX.NodeGraph, used_texture_types: set) -> None:
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
