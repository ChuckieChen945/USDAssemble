#!/usr/bin/env python3
"""测试CLI功能."""

import tempfile
from pathlib import Path
from string import Template
from unittest.mock import Mock, call, patch

import pytest
from typer.testing import CliRunner

from usdassemble.cli import (
    AssemblyError,
    app,
    create_assembly_main,
    create_component_look,
    create_component_main,
    create_component_payload,
    create_from_template,
    process_component,
    scan_components,
)
from usdassemble.utils import ComponentType


class TestCreateFromTemplate:
    """测试create_from_template函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_from_template_success(self):
        """测试成功从模板创建文件."""
        # 创建模板文件
        template_path = self.temp_dir / "template.txt"
        template_content = "Hello $name, welcome to $project!"
        with open(template_path, "w", encoding="utf-8") as f:
            f.write(template_content)

        # 创建输出路径
        output_path = self.temp_dir / "output" / "result.txt"
        substitutions = {"name": "测试", "project": "USDAssemble"}

        # 执行函数
        create_from_template(template_path, output_path, substitutions)

        # 验证结果
        assert output_path.exists()
        with open(output_path, encoding="utf-8") as f:
            content = f.read()
        assert content == "Hello 测试, welcome to USDAssemble!"

    def test_create_from_template_missing_template(self):
        """测试模板文件不存在的情况."""
        template_path = self.temp_dir / "missing_template.txt"
        output_path = self.temp_dir / "output.txt"
        substitutions = {"name": "test"}

        with pytest.raises(AssemblyError, match="模板文件不存在"):
            create_from_template(template_path, output_path, substitutions)

    def test_create_from_template_creates_directories(self):
        """测试自动创建输出目录."""
        # 创建模板文件
        template_path = self.temp_dir / "template.txt"
        with open(template_path, "w", encoding="utf-8") as f:
            f.write("Content: $value")

        # 输出到深层目录
        output_path = self.temp_dir / "deep" / "nested" / "output.txt"
        substitutions = {"value": "test"}

        create_from_template(template_path, output_path, substitutions)

        # 验证目录和文件都创建了
        assert output_path.exists()
        assert output_path.parent.exists()


class TestScanComponents:
    """测试scan_components函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_scan_components_success(self):
        """测试成功扫描components目录."""
        # 创建components目录结构
        components_dir = self.temp_dir / "components"
        components_dir.mkdir()

        # 创建有效组件
        comp1_dir = components_dir / "component1"
        comp1_dir.mkdir()
        (comp1_dir / "component1_geom.usd").touch()

        comp2_dir = components_dir / "component2"
        comp2_dir.mkdir()
        (comp2_dir / "component2_geom.usd").touch()

        # 创建无效组件（缺少geom文件）
        comp3_dir = components_dir / "component3"
        comp3_dir.mkdir()

        components, component_type = scan_components(str(self.temp_dir))

        assert len(components) == 2
        assert "component1" in components
        assert "component2" in components
        assert "component3" not in components
        assert component_type == ComponentType.COMPONENT

    def test_scan_subcomponents_success(self):
        """测试成功扫描subcomponents目录."""
        # 创建subcomponents目录结构
        subcomponents_dir = self.temp_dir / "subcomponents"
        subcomponents_dir.mkdir()

        # 创建有效子组件
        subcomp1_dir = subcomponents_dir / "subcomponent1"
        subcomp1_dir.mkdir()
        (subcomp1_dir / "subcomponent1_geom.usd").touch()

        components, component_type = scan_components(str(self.temp_dir))

        assert len(components) == 1
        assert "subcomponent1" in components
        assert component_type == ComponentType.SUBCOMPONENT

    def test_scan_components_no_directory(self):
        """测试没有组件目录的情况."""
        with pytest.raises(AssemblyError, match="未找到支持的组件目录"):
            scan_components(str(self.temp_dir))

    def test_scan_components_empty_directory(self):
        """测试空组件目录的情况."""
        components_dir = self.temp_dir / "components"
        components_dir.mkdir()

        with pytest.raises(AssemblyError, match="未找到任何有效component"):
            scan_components(str(self.temp_dir))

    def test_scan_components_prefer_components_over_subcomponents(self):
        """测试当两种目录都存在时，优先选择components."""
        # 创建两种目录
        components_dir = self.temp_dir / "components"
        components_dir.mkdir()
        comp_dir = components_dir / "component1"
        comp_dir.mkdir()
        (comp_dir / "component1_geom.usd").touch()

        subcomponents_dir = self.temp_dir / "subcomponents"
        subcomponents_dir.mkdir()
        subcomp_dir = subcomponents_dir / "subcomponent1"
        subcomp_dir.mkdir()
        (subcomp_dir / "subcomponent1_geom.usd").touch()

        components, component_type = scan_components(str(self.temp_dir))

        assert component_type == ComponentType.COMPONENT
        assert "component1" in components


