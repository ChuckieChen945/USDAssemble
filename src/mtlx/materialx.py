#!/usr/bin/env python3
"""MaterialX Chess Board Material Processor.

加载原始MaterialX文件，连接贴图文件，并输出修改后的材质文件
"""

from pathlib import Path

import MaterialX as mx


def create_materialx_file(component_path: str, component_name: str, texture_files: dict[str, str]) -> None:
    """处理棋盘材质：加载原始MaterialX文件，连接贴图，并输出新文件."""
    # 创建MaterialX文档
    doc = mx.createDocument()

    # 加载原始MaterialX文件
    # TODO: 当前脚本文件路径下的"open_pbr.mtlx"
    input_file = "open_pbr.mtlx"
    output_file = Path(component_path) / f"{component_name}_mat.mtlx"

    try:
        # 读取原始文件
        mx.readFromXmlFile(doc, input_file)
        print(f"成功加载模板材质文件: {input_file}")

        # 查找compound1节点图
        compound_ng = doc.getNodeGraph("compound1")
        if not compound_ng:
            print("错误: 找不到compound1节点图")
            return False

        # 重命名节点图为NG_ChessBoard
        compound_ng.setName(f"NG_{component_name}")
        print(f"已重命名节点图为: NG_{component_name}")

        # 为每个image节点添加file输入
        # TODO 删除多余的，没有载入贴图的节点
        for node_name, texture_path in texture_files.items():
            image_node = compound_ng.getNode(node_name)
            if image_node:
                # 添加file输入
                file_input = image_node.addInput("file", "filename")
                file_input.setValue(texture_path)

                # 为base color贴图设置colorspace
                if node_name == "base_color":
                    file_input.setAttribute("colorspace", "srgb_texture")

                print(f"已为节点 {node_name} 添加贴图: {texture_path}")
            else:
                print(f"警告: 找不到节点 {node_name}")

        # 查找并修改shader节点
        # 找到open_pbr_surface节点并重命名
        pbr_surface = doc.getNode("open_pbr_surface1")
        if pbr_surface:
            pbr_surface.setName(f"{component_name}")

        # 修改材质节点名称
        material = doc.getNode("OpenPBR_Surface1")
        if material:
            material.setName(f"M_{component_name}")
            # 更新surfaceshader输入的引用
            shader_input = material.getInput("surfaceshader")
            if shader_input:
                shader_input.setNodeName(f"{component_name}")
            print(f"已重命名材质节点为: M_{component_name}")

        # 输出修改后的MaterialX文件
        mx.writeToXmlFile(doc, output_file)
        print(f"\n成功输出材质文件: {output_file}")

        return True

    except Exception as e:
        print(f"处理过程中发生错误: {e!s}")
        return False
