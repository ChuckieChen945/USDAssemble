#!/usr/bin/env python3
"""集成测试 - 测试完整的USD装配流程."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner
from usdassemble.cli import app
from usdassemble.utils import ComponentType


class TestCompleteWorkflow:
    """测试完整的USD装配工作流程."""

    def setup_method(self):
        """设置测试环境."""
        self.runner = CliRunner()
        self.temp_dir = Path(tempfile.mkdtemp())
        self.setup_test_project()

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def setup_test_project(self):
        """设置测试项目结构."""
        # 创建模拟的模板目录
        self.setup_templates()

    def setup_templates(self):
        """设置模板文件."""
        # 设置components模板
        comp_template_dir = (
            self.temp_dir / "templates" / "{$assembly_name}" / "components" / "{$component_name}"
        )
        comp_template_dir.mkdir(parents=True)

        self.create_template_files(comp_template_dir, "component")

        # 设置subcomponents模板
        subcomp_template_dir = (
            self.temp_dir / "templates" / "{$assembly_name}" / "subcomponents" / "{$component_name}"
        )
        subcomp_template_dir.mkdir(parents=True)

        self.create_template_files(subcomp_template_dir, "subcomponent")

    def create_template_files(self, template_dir: Path, kind: str):
        """创建模板文件."""
        # 主文件模板
        main_template = f"""#usda 1.0
(
    defaultPrim = "${{component_name}}"
    metersPerUnit = 1
    upAxis = "Z"
)

def Xform "${{component_name}}" (
    kind = "{kind}"
    payload = @./${{component_name}}_payload.usd@</${{component_name}}>
)
{{
}}
"""

        # Payload模板
        payload_template = """#usda 1.0
(
    defaultPrim = "${component_name}"
    metersPerUnit = 1
    subLayers = [
        @./${component_name}_look.usd@,
        @./${component_name}_geom.usd@
    ]
    upAxis = "Z"
)
"""

        # Look模板
        look_template = """#usda 1.0
(
    defaultPrim = "${component_name}"
    metersPerUnit = 1
    upAxis = "Z"
)

over "${component_name}"
{
    def Scope "Materials" (
        prepend references = @./${component_name}_mat.mtlx@</MaterialX/Materials>
    )
    {
    }
}
"""

        # MaterialX模板
        mtlx_template = """<?xml version="1.0"?>
<materialx version="1.38" colorspace="lin_rec709">
  <nodegraph name="NG_${component_name}">
    <image name="base_color" type="color3" />
    <image name="metallic" type="float" />
    <output name="base_color_output" type="color3" nodename="base_color" />
    <output name="metalness_output" type="float" nodename="metallic" />
  </nodegraph>

  <open_pbr_surface name="${component_name}" type="surfaceshader">
    <input name="base_color" type="color3" nodegraph="NG_${component_name}" output="base_color_output" />
  </open_pbr_surface>

  <surfacematerial name="M_${component_name}" type="material">
    <input name="${component_name}" type="surfaceshader" nodename="open_pbr_surface1" />
  </surfacematerial>