class TestCreateComponentMain:
    """测试create_component_main函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())
        # 创建模拟的模板目录
        self.template_dir = self.temp_dir / "template"
        self.setup_template_structure()

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def setup_template_structure(self):
        """设置模板目录结构."""
        # 创建components模板
        comp_template_dir = (
            self.template_dir / "{$assembly_name}" / "components" / "{$component_name}"
        )
        comp_template_dir.mkdir(parents=True)

        comp_template_content = """#usda 1.0
(
    defaultPrim = "${component_name}"
)

def Xform "${component_name}" (
    kind = "component"
)
{
}
"""
        comp_template_file = comp_template_dir / "{$component_name}.usd"
        with open(comp_template_file, "w", encoding="utf-8") as f:
            f.write(comp_template_content)

        # 创建subcomponents模板
        subcomp_template_dir = (
            self.template_dir / "{$assembly_name}" / "subcomponents" / "{$component_name}"
        )
        subcomp_template_dir.mkdir(parents=True)

        subcomp_template_content = """#usda 1.0
(
    defaultPrim = "${component_name}"
)

def Xform "${component_name}" (
    kind = "subcomponent"
)
{
}
"""
        subcomp_template_file = subcomp_template_dir / "{$component_name}.usd"
        with open(subcomp_template_file, "w", encoding="utf-8") as f:
            f.write(subcomp_template_content)

    @patch("usdassemble.cli.get_template_dir")
    @patch("pxr.Usd.Stage.Open")
    @patch("pxr.Kind.Registry.SetKind")
    def test_create_component_main_component_type(
        self, mock_set_kind, mock_stage_open, mock_get_template
    ):
        """测试创建component类型的主文件."""
        mock_get_template.return_value = self.template_dir

        # 模拟USD Stage
        mock_stage = Mock()
        mock_prim = Mock()
        mock_stage.GetPrimAtPath.return_value = mock_prim
        mock_stage_open.return_value = mock_stage

        output_path = self.temp_dir / "component1.usd"

        create_component_main(str(output_path), "component1", ComponentType.COMPONENT)

        # 验证模板文件被使用
        assert output_path.exists()

        # 验证USD API调用
        mock_stage_open.assert_called_once_with(str(output_path))
        mock_stage.GetPrimAtPath.assert_called_once_with("/component1")
        mock_set_kind.assert_called_once_with(mock_prim, "component")
        mock_stage.Save.assert_called_once()

    @patch("usdassemble.cli.get_template_dir")
    @patch("pxr.Usd.Stage.Open")
    @patch("pxr.Kind.Registry.SetKind")
    def test_create_component_main_subcomponent_type(
        self, mock_set_kind, mock_stage_open, mock_get_template
    ):
        """测试创建subcomponent类型的主文件."""
        mock_get_template.return_value = self.template_dir

        # 模拟USD Stage
        mock_stage = Mock()
        mock_prim = Mock()
        mock_stage.GetPrimAtPath.return_value = mock_prim
        mock_stage_open.return_value = mock_stage

        output_path = self.temp_dir / "subcomponent1.usd"

        create_component_main(str(output_path), "subcomponent1", ComponentType.SUBCOMPONENT)

        # 验证模板文件被使用
        assert output_path.exists()

        # 验证USD API调用
        mock_set_kind.assert_called_once_with(mock_prim, "subcomponent")


class TestCreateAssemblyMain:
    """测试create_assembly_main函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.setup_template()

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def setup_template(self):
        """设置模板文件."""
        template_dir = self.temp_dir / "template" / "{$assembly_name}"
        template_dir.mkdir(parents=True)

        template_content = """#usda 1.0
(
    defaultPrim = "${assembly_name}"
)

def Xform "${assembly_name}" (
    kind = "assembly"
)
{
}
"""
        template_file = template_dir / "{$assembly_name}.usda"
        with open(template_file, "w", encoding="utf-8") as f:
            f.write(template_content)

    @patch("usdassemble.cli.get_template_dir")
    @patch("pxr.Usd.Stage.Open")
    def test_create_assembly_main_with_components(self, mock_stage_open, mock_get_template):
        """测试创建包含components的assembly主文件."""
        mock_get_template.return_value = self.temp_dir / "template"

        # 模拟USD Stage
        mock_stage = Mock()
        mock_assembly_prim = Mock()
        mock_stage.GetPrimAtPath.return_value = mock_assembly_prim
        mock_stage_open.return_value = mock_stage

        # 模拟组件prim创建
        mock_comp_prim = Mock()
        mock_comp_refs = Mock()
        mock_comp_prim.GetReferences.return_value = mock_comp_refs
        mock_stage.DefinePrim.return_value = mock_comp_prim

        output_path = self.temp_dir / "test_assembly.usda"
        components = ["comp1", "comp2"]

        create_assembly_main(
            str(output_path),
            "test_assembly",
            components,
            ComponentType.COMPONENT,
        )

        # 验证组件引用路径使用了正确的目录
        expected_calls = [
            call("./components/comp1/comp1.usd"),
            call("./components/comp2/comp2.usd"),
        ]
        mock_comp_refs.AddReference.assert_has_calls(expected_calls)

    @patch("usdassemble.cli.get_template_dir")
    @patch("pxr.Usd.Stage.Open")
    def test_create_assembly_main_with_subcomponents(self, mock_stage_open, mock_get_template):
        """测试创建包含subcomponents的assembly主文件."""
        mock_get_template.return_value = self.temp_dir / "template"

        # 模拟USD Stage
        mock_stage = Mock()
        mock_assembly_prim = Mock()
        mock_stage.GetPrimAtPath.return_value = mock_assembly_prim
        mock_stage_open.return_value = mock_stage

        # 模拟组件prim创建
        mock_comp_prim = Mock()
        mock_comp_refs = Mock()
        mock_comp_prim.GetReferences.return_value = mock_comp_refs
        mock_stage.DefinePrim.return_value = mock_comp_prim

        output_path = self.temp_dir / "test_assembly.usda"
        components = ["subcomp1"]

        create_assembly_main(
            str(output_path),
            "test_assembly",
            components,
            ComponentType.SUBCOMPONENT,
        )

        # 验证子组件引用路径使用了正确的目录
        mock_comp_refs.AddReference.assert_called_once_with("./subcomponents/subcomp1/subcomp1.usd")


