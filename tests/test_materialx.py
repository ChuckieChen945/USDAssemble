#!/usr/bin/env python3
"""测试MaterialX功能."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from mtlx.materialx import (
    MaterialXError,
    _cleanup_unused_image_nodes,
    _update_shader_nodes,
    create_materialx_file,
)


class TestCreateMaterialXFile:
    """测试create_materialx_file函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("mtlx.materialx.get_template_dir")
    @patch("mtlx.materialx.mx.createDocument")
    @patch("mtlx.materialx.mx.readFromXmlFile")
    @patch("mtlx.materialx.mx.writeToXmlFile")
    @patch("mtlx.materialx.console")
    def test_create_materialx_file_success(
        self,
        mock_console,
        mock_write_xml,
        mock_read_xml,
        mock_create_doc,
        mock_get_template_dir,
    ):
        """测试成功创建MaterialX文件."""
        # 模拟模板目录
        template_dir = Path("/mock/template")
        mock_get_template_dir.return_value = template_dir

        template_path = (
            template_dir
            / "{$assembly_name}"
            / "components"
            / "{$component_name}"
            / "{$component_name}_mat.mtlx"
        )
        template_content = """<?xml version="1.0"?>
<materialx version="1.38">
  <nodegraph name="NG_${component_name}">
    <image name="base_color" type="color3" />
    <image name="metallic" type="float" />
  </nodegraph>
  <open_pbr_surface name="component_name" type="surfaceshader">
  </open_pbr_surface>
  <surfacematerial name="M_${component_name}" type="material">
  </surfacematerial>
</materialx>"""

        # 模拟MaterialX文档
        mock_doc = Mock()
        mock_create_doc.return_value = mock_doc

        # 模拟节点图
        mock_node_graph = Mock()
        mock_node_graph.getName.return_value = "NG_test_component"
        mock_doc.getNodeGraph.return_value = mock_node_graph

        # 模拟图像节点
        mock_base_color_node = Mock()
        mock_metallic_node = Mock()
        mock_unused_node = Mock()
        mock_unused_node.getType.return_value = "image"
        mock_unused_node.getName.return_value = "unused_texture"

        def mock_get_node(name):
            if name == "base_color":
                return mock_base_color_node
            if name == "metallic":
                return mock_metallic_node
            return None

        mock_node_graph.getNode.side_effect = mock_get_node
        mock_node_graph.getNodes.return_value = [
            mock_base_color_node,
            mock_metallic_node,
            mock_unused_node,
        ]

        # 模拟shader节点
        mock_pbr_node = Mock()
        mock_material_node = Mock()
        mock_shader_input = Mock()
        mock_material_node.getInput.return_value = mock_shader_input

        def mock_get_doc_node(name):
            if name == "component_name":
                return mock_pbr_node
            if name == "M_test_component":
                return mock_material_node
            return None

        mock_doc.getNode.side_effect = mock_get_doc_node

        # 模拟文件操作
        with patch("builtins.open", mock_open(read_data=template_content)):
            # 执行函数
            component_name = "test_component"
            texture_files = {
                "base_color": "textures/test_base_color.jpg",
                "metallic": "textures/test_metallic.png",
            }
            output_path = str(self.temp_dir / "test_mat.mtlx")

            create_materialx_file(component_name, texture_files, output_path)

            # 验证调用
            mock_read_xml.assert_called_once()
            mock_write_xml.assert_called_once_with(mock_doc, output_path)

            # 验证节点配置
            mock_base_color_node.addInput.assert_called_once_with("file", "filename")
            mock_metallic_node.addInput.assert_called_once_with("file", "filename")

    @patch("mtlx.materialx.get_template_dir")
    def test_create_materialx_file_template_not_found(self, mock_get_template_dir):
        """测试模板文件不存在的情况."""
        mock_get_template_dir.return_value = Path("/nonexistent")

        with pytest.raises(MaterialXError) as exc_info:
            create_materialx_file("test", {}, "output.mtlx")

        assert "模板文件不存在" in str(exc_info.value)

    @patch("mtlx.materialx.get_template_dir")
    @patch("mtlx.materialx.mx.createDocument")
    @patch("mtlx.materialx.mx.readFromXmlFile")
    def test_create_materialx_file_missing_node_graph(
        self,
        mock_read_xml,
        mock_create_doc,
        mock_get_template_dir,
    ):
        """测试找不到节点图的情况."""
        # 模拟模板目录和文件
        template_dir = Path("/mock/template")
        mock_get_template_dir.return_value = template_dir

        mock_doc = Mock()
        mock_create_doc.return_value = mock_doc
        mock_doc.getNodeGraph.return_value = None  # 找不到节点图

        template_content = "mock template content"
        with patch("builtins.open", mock_open(read_data=template_content)):
            with pytest.raises(MaterialXError) as exc_info:
                create_materialx_file("test_component", {}, "output.mtlx")

            assert "找不到节点图" in str(exc_info.value)

    @patch("mtlx.materialx.get_template_dir")
    @patch("mtlx.materialx.mx.createDocument")
    @patch("mtlx.materialx.mx.readFromXmlFile")
    @patch("mtlx.materialx.console")
    def test_create_materialx_file_missing_image_node(
        self,
        mock_console,
        mock_read_xml,
        mock_create_doc,
        mock_get_template_dir,
    ):
        """测试节点图中缺少图像节点的情况."""
        # 模拟设置
        mock_get_template_dir.return_value = Path("/mock/template")

        mock_doc = Mock()
        mock_create_doc.return_value = mock_doc

        mock_node_graph = Mock()
        mock_node_graph.getNode.return_value = None  # 找不到图像节点
        mock_node_graph.getNodes.return_value = []
        mock_doc.getNodeGraph.return_value = mock_node_graph

        mock_doc.getNode.return_value = None

        template_content = "mock template content"
        with patch("builtins.open", mock_open(read_data=template_content)):
            with patch("mtlx.materialx.mx.writeToXmlFile"):
                # 应该不报错，但会有警告
                create_materialx_file("test_component", {"base_color": "test.jpg"}, "output.mtlx")

                # 验证警告信息
                mock_console.print.assert_any_call(
                    "[yellow]⚠ 警告: 节点图中未找到节点 base_color[/yellow]",
                )