</materialx>"""

        # 写入模板文件
        (template_dir / "{$component_name}.usd").write_text(main_template, encoding="utf-8")
        (template_dir / "{$component_name}_payload.usd").write_text(
            payload_template,
            encoding="utf-8",
        )
        (template_dir / "{$component_name}_look.usd").write_text(look_template, encoding="utf-8")
        (template_dir / "{$component_name}_mat.mtlx").write_text(mtlx_template, encoding="utf-8")

    def create_project_with_components(self, project_dir: Path):
        """创建包含components的测试项目."""
        components_dir = project_dir / "components"
        components_dir.mkdir(parents=True)

        # 创建component1
        comp1_dir = components_dir / "component1"
        comp1_dir.mkdir()
        (comp1_dir / "component1_geom.usd").touch()

        # 创建带纹理的component2
        comp2_dir = components_dir / "component2"
        comp2_dir.mkdir()
        (comp2_dir / "component2_geom.usd").touch()

        # 创建纹理目录和文件
        textures_dir = comp2_dir / "textures"
        textures_dir.mkdir()
        (textures_dir / "comp2_base_color.jpg").touch()
        (textures_dir / "comp2_metallic.png").touch()

    def create_project_with_subcomponents(self, project_dir: Path):
        """创建包含subcomponents的测试项目."""
        subcomponents_dir = project_dir / "subcomponents"
        subcomponents_dir.mkdir(parents=True)

        # 创建subcomponent1
        subcomp1_dir = subcomponents_dir / "subcomponent1"
        subcomp1_dir.mkdir()
        (subcomp1_dir / "subcomponent1_geom.usd").touch()

    @patch("usdassemble.cli.get_template_dir")
    @patch("pxr.Usd.Stage.Open")
    @patch("pxr.Kind.Registry.SetKind")
    @patch("MaterialX.createDocument")
    @patch("MaterialX.readFromXmlFile")
    @patch("MaterialX.writeToXmlFile")
    def test_components_workflow_end_to_end(
        self,
        mock_write_xml,
        mock_read_xml,
        mock_create_doc,
        mock_set_kind,
        mock_stage_open,
        mock_get_template,
    ):
        """测试components的端到端工作流程."""
        mock_get_template.return_value = self.temp_dir / "templates"

        # 模拟USD Stage
        mock_stage = self.setup_usd_mocks(mock_stage_open)

        # 模拟MaterialX
        self.setup_materialx_mocks(mock_create_doc, mock_read_xml)

        # 创建测试项目
        project_dir = self.temp_dir / "test_project"
        self.create_project_with_components(project_dir)

        # 执行assembly命令
        result = self.runner.invoke(app, ["assembly", str(project_dir)])

        # 验证成功
        assert result.exit_code == 0, f"命令失败: {result.stdout}"
        assert "装配完成" in result.stdout
        assert "component" in result.stdout  # 应该显示组件类型

        # 验证Kind.Registry.SetKind被调用时使用了正确的kind值
        set_kind_calls = mock_set_kind.call_args_list
        # 应该为两个组件各调用一次
        assert len(set_kind_calls) == 2
        for call_args in set_kind_calls:
            # 第二个参数应该是"component"
            assert call_args[0][1] == "component"

    @patch("usdassemble.cli.get_template_dir")
    @patch("pxr.Usd.Stage.Open")
    @patch("pxr.Kind.Registry.SetKind")
    @patch("MaterialX.createDocument")
    @patch("MaterialX.readFromXmlFile")
    @patch("MaterialX.writeToXmlFile")
    def test_subcomponents_workflow_end_to_end(
        self,
        mock_write_xml,
        mock_read_xml,
        mock_create_doc,
        mock_set_kind,
        mock_stage_open,
        mock_get_template,
    ):
        """测试subcomponents的端到端工作流程."""
        mock_get_template.return_value = self.temp_dir / "templates"

        # 模拟USD Stage
        mock_stage = self.setup_usd_mocks(mock_stage_open)

        # 模拟MaterialX
        self.setup_materialx_mocks(mock_create_doc, mock_read_xml)

        # 创建测试项目
        project_dir = self.temp_dir / "test_subproject"
        self.create_project_with_subcomponents(project_dir)

        # 执行assembly命令
        result = self.runner.invoke(app, ["assembly", str(project_dir)])

        # 验证成功
        assert result.exit_code == 0, f"命令失败: {result.stdout}"
        assert "装配完成" in result.stdout
        assert "subcomponent" in result.stdout  # 应该显示子组件类型

        # 验证Kind.Registry.SetKind被调用时使用了正确的kind值
        set_kind_calls = mock_set_kind.call_args_list
        assert len(set_kind_calls) == 1
        # 第二个参数应该是"subcomponent"
        assert set_kind_calls[0][0][1] == "subcomponent"

    @patch("usdassemble.cli.get_template_dir")
    def test_mixed_directories_prefer_components(self, mock_get_template):
        """测试当同时存在components和subcomponents目录时，优先处理components."""
        mock_get_template.return_value = self.temp_dir / "templates"

        # 创建同时包含两种目录的项目
        project_dir = self.temp_dir / "mixed_project"

        # 创建components
        self.create_project_with_components(project_dir)

        # 创建subcomponents
        self.create_project_with_subcomponents(project_dir)

        with patch("pxr.Usd.Stage.Open") as mock_stage_open:
            mock_stage = self.setup_usd_mocks(mock_stage_open)

            with patch("MaterialX.createDocument") as mock_create_doc:
                self.setup_materialx_mocks(mock_create_doc, None)

                # 执行assembly命令
                result = self.runner.invoke(app, ["assembly", str(project_dir)])

                # 验证成功并优先处理了components
                assert result.exit_code == 0
                assert "component1" in result.stdout
                assert "component2" in result.stdout
                # 不应该处理subcomponents
                assert "subcomponent1" not in result.stdout

    def test_no_component_directories(self):
        """测试没有组件目录时的错误处理."""
        project_dir = self.temp_dir / "empty_project"
        project_dir.mkdir()

        result = self.runner.invoke(app, ["assembly", str(project_dir)])

        assert result.exit_code == 1
        assert "装配失败" in result.stdout
        assert "未找到支持的组件目录" in result.stdout

    def test_empty_components_directory(self):
        """测试空组件目录的错误处理."""
        project_dir = self.temp_dir / "empty_components_project"
        project_dir.mkdir()
        (project_dir / "components").mkdir()  # 空目录

        result = self.runner.invoke(app, ["assembly", str(project_dir)])

        assert result.exit_code == 1
        assert "装配失败" in result.stdout
        assert "未找到任何有效component" in result.stdout

    def test_invalid_components_missing_geom(self):
        """测试包含无效组件（缺少geom文件）的处理."""
        project_dir = self.temp_dir / "invalid_project"
        components_dir = project_dir / "components"
        components_dir.mkdir(parents=True)

        # 创建无效组件（缺少geom文件）
        invalid_comp_dir = components_dir / "invalid_component"
        invalid_comp_dir.mkdir()
        # 不创建_geom.usd文件

        result = self.runner.invoke(app, ["assembly", str(project_dir)])

        assert result.exit_code == 1
        assert "装配失败" in result.stdout
        assert "未找到任何有效component" in result.stdout

    def setup_usd_mocks(self, mock_stage_open):
        """设置USD相关的mock对象."""
        from unittest.mock import Mock

        mock_stage = Mock()
        mock_stage_open.return_value = mock_stage

        # 模拟prim
        mock_prim = Mock()
        mock_stage.GetPrimAtPath.return_value = mock_prim
        mock_stage.DefinePrim.return_value = mock_prim

        # 模拟references
        mock_refs = Mock()
        mock_prim.GetReferences.return_value = mock_refs

        return mock_stage

    def setup_materialx_mocks(self, mock_create_doc, mock_read_xml):
        """设置MaterialX相关的mock对象."""
        from unittest.mock import Mock

        mock_doc = Mock()
        mock_create_doc.return_value = mock_doc

        # 模拟节点图
        mock_node_graph = Mock()
        mock_doc.getNodeGraph.return_value = mock_node_graph

        # 模拟节点
        mock_node = Mock()
        mock_node_graph.getNode.return_value = mock_node
        mock_node_graph.getNodes.return_value = []

        # 模拟输入
        mock_input = Mock()
        mock_node.addInput.return_value = mock_input

        return mock_doc


class TestComponentTypeDetection:
    """测试组件类型检测功能."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_detect_components_type(self):
        """测试检测components类型."""
        from usdassemble.utils import get_component_directory_and_type

        # 创建components目录
        components_dir = self.temp_dir / "components"
        components_dir.mkdir()

        result_dir, result_type = get_component_directory_and_type(self.temp_dir)

        assert result_dir == components_dir
        assert result_type == ComponentType.COMPONENT

    def test_detect_subcomponents_type(self):
        """测试检测subcomponents类型."""
        from usdassemble.utils import get_component_directory_and_type

        # 创建subcomponents目录
        subcomponents_dir = self.temp_dir / "subcomponents"
        subcomponents_dir.mkdir()

        result_dir, result_type = get_component_directory_and_type(self.temp_dir)

        assert result_dir == subcomponents_dir
        assert result_type == ComponentType.SUBCOMPONENT

    def test_prefer_components_over_subcomponents(self):
        """测试当两种目录都存在时，优先选择components."""
        from usdassemble.utils import get_component_directory_and_type

        # 创建两种目录
        components_dir = self.temp_dir / "components"
        components_dir.mkdir()
        subcomponents_dir = self.temp_dir / "subcomponents"
        subcomponents_dir.mkdir()

        result_dir, result_type = get_component_directory_and_type(self.temp_dir)

        assert result_dir == components_dir
        assert result_type == ComponentType.COMPONENT

    def test_no_component_directories_error(self):
        """测试没有组件目录时抛出错误."""
        from usdassemble.utils import get_component_directory_and_type

        with pytest.raises(ValueError, match="未找到支持的组件目录"):
            get_component_directory_and_type(self.temp_dir)