class TestProcessComponent:
    """测试process_component函数."""

    def setup_method(self):
        """设置测试环境."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """清理测试环境."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("usdassemble.cli.validate_texture_files")
    @patch("usdassemble.cli.create_materialx_file")
    @patch("usdassemble.cli.create_component_main")
    @patch("usdassemble.cli.create_component_payload")
    @patch("usdassemble.cli.create_component_look")
    def test_process_component_with_textures(
        self,
        mock_create_look,
        mock_create_payload,
        mock_create_main,
        mock_create_mtlx,
        mock_validate_textures,
    ):
        """测试处理带纹理的组件."""
        # 模拟纹理文件验证返回
        mock_validate_textures.return_value = {
            "base_color": "textures/comp_base_color.jpg",
            "metallic": "textures/comp_metallic.png",
        }

        component_path = str(self.temp_dir / "components" / "test_comp")
        Path(component_path).mkdir(parents=True)

        process_component(component_path, "test_comp", ComponentType.COMPONENT)

        # 验证所有必要的文件创建函数都被调用
        mock_validate_textures.assert_called_once()
        mock_create_mtlx.assert_called_once()
        mock_create_main.assert_called_once_with(
            str(Path(component_path) / "test_comp.usd"),
            "test_comp",
            ComponentType.COMPONENT,
        )
        mock_create_payload.assert_called_once_with(
            str(Path(component_path) / "test_comp_payload.usd"),
            "test_comp",
            ComponentType.COMPONENT,
        )
        mock_create_look.assert_called_once_with(
            str(Path(component_path) / "test_comp_look.usd"),
            "test_comp",
            ComponentType.COMPONENT,
        )

    @patch("usdassemble.cli.validate_texture_files")
    @patch("usdassemble.cli.create_materialx_file")
    @patch("usdassemble.cli.create_component_main")
    @patch("usdassemble.cli.create_component_payload")
    @patch("usdassemble.cli.create_component_look")
    def test_process_subcomponent_without_textures(
        self,
        mock_create_look,
        mock_create_payload,
        mock_create_main,
        mock_create_mtlx,
        mock_validate_textures,
    ):
        """测试处理无纹理的子组件."""
        # 模拟无纹理文件
        mock_validate_textures.return_value = {}

        component_path = str(self.temp_dir / "subcomponents" / "test_subcomp")
        Path(component_path).mkdir(parents=True)

        process_component(component_path, "test_subcomp", ComponentType.SUBCOMPONENT)

        # 验证MaterialX文件没有被创建
        mock_create_mtlx.assert_not_called()

        # 验证其他文件创建函数被调用时使用了正确的组件类型
        mock_create_main.assert_called_once_with(
            str(Path(component_path) / "test_subcomp.usd"),
            "test_subcomp",
            ComponentType.SUBCOMPONENT,
        )


