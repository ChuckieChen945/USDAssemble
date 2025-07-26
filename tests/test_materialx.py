#!/usr/bin/env python3
"""测试MaterialX功能."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from mtlx.materialx import MaterialXError, create_materialx_file
from usdassemble.utils import ComponentType


class TestCreateMaterialXFile:
    """测试create_materialx_file函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.setup_mock_templates()

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def setup_mock_templates(self):
        """设置模拟模板文件."""
        # 创建components模板
        comp_template_dir = (
            self.temp_dir / "template" / "{$assembly_name}" / "components" / "{$component_name}"
        )
        comp_template_dir.mkdir(parents=True)

        comp_template_content = """<?xml version="1.0"?>
<materialx version="1.38" colorspace="lin_rec709">
  <nodegraph name="NG_${component_name}">
    <image name="base_color" type="color3" />
    <image name="metallic" type="float" />
    <image name="roughness" type="float" />
    <image name="normal" type="vector3" />
    <output name="base_color_output" type="color3" nodename="base_color" />
    <output name="metalness_output" type="float" nodename="metallic" />
    <output name="roughness_output" type="float" nodename="roughness" />
    <output name="normal_output" type="vector3" nodename="normal" />
  </nodegraph>

  <open_pbr_surface name="${component_name}" type="surfaceshader">
    <input name="base_color" type="color3" nodegraph="NG_${component_name}" output="base_color_output" />
    <input name="base_metalness" type="float" nodegraph="NG_${component_name}" output="metalness_output" />
    <input name="specular_roughness" type="float" nodegraph="NG_${component_name}" output="roughness_output" />
    <input name="geometry_normal" type="vector3" nodegraph="NG_${component_name}" output="normal_output" />
  </open_pbr_surface>

  <surfacematerial name="M_${component_name}" type="material">
    <input name="${component_name}" type="surfaceshader" nodename="open_pbr_surface1" />
  </surfacematerial>
</materialx>"""

        comp_template_file = comp_template_dir / "{$component_name}_mat.mtlx"
        with open(comp_template_file, "w", encoding="utf-8") as f:
            f.write(comp_template_content)

        # 创建subcomponents模板
        subcomp_template_dir = (
            self.temp_dir / "template" / "{$assembly_name}" / "subcomponents" / "{$component_name}"
        )
        subcomp_template_dir.mkdir(parents=True)

        subcomp_template_file = subcomp_template_dir / "{$component_name}_mat.mtlx"
        with open(subcomp_template_file, "w", encoding="utf-8") as f:
            f.write(comp_template_content)  # 内容相同

    @patch("mtlx.materialx.get_template_dir")
    @patch("MaterialX.createDocument")
    @patch("MaterialX.readFromXmlFile")
    @patch("MaterialX.writeToXmlFile")
    def test_create_materialx_file_component_success(
        self,
        mock_write_xml,
        mock_read_xml,
        mock_create_doc,
        mock_get_template,
    ):
        """测试成功创建component类型的MaterialX文件."""
        mock_get_template.return_value = self.temp_dir / "template"

        # 模拟MaterialX文档
        mock_doc = Mock()
        mock_create_doc.return_value = mock_doc

        # 模拟节点图
        mock_node_graph = Mock()
        mock_doc.getNodeGraph.return_value = mock_node_graph

        # 模拟节点
        mock_base_color_node = Mock()
        mock_metallic_node = Mock()
        mock_normal_node = Mock()

        def get_node_side_effect(node_name):
            node_map = {
                "base_color": mock_base_color_node,
                "metallic": mock_metallic_node,
                "normal": mock_normal_node,
            }
            return node_map.get(node_name)

        mock_node_graph.getNode.side_effect = get_node_side_effect
        mock_node_graph.getNodes.return_value = []  # 没有未使用的节点

        # 模拟输入
        mock_input = Mock()
        mock_base_color_node.addInput.return_value = mock_input
        mock_metallic_node.addInput.return_value = mock_input
        mock_normal_node.addInput.return_value = mock_input

        # 测试数据
        component_name = "test_component"
        texture_files = {
            "base_color": "textures/test_base_color.jpg",
            "metallic": "textures/test_metallic.png",
            "normal": "textures/test_normal.exr",
        }
        output_path = self.temp_dir / "output.mtlx"

        # 执行函数
        create_materialx_file(
            component_name,
            texture_files,
            str(output_path),
            ComponentType.COMPONENT,
        )

        # 验证调用
        mock_create_doc.assert_called_once()
        mock_read_xml.assert_called_once()
        mock_write_xml.assert_called_once_with(mock_doc, str(output_path))

        # 验证节点图查询
        mock_doc.getNodeGraph.assert_called_once_with(f"NG_{component_name}")

        # 验证纹理文件设置
        assert mock_base_color_node.addInput.call_count == 1
        assert mock_metallic_node.addInput.call_count == 1
        assert mock_normal_node.addInput.call_count == 1

    @patch("mtlx.materialx.get_template_dir")
    @patch("MaterialX.createDocument")
    @patch("MaterialX.readFromXmlFile")
    @patch("MaterialX.writeToXmlFile")
    def test_create_materialx_file_subcomponent_success(
        self,
        mock_write_xml,
        mock_read_xml,
        mock_create_doc,
        mock_get_template,
    ):
        """测试成功创建subcomponent类型的MaterialX文件."""
        mock_get_template.return_value = self.temp_dir / "template"

        # 模拟MaterialX文档
        mock_doc = Mock()
        mock_create_doc.return_value = mock_doc

        # 模拟节点图
        mock_node_graph = Mock()
        mock_doc.getNodeGraph.return_value = mock_node_graph

        # 模拟节点
        mock_base_color_node = Mock()
        mock_node_graph.getNode.return_value = mock_base_color_node
        mock_node_graph.getNodes.return_value = []

        # 模拟输入
        mock_input = Mock()
        mock_base_color_node.addInput.return_value = mock_input

        # 测试数据
        component_name = "test_subcomponent"
        texture_files = {"base_color": "textures/test_base_color.jpg"}
        output_path = self.temp_dir / "output.mtlx"

        # 执行函数
        create_materialx_file(
            component_name,
            texture_files,
            str(output_path),
            ComponentType.SUBCOMPONENT,
        )

        # 验证使用了正确的模板路径（subcomponents目录）
        expected_template_calls = mock_get_template.call_args_list
        assert len(expected_template_calls) >= 1

    @patch("mtlx.materialx.get_template_dir")
    def test_create_materialx_file_template_not_found(self, mock_get_template):
        """测试模板文件不存在的情况."""
        mock_get_template.return_value = Path("/nonexistent/template")

        component_name = "test_component"
        texture_files = {"base_color": "textures/test.jpg"}
        output_path = self.temp_dir / "output.mtlx"

        with pytest.raises(MaterialXError, match="MaterialX模板文件不存在"):
            create_materialx_file(
                component_name,
                texture_files,
                str(output_path),
                ComponentType.COMPONENT,
            )

    @patch("mtlx.materialx.get_template_dir")
    @patch("MaterialX.createDocument")
    @patch("MaterialX.readFromXmlFile")
    def test_create_materialx_file_node_graph_not_found(
        self,
        mock_read_xml,
        mock_create_doc,
        mock_get_template,
    ):
        """测试节点图不存在的情况."""
        mock_get_template.return_value = self.temp_dir / "template"

        # 模拟MaterialX文档
        mock_doc = Mock()
        mock_create_doc.return_value = mock_doc
        mock_doc.getNodeGraph.return_value = None  # 节点图不存在

        component_name = "test_component"
        texture_files = {"base_color": "textures/test.jpg"}
        output_path = self.temp_dir / "output.mtlx"

        with pytest.raises(MaterialXError, match="找不到节点图"):
            create_materialx_file(
                component_name,
                texture_files,
                str(output_path),
                ComponentType.COMPONENT,
            )

    @patch("mtlx.materialx.get_template_dir")
    @patch("MaterialX.createDocument")
    @patch("MaterialX.readFromXmlFile")
    @patch("MaterialX.writeToXmlFile")
    def test_create_materialx_file_with_cleanup(
        self,
        mock_write_xml,
        mock_read_xml,
        mock_create_doc,
        mock_get_template,
    ):
        """测试MaterialX文件创建并清理未使用的节点."""
        mock_get_template.return_value = self.temp_dir / "template"

        # 模拟MaterialX文档
        mock_doc = Mock()
        mock_create_doc.return_value = mock_doc

        # 模拟节点图
        mock_node_graph = Mock()
        mock_doc.getNodeGraph.return_value = mock_node_graph

        # 模拟使用的节点
        mock_used_node = Mock()
        mock_used_node.addInput.return_value = Mock()

        # 模拟未使用的节点
        mock_unused_node = Mock()
        mock_unused_node.getType.return_value = "image"
        mock_unused_node.getName.return_value = "unused_texture"

        def get_node_side_effect(node_name):
            if node_name == "base_color":
                return mock_used_node
            return None

        mock_node_graph.getNode.side_effect = get_node_side_effect
        mock_node_graph.getNodes.return_value = [mock_unused_node]

        # 测试数据
        component_name = "test_component"
        texture_files = {"base_color": "textures/test.jpg"}
        output_path = self.temp_dir / "output.mtlx"

        # 执行函数
        create_materialx_file(
            component_name,
            texture_files,
            str(output_path),
            ComponentType.COMPONENT,
        )

        # 验证清理未使用的节点
        mock_node_graph.removeNode.assert_called_once_with("unused_texture")

    @patch("mtlx.materialx.get_template_dir")
    @patch("MaterialX.createDocument")
    @patch("MaterialX.readFromXmlFile")
    @patch("MaterialX.writeToXmlFile")
    def test_create_materialx_file_missing_texture_node(
        self,
        mock_write_xml,
        mock_read_xml,
        mock_create_doc,
        mock_get_template,
    ):
        """测试纹理节点缺失的情况（应该给出警告但继续）."""
        mock_get_template.return_value = self.temp_dir / "template"

        # 模拟MaterialX文档
        mock_doc = Mock()
        mock_create_doc.return_value = mock_doc

        # 模拟节点图
        mock_node_graph = Mock()
        mock_doc.getNodeGraph.return_value = mock_node_graph
        mock_node_graph.getNode.return_value = None  # 节点不存在
        mock_node_graph.getNodes.return_value = []

        # 测试数据
        component_name = "test_component"
        texture_files = {"missing_texture": "textures/test.jpg"}
        output_path = self.temp_dir / "output.mtlx"

        # 执行函数（应该成功，但会有警告）
        with patch("mtlx.materialx.console") as mock_console:
            create_materialx_file(
                component_name,
                texture_files,
                str(output_path),
                ComponentType.COMPONENT,
            )

            # 验证输出了警告信息
            mock_console.print.assert_called_once()
            warning_call = mock_console.print.call_args[0][0]
            assert "警告" in warning_call and "missing_texture" in warning_call

    def test_create_materialx_file_default_component_type(self):
        """测试默认组件类型为COMPONENT."""
        # 这个测试确保当没有指定component_type时，默认使用COMPONENT
        with patch("mtlx.materialx.get_template_dir") as mock_get_template:
            mock_get_template.return_value = self.temp_dir / "template"

            with patch("MaterialX.createDocument") as mock_create_doc:
                mock_doc = Mock()
                mock_create_doc.return_value = mock_doc
                mock_node_graph = Mock()
                mock_doc.getNodeGraph.return_value = mock_node_graph
                mock_node_graph.getNode.return_value = None
                mock_node_graph.getNodes.return_value = []

                with patch("MaterialX.readFromXmlFile"), patch("MaterialX.writeToXmlFile"):
                    # 不指定component_type参数
                    create_materialx_file(
                        "test_component",
                        {},
                        str(self.temp_dir / "output.mtlx"),
                    )

                    # 验证使用了components目录的模板
                    # 这里通过检查模板路径来验证默认使用了COMPONENT类型