class TestTemplatePathResolution:
    """测试模板路径解析功能."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("usdassemble.cli.get_template_dir")
    def test_component_template_path_resolution(self, mock_get_template):
        """测试component模板路径解析."""
        from usdassemble.cli import create_component_main

        mock_get_template.return_value = self.temp_dir

        # 创建模板文件
        template_dir = self.temp_dir / "{$assembly_name}" / "components" / "{$component_name}"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "{$component_name}.usd"
        template_file.write_text('#usda 1.0\ndef Xform "${component_name}" (kind = "component") {}')

        with patch("pxr.Usd.Stage.Open") as mock_stage_open:
            mock_stage = Mock()
            mock_prim = Mock()
            mock_stage.GetPrimAtPath.return_value = mock_prim
            mock_stage_open.return_value = mock_stage

            output_path = self.temp_dir / "test_comp.usd"

            # 应该不抛出异常
            create_component_main(str(output_path), "test_comp", ComponentType.COMPONENT)

            # 验证文件被创建
            assert output_path.exists()

    @patch("usdassemble.cli.get_template_dir")
    def test_subcomponent_template_path_resolution(self, mock_get_template):
        """测试subcomponent模板路径解析."""
        from usdassemble.cli import create_component_main

        mock_get_template.return_value = self.temp_dir

        # 创建模板文件
        template_dir = self.temp_dir / "{$assembly_name}" / "subcomponents" / "{$component_name}"
        template_dir.mkdir(parents=True)
        template_file = template_dir / "{$component_name}.usd"
        template_file.write_text(
            '#usda 1.0\ndef Xform "${component_name}" (kind = "subcomponent") {}',
        )

        with patch("pxr.Usd.Stage.Open") as mock_stage_open:
            mock_stage = Mock()
            mock_prim = Mock()
            mock_stage.GetPrimAtPath.return_value = mock_prim
            mock_stage_open.return_value = mock_stage

            output_path = self.temp_dir / "test_subcomp.usd"

            # 应该不抛出异常
            create_component_main(str(output_path), "test_subcomp", ComponentType.SUBCOMPONENT)

            # 验证文件被创建
            assert output_path.exists()

    @patch("mtlx.materialx.get_template_dir")
    def test_materialx_template_path_resolution(self, mock_get_template):
        """测试MaterialX模板路径解析."""
        from mtlx.materialx import create_materialx_file

        mock_get_template.return_value = self.temp_dir

        # 创建MaterialX模板文件
        comp_template_dir = self.temp_dir / "{$assembly_name}" / "components" / "{$component_name}"
        comp_template_dir.mkdir(parents=True)
        comp_template_file = comp_template_dir / "{$component_name}_mat.mtlx"
        comp_template_file.write_text("""<?xml version="1.0"?>