class TestAssemblyCommand:
    """测试assembly命令."""

    def setup_method(self):
        """设置测试环境."""
        self.runner = CliRunner()

    @patch("usdassemble.cli.scan_components")
    @patch("usdassemble.cli.process_component")
    @patch("usdassemble.cli.create_assembly_main")
    def test_assembly_command_success(self, mock_create_assembly, mock_process_comp, mock_scan):
        """测试assembly命令成功执行."""
        # 模拟扫描结果
        mock_scan.return_value = (["comp1", "comp2"], ComponentType.COMPONENT)

        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["assembly", temp_dir])

            assert result.exit_code == 0
            mock_scan.assert_called_once()
            assert mock_process_comp.call_count == 2
            mock_create_assembly.assert_called_once()

    @patch("usdassemble.cli.scan_components")
    def test_assembly_command_no_components(self, mock_scan):
        """测试没有组件时的assembly命令."""
        # 模拟扫描失败
        mock_scan.side_effect = AssemblyError("未找到任何有效组件")

        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["assembly", temp_dir])

            assert result.exit_code == 1
            assert "装配失败" in result.stdout

    @patch("usdassemble.cli.scan_components")
    @patch("usdassemble.cli.process_component")
    @patch("usdassemble.cli.create_assembly_main")
    def test_assembly_command_with_subcomponents(
        self, mock_create_assembly, mock_process_comp, mock_scan
    ):
        """测试assembly命令处理subcomponents."""
        # 模拟子组件扫描结果
        mock_scan.return_value = (["subcomp1"], ComponentType.SUBCOMPONENT)

        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.runner.invoke(app, ["assembly", temp_dir])

            assert result.exit_code == 0
            # 验证process_component被调用时传递了正确的组件类型
            mock_process_comp.assert_called_once()
            args, kwargs = mock_process_comp.call_args
            assert args[2] == ComponentType.SUBCOMPONENT