class TestCleanupUnusedImageNodes:
    """测试_cleanup_unused_image_nodes函数."""

    def test_cleanup_unused_image_nodes(self):
        """测试清理未使用的图像节点."""
        # 创建模拟节点
        used_node = Mock()
        used_node.getType.return_value = "image"
        used_node.getName.return_value = "base_color"

        unused_node = Mock()
        unused_node.getType.return_value = "image"
        unused_node.getName.return_value = "unused_texture"

        other_node = Mock()
        other_node.getType.return_value = "multiply"
        other_node.getName.return_value = "multiply1"

        # 模拟节点图
        mock_node_graph = Mock()
        mock_node_graph.getNodes.return_value = [used_node, unused_node, other_node]

        # 执行函数
        used_texture_types = {"base_color", "metallic"}

        with patch("mtlx.materialx.console") as mock_console:
            _cleanup_unused_image_nodes(mock_node_graph, used_texture_types)

            # 验证只移除了未使用的图像节点
            mock_node_graph.removeNode.assert_called_once_with("unused_texture")
            mock_console.print.assert_called_once()

    def test_cleanup_unused_image_nodes_none_to_remove(self):
        """测试没有需要清理的节点的情况."""
        # 创建模拟节点（都被使用）
        used_node = Mock()
        used_node.getType.return_value = "image"
        used_node.getName.return_value = "base_color"

        mock_node_graph = Mock()
        mock_node_graph.getNodes.return_value = [used_node]

        used_texture_types = {"base_color"}

        with patch("mtlx.materialx.console") as mock_console:
            _cleanup_unused_image_nodes(mock_node_graph, used_texture_types)

            # 验证没有移除任何节点
            mock_node_graph.removeNode.assert_not_called()
            mock_console.print.assert_not_called()


class TestUpdateShaderNodes:
    """测试_update_shader_nodes函数."""

    def test_update_shader_nodes_success(self):
        """测试成功更新shader节点."""
        # 模拟PBR surface节点
        mock_pbr_surface = Mock()

        # 模拟材质节点
        mock_material = Mock()
        mock_shader_input = Mock()
        mock_material.getInput.return_value = mock_shader_input

        # 模拟文档
        mock_doc = Mock()

        def mock_get_node(name):
            if name == "component_name":
                return mock_pbr_surface
            if name == "M_test_component":
                return mock_material
            return None

        mock_doc.getNode.side_effect = mock_get_node

        # 执行函数
        _update_shader_nodes(mock_doc, "test_component")

        # 验证调用
        mock_pbr_surface.setName.assert_called_once_with("test_component")
        mock_shader_input.setNodeName.assert_called_once_with("test_component")

    def test_update_shader_nodes_missing_nodes(self):
        """测试缺少节点的情况."""
        mock_doc = Mock()
        mock_doc.getNode.return_value = None  # 所有节点都找不到

        # 执行函数（应该不报错）
        _update_shader_nodes(mock_doc, "test_component")

        # 验证没有设置操作
        mock_doc.getNode.assert_called()

    def test_update_shader_nodes_missing_shader_input(self):
        """测试材质节点缺少shader输入的情况."""
        # 模拟PBR surface节点
        mock_pbr_surface = Mock()

        # 模拟材质节点（无shader输入）
        mock_material = Mock()
        mock_material.getInput.return_value = None

        mock_doc = Mock()

        def mock_get_node(name):
            if name == "component_name":
                return mock_pbr_surface
            if name == "M_test_component":
                return mock_material
            return None

        mock_doc.getNode.side_effect = mock_get_node

        # 执行函数（应该不报错）
        _update_shader_nodes(mock_doc, "test_component")

        # 验证PBR surface仍然被重命名
        mock_pbr_surface.setName.assert_called_once_with("test_component")