<materialx version="1.38">
  <nodegraph name="NG_${component_name}">
    <image name="base_color" type="color3" />
  </nodegraph>
</materialx>""")

        subcomp_template_dir = (
            self.temp_dir / "{$assembly_name}" / "subcomponents" / "{$component_name}"
        )
        subcomp_template_dir.mkdir(parents=True)
        subcomp_template_file = subcomp_template_dir / "{$component_name}_mat.mtlx"
        subcomp_template_file.write_text(comp_template_file.read_text())

        with patch("MaterialX.createDocument") as mock_create_doc:
            mock_doc = Mock()
            mock_create_doc.return_value = mock_doc
            mock_node_graph = Mock()
            mock_doc.getNodeGraph.return_value = mock_node_graph
            mock_node_graph.getNode.return_value = None
            mock_node_graph.getNodes.return_value = []

            with patch("MaterialX.readFromXmlFile"), patch("MaterialX.writeToXmlFile"):
                # 测试component类型
                output_path = self.temp_dir / "comp_mat.mtlx"
                create_materialx_file("test_comp", {}, str(output_path), ComponentType.COMPONENT)

                # 测试subcomponent类型
                output_path = self.temp_dir / "subcomp_mat.mtlx"
                create_materialx_file(
                    "test_subcomp",
                    {},
                    str(output_path),
                    ComponentType.SUBCOMPONENT,
                )
