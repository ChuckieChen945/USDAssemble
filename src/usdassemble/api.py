"""USDAssemble REST API."""

import asyncio
import logging
import os
import shutil
import tempfile
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .cli import (
    create_assembly_main,
    create_component_look,
    create_component_main,
    create_component_payload,
    create_materialx_file,
    detect_texture_files,
    process_component,
    read_existing_geom_file,
    scan_components,
)


class AssemblyRequest(BaseModel):
    """Assembly 装配请求"""

    base_path: str
    assembly_name: str | None = None


class ComponentRequest(BaseModel):
    """Component 装配请求"""

    base_path: str
    component_name: str | None = None


class SubcomponentRequest(BaseModel):
    """Subcomponent 装配请求"""

    base_path: str
    subcomponent_name: str | None = None


class AssemblyResponse(BaseModel):
    """装配响应"""

    success: bool
    message: str
    generated_files: list[str]
    components: list[str] | None = None


class ComponentInfo(BaseModel):
    """组件信息"""

    name: str
    path: str
    has_geometry: bool
    texture_files: dict[str, str]
    generated_files: list[str]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Handle FastAPI startup and shutdown events."""
    # Startup events.
    for handler in logging.root.handlers:
        logging.root.removeHandler(handler)
    yield
    # Shutdown events.


app = FastAPI(
    title="USDAssemble API",
    description="用于自动化装配 USD 资产的 REST API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "USDAssemble API - USD 资产自动装配服务",
        "version": "1.0.0",
        "endpoints": {
            "assembly": "/assemble/assembly",
            "component": "/assemble/component",
            "subcomponent": "/assemble/subcomponent",
            "scan": "/scan/components",
            "info": "/info/component/{component_path}",
        },
    }


@app.post("/assemble/assembly", response_model=AssemblyResponse)
async def assemble_assembly(request: AssemblyRequest, background_tasks: BackgroundTasks):
    """装配 USD Assembly"""
    try:
        base_path = os.path.abspath(request.base_path)
        assembly_name = request.assembly_name or os.path.basename(base_path)

        if not os.path.exists(base_path):
            raise HTTPException(status_code=404, detail=f"路径不存在: {base_path}")

        # 扫描组件
        components = await asyncio.to_thread(scan_components, base_path)

        if not components:
            raise HTTPException(status_code=400, detail="未找到任何组件")

        generated_files = []

        # 处理每个组件
        for component_name in components:
            component_path = os.path.join(base_path, "components", component_name)
            await asyncio.to_thread(process_component, component_path, component_name)

            # 记录生成的文件
            generated_files.extend(
                [
                    f"components/{component_name}/{component_name}.usda",
                    f"components/{component_name}/{component_name}_payload.usda",
                    f"components/{component_name}/{component_name}_look.usda",
                    f"components/{component_name}/{component_name}_mat.mtlx",
                ]
            )

        # 创建 assembly 主文件
        assembly_file = os.path.join(base_path, f"{assembly_name}.usda")
        await asyncio.to_thread(create_assembly_main, assembly_file, assembly_name, components)
        generated_files.append(f"{assembly_name}.usda")

        return AssemblyResponse(
            success=True,
            message=f"Assembly {assembly_name} 装配完成",
            generated_files=generated_files,
            components=components,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"装配失败: {e!s}")


@app.post("/assemble/component", response_model=AssemblyResponse)
async def assemble_component(request: ComponentRequest):
    """装配 USD Component"""
    try:
        base_path = os.path.abspath(request.base_path)
        component_name = request.component_name or os.path.basename(base_path)

        if not os.path.exists(base_path):
            raise HTTPException(status_code=404, detail=f"路径不存在: {base_path}")

        # 检查几何体文件
        geom_file = os.path.join(base_path, f"{component_name}_geom.usd")
        geom_stage = await asyncio.to_thread(read_existing_geom_file, geom_file)

        if not geom_stage:
            raise HTTPException(status_code=400, detail=f"未找到几何体文件: {geom_file}")

        # 处理组件
        await asyncio.to_thread(process_component, base_path, component_name)

        generated_files = [
            f"{component_name}.usda",
            f"{component_name}_payload.usda",
            f"{component_name}_look.usda",
            f"{component_name}_mat.mtlx",
        ]

        return AssemblyResponse(
            success=True,
            message=f"Component {component_name} 装配完成",
            generated_files=generated_files,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"装配失败: {e!s}")


@app.post("/assemble/subcomponent", response_model=AssemblyResponse)
async def assemble_subcomponent(request: SubcomponentRequest):
    """装配 USD Subcomponent"""
    try:
        base_path = os.path.abspath(request.base_path)
        subcomponent_name = request.subcomponent_name or os.path.basename(base_path)

        if not os.path.exists(base_path):
            raise HTTPException(status_code=404, detail=f"路径不存在: {base_path}")

        # 检查几何体文件
        geom_file = os.path.join(base_path, f"{subcomponent_name}_geom.usd")
        geom_stage = await asyncio.to_thread(read_existing_geom_file, geom_file)

        if not geom_stage:
            raise HTTPException(status_code=400, detail=f"未找到几何体文件: {geom_file}")

        # 处理子组件 (目前逻辑与 component 相同)
        await asyncio.to_thread(process_component, base_path, subcomponent_name)

        generated_files = [
            f"{subcomponent_name}.usda",
            f"{subcomponent_name}_payload.usda",
            f"{subcomponent_name}_look.usda",
            f"{subcomponent_name}_mat.mtlx",
        ]

        return AssemblyResponse(
            success=True,
            message=f"Subcomponent {subcomponent_name} 装配完成",
            generated_files=generated_files,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"装配失败: {e!s}")


@app.get("/scan/components")
async def scan_components_api(base_path: str = "./"):
    """扫描目录中的组件"""
    try:
        base_path = os.path.abspath(base_path)

        if not os.path.exists(base_path):
            raise HTTPException(status_code=404, detail=f"路径不存在: {base_path}")

        components = await asyncio.to_thread(scan_components, base_path)

        return {
            "base_path": base_path,
            "components": components,
            "count": len(components),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"扫描失败: {e!s}")


@app.get("/info/component", response_model=ComponentInfo)
async def get_component_info(component_path: str):
    """获取组件信息"""
    try:
        component_path = os.path.abspath(component_path)
        component_name = os.path.basename(component_path)

        if not os.path.exists(component_path):
            raise HTTPException(status_code=404, detail=f"组件路径不存在: {component_path}")

        # 检查几何体文件
        geom_file = os.path.join(component_path, f"{component_name}_geom.usd")
        has_geometry = os.path.exists(geom_file)

        # 检测纹理文件
        texture_files = await asyncio.to_thread(
            detect_texture_files, component_path, component_name
        )

        # 检查已生成的文件
        generated_files = []
        potential_files = [
            f"{component_name}.usda",
            f"{component_name}_payload.usda",
            f"{component_name}_look.usda",
            f"{component_name}_mat.mtlx",
        ]

        for file in potential_files:
            file_path = os.path.join(component_path, file)
            if os.path.exists(file_path):
                generated_files.append(file)

        return ComponentInfo(
            name=component_name,
            path=component_path,
            has_geometry=has_geometry,
            texture_files=texture_files,
            generated_files=generated_files,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取组件信息失败: {e!s}")


@app.get("/download/{file_type}")
async def download_file(file_type: str, base_path: str, component_name: str = None):
    """下载生成的文件"""
    try:
        base_path = os.path.abspath(base_path)

        if not os.path.exists(base_path):
            raise HTTPException(status_code=404, detail=f"路径不存在: {base_path}")

        if file_type == "assembly":
            assembly_name = os.path.basename(base_path)
            file_path = os.path.join(base_path, f"{assembly_name}.usda")
            filename = f"{assembly_name}.usda"
        elif file_type in ["component", "payload", "look", "material"]:
            if not component_name:
                raise HTTPException(
                    status_code=400, detail="Component 文件下载需要提供 component_name"
                )

            file_extensions = {
                "component": ".usda",
                "payload": "_payload.usda",
                "look": "_look.usda",
                "material": "_mat.mtlx",
            }

            extension = file_extensions[file_type]
            filename = f"{component_name}{extension}"
            file_path = os.path.join(base_path, filename)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_type}")

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"文件不存在: {filename}")

        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {e!s}")


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "service": "USDAssemble API"}


# 保留原有的计算接口作为示例
@app.get("/compute")
async def compute(n: int = 42) -> int:
    """Compute the result of a CPU-bound function."""

    def fibonacci(n: int) -> int:
        return n if n <= 1 else fibonacci(n - 1) + fibonacci(n - 2)

    result = await asyncio.to_thread(fibonacci, n)
    return result
