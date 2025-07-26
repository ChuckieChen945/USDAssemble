#!/usr/bin/env python3
"""
MaterialX Chess Board Material Processor
加载原始MaterialX文件，连接贴图文件，并输出修改后的材质文件
"""

import os

import MaterialX as mx


def process_chessboard_material():
    """
    处理棋盘材质：加载原始MaterialX文件，连接贴图，并输出新文件
    """
    # 创建MaterialX文档
    doc = mx.createDocument()

    # 加载原始MaterialX文件
    input_file = "Chessboard_mat.mtlx"
    output_file = "Chessboard_mat_out.mtlx"

    try:
        # 读取原始文件
        mx.readFromXmlFile(doc, input_file)
        print(f"成功加载原始材质文件: {input_file}")

        # 查找compound1节点图
        compound_ng = doc.getNodeGraph("compound1")
        if not compound_ng:
            print("错误: 找不到compound1节点图")
            return False

        # 重命名节点图为NG_ChessBoard
        compound_ng.setName("NG_ChessBoard")
        print("已重命名节点图为: NG_ChessBoard")

        # 定义贴图文件路径映射
        texture_mappings = {
            "mtlximage13": "tex/chessboard_base_color.jpg",  # base color
            "mtlximage16": "tex/chessboard_metallic.jpg",  # metallic
            "mtlximage17": "tex/chessboard_roughness.jpg",  # roughness
            "mtlximage15": "tex/chessboard_normal.jpg",  # normal
        }

        # 为每个image节点添加file输入
        for node_name, texture_path in texture_mappings.items():
            image_node = compound_ng.getNode(node_name)
            if image_node:
                # 添加file输入
                file_input = image_node.addInput("file", "filename")
                file_input.setValue(texture_path)

                # 为base color贴图设置colorspace
                if node_name == "mtlximage13":
                    file_input.setAttribute("colorspace", "srgb_texture")

                print(f"已为节点 {node_name} 添加贴图: {texture_path}")
            else:
                print(f"警告: 找不到节点 {node_name}")

        # 查找并修改shader节点
        # 找到open_pbr_surface节点并重命名为standard_surface
        pbr_surface = doc.getNode("open_pbr_surface1")
        if pbr_surface:
            # 创建新的standard_surface节点
            standard_surface = doc.addNode(
                "standard_surface", "Chessboard", "surfaceshader"
            )

            # 重新连接输入，映射到standard_surface的对应输入
            input_mappings = {
                "base_color": "base_color",
                "base_metalness": "metalness",
                "specular_roughness": "specular_roughness",
                "geometry_normal": "normal",
            }

            for old_input_name, new_input_name in input_mappings.items():
                old_input = pbr_surface.getInput(old_input_name)
                if old_input:
                    new_input = standard_surface.addInput(
                        new_input_name, old_input.getType()
                    )
                    if old_input.getNodeGraphString():
                        new_input.setNodeGraphString(old_input.getNodeGraphString())
                        new_input.setOutputString(old_input.getOutputString())

            # 删除旧的open_pbr_surface节点
            doc.removeNode("open_pbr_surface1")
            print("已将open_pbr_surface1替换为standard_surface节点: Chessboard")

        # 修改材质节点名称
        material = doc.getNode("OpenPBR_Surface1")
        if material:
            material.setName("M_Chessboard")
            # 更新surfaceshader输入的引用
            shader_input = material.getInput("surfaceshader")
            if shader_input:
                shader_input.setNodeName("Chessboard")
            print("已重命名材质节点为: M_Chessboard")

        # 验证贴图文件是否存在
        print("\n验证贴图文件:")
        for texture_path in texture_mappings.values():
            if os.path.exists(texture_path):
                print(f"✓ {texture_path}")
            else:
                print(f"✗ {texture_path} (文件不存在)")

        # 输出修改后的MaterialX文件
        mx.writeToXmlFile(doc, output_file)
        print(f"\n成功输出材质文件: {output_file}")

        # 显示节点图结构
        print("\n节点图结构:")
        ng = doc.getNodeGraph("NG_ChessBoard")
        if ng:
            print(f"节点图: {ng.getName()}")
            for node in ng.getNodes():
                print(f"  节点: {node.getName()} (类型: {node.getCategory()})")
                for input_port in node.getInputs():
                    try:
                        value = input_port.getValue()
                        if value:
                            print(f"    输入 {input_port.getName()}: {value}")
                    except:
                        # 如果没有值或获取值失败，跳过
                        pass

        print("\n材质节点:")
        for material in doc.getMaterials():
            print(f"材质: {material.getName()}")

        return True

    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        return False


def main():
    """
    主函数
    """
    print("=== MaterialX 棋盘材质处理器 ===\n")

    # 检查输入文件是否存在
    if not os.path.exists("Chessboard_mat.mtlx"):
        print("错误: 找不到输入文件 Chessboard_mat.mtlx")
        return

    # 检查贴图目录是否存在
    if not os.path.exists("tex"):
        print("错误: 找不到贴图目录 tex/")
        return

    # 处理材质
    success = process_chessboard_material()

    if success:
        print("\n✓ 材质处理完成！")
        print("输出文件: Chessboard_mat_out.mtlx")
    else:
        print("\n✗ 材质处理失败")


if __name__ == "__main__":
    main()
