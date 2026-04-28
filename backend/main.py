"""
FastAPI 后端主入口
提供 RAG 需求解析和测试用例生成的 REST API
"""
from __future__ import annotations

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径，确保能导入 rag_avionics
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_avionics.indexing import build_or_load_index
from rag_avionics.pipeline import run_pipeline
from rag_avionics.settings import load_settings
from rag_avionics.export_excel import build_traceability_excel
from rag_avionics.evaluation import evaluate_excel


# 全局变量：索引和配置（单例模式，避免 Qdrant 多实例冲突）
_index = None
_paths = None
_ms = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理：启动时加载索引，关闭时清理资源"""
    global _index, _paths, _ms
    
    print("🚀 正在启动 FastAPI 服务...")
    _paths, _ms = load_settings()
    
    # 启动时加载索引（不重建）
    print("📚 正在加载向量索引...")
    _index = build_or_load_index(paths=_paths, ms=_ms, rebuild=False)
    print("✅ 索引加载完成！")
    
    yield
    
    # 关闭时清理（如果需要）
    print("👋 正在关闭服务...")


app = FastAPI(
    title="RAG 机载软件需求解析与测试用例生成系统",
    description="基于 RAG 的机载软件需求自动解析与测试用例生成 API",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 配置：允许前端跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite 默认端口 5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== API 数据模型 ====================

class RequirementInput(BaseModel):
    """需求输入"""
    requirement_text: str = Field(..., description="需求文本（支持多段）")
    llm_provider: str = Field("qwen", description="LLM 提供商：qwen/deepseek/zhipu")
    llm_model: str = Field("qwen3-max", description="具体模型名称")
    top_k: int = Field(3, ge=1, le=10, description="检索证据数量")
    window_size: int = Field(4, ge=2, le=8, description="句子窗口大小")


class AtomicRequirementResponse(BaseModel):
    """原子需求响应"""
    req_id: str
    statement: str
    category: Optional[str] = None
    source_req: Optional[str] = None
    source_text: Optional[str] = None


class TestCaseResponse(BaseModel):
    """测试用例响应"""
    tc_id: str
    title: str
    objective: str
    test_method: Optional[str] = None
    preconditions: Optional[str | list[str]] = None  # 支持字符串或列表
    inputs: Optional[str | list[str]] = None  # 支持字符串或列表
    steps: Optional[str | list[str]] = None  # 支持字符串或列表
    expected_results: Optional[str | list[str]] = None  # 支持字符串或列表
    design_rationale: Optional[str] = None
    trace_to_atomic_req: Optional[str] = None
    trace_to_source_req: Optional[str] = None
    evidence_refs: Optional[list[str]] = None


class PipelineResponse(BaseModel):
    """完整流程响应"""
    requirement_id: str
    domain_context: list[dict]
    atomic_requirements: list[AtomicRequirementResponse]
    evidences: dict[str, list[dict]]
    test_cases: list[TestCaseResponse]


# ==================== API 路由 ====================

@app.get("/")
async def root():
    """健康检查"""
    return {
        "status": "ok",
        "message": "RAG 机载软件需求解析与测试用例生成系统 API",
        "version": "2.0.0"
    }


@app.get("/api/health")
async def health_check():
    """健康检查（包含索引状态）"""
    return {
        "status": "healthy",
        "index_loaded": _index is not None,
        "embed_model": _ms.embed_model_name if _ms else None,
        "llm_provider": _ms.llm_provider if _ms else None
    }


@app.post("/api/rebuild-index")
async def rebuild_index():
    """重建向量索引（首次运行或数据更新时使用）"""
    global _index
    
    if not _paths or not _ms:
        raise HTTPException(status_code=500, detail="系统配置未加载")
    
    try:
        print("🔄 正在重建向量索引...")
        
        # 先删除整个 storage 目录，确保完全清理
        import shutil
        if _paths.storage_dir.exists():
            print(f"🗑️ 删除旧的 storage 目录: {_paths.storage_dir}")
            shutil.rmtree(_paths.storage_dir)
            print("✓ 旧数据已清理")
        
        _index = build_or_load_index(paths=_paths, ms=_ms, rebuild=True)
        print("✅ 索引重建完成！")
        return {"status": "success", "message": "向量索引重建完成"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重建索引失败: {str(e)}")


@app.post("/api/analyze", response_model=PipelineResponse)
async def analyze_requirement(req: RequirementInput):
    """
    分析需求并生成原子需求和测试用例
    
    完整流程：
    1. 预检索：提取术语并匹配词典
    2. 需求分解：生成原子需求
    3. 证据检索：双路检索（标准文档 + SRD）
    4. 用例生成：生成 IEEE 829 测试用例
    """
    if not _index:
        raise HTTPException(status_code=503, detail="向量索引未加载，请先重建索引")
    
    try:
        # 动态更新模型配置
        from dataclasses import replace
        ms_runtime = replace(
            _ms,
            llm_provider=req.llm_provider,
            top_k=req.top_k,
            sentence_window_size=req.window_size
        )
        
        # 根据提供商设置具体模型
        if req.llm_provider == "deepseek":
            ms_runtime = replace(ms_runtime, deepseek_model=req.llm_model)
        elif req.llm_provider == "zhipu":
            ms_runtime = replace(ms_runtime, zhipu_model=req.llm_model)
        else:  # qwen
            ms_runtime = replace(ms_runtime, qwen_model=req.llm_model)
        
        # 运行 RAG 流程
        result = run_pipeline(
            index=_index,
            ms=ms_runtime,
            requirement_text=req.requirement_text
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@app.post("/api/export-excel")
async def export_excel(req: RequirementInput):
    """
    导出追溯矩阵 Excel（重新分析）
    
    返回二进制文件流
    """
    if not _index:
        raise HTTPException(status_code=503, detail="向量索引未加载")
    
    try:
        # 运行流程
        from dataclasses import replace
        ms_runtime = replace(
            _ms,
            llm_provider=req.llm_provider,
            top_k=req.top_k,
            sentence_window_size=req.window_size
        )
        
        if req.llm_provider == "deepseek":
            ms_runtime = replace(ms_runtime, deepseek_model=req.llm_model)
        elif req.llm_provider == "zhipu":
            ms_runtime = replace(ms_runtime, zhipu_model=req.llm_model)
        else:
            ms_runtime = replace(ms_runtime, qwen_model=req.llm_model)
        
        result = run_pipeline(
            index=_index,
            ms=ms_runtime,
            requirement_text=req.requirement_text
        )
        
        # 生成 Excel
        excel_bytes = build_traceability_excel(result)
        
        from fastapi.responses import Response
        req_id = result.get("requirement_id", "UNKNOWN")
        filename = f"traceability_{req_id}.xlsx"
        
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.post("/api/export-excel-direct")
async def export_excel_direct(result: dict):
    """
    导出追溯矩阵 Excel（使用已有结果，不重新分析）
    
    直接接收前端已分析的结果，快速生成 Excel
    """
    try:
        print(f"📊 开始导出 Excel...")
        print(f"  收到的数据键: {list(result.keys())}")
        
        # 生成 Excel（直接使用字典）
        excel_bytes = build_traceability_excel(result)
        
        req_id = result.get("requirement_id", "UNKNOWN")
        filename = f"traceability_{req_id}.xlsx"
        
        print(f"✅ Excel 生成成功: {filename}")
        
        from fastapi.responses import Response
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ 导出 Excel 失败:")
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")


@app.post("/api/evaluate")
async def evaluate_report(
    request_data: dict
):
    """
    评估生成的测试用例质量
    
    对已生成的结果进行四个维度的评估：
    1. 需求覆盖完整度
    2. 用例结构规范性
    3. 测试方法与逻辑合理性（可选 LLM 盲评）
    4. 追溯链路与证据完整性
    
    Args:
        request_data: 包含 result, enable_llm, llm_provider, llm_model 的字典
    
    Returns:
        评估结果的 JSON 对象
    """
    try:
        result = request_data.get("result", {})
        enable_llm = request_data.get("enable_llm", False)
        llm_provider = request_data.get("llm_provider", "qwen")
        llm_model = request_data.get("llm_model", "qwen3-max")
        
        print(f"📊 开始评估...")
        print(f"  收到的数据键: {list(result.keys())}")
        print(f"  原子需求数量: {len(result.get('atomic_requirements', []))}")
        print(f"  测试用例数量: {len(result.get('test_cases', []))}")
        
        # 打印第一个原子需求的键，用于调试
        if result.get('atomic_requirements'):
            first_ar = result['atomic_requirements'][0]
            print(f"  第一个原子需求的键: {list(first_ar.keys())}")
            print(f"  第一个原子需求: {first_ar}")
        
        print(f"  LLM 盲评: {'启用' if enable_llm else '禁用'}")
        
        # 先生成 Excel（评估需要读取 Excel 文件）
        excel_bytes = build_traceability_excel(result)
        
        # 如果启用 LLM，创建 LLM 实例
        llm = None
        if enable_llm:
            from dataclasses import replace
            from rag_avionics.llm import make_llm
            
            print(f"  LLM 提供商: {llm_provider}")
            print(f"  LLM 模型: {llm_model}")
            
            # 动态创建模型配置
            ms_runtime = replace(_ms, llm_provider=llm_provider)
            
            if llm_provider == "deepseek":
                ms_runtime = replace(ms_runtime, deepseek_model=llm_model)
            elif llm_provider == "zhipu":
                ms_runtime = replace(ms_runtime, zhipu_model=llm_model)
            else:  # qwen
                ms_runtime = replace(ms_runtime, qwen_model=llm_model)
            
            # 创建 LLM 实例（温度设为 0.1 以获得更稳定的评分）
            llm = make_llm(ms_runtime, temperature=0.1)
        
        # 执行评估
        evaluation_result = evaluate_excel(excel_bytes, enable_llm=enable_llm, llm=llm)
        
        print(f"✅ 评估完成")
        
        return evaluation_result.to_dict()
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ 评估失败:")
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


@app.post("/api/evaluate-from-file")
async def evaluate_from_uploaded_file(file: bytes, enable_llm: bool = False):
    """
    评估上传的 Excel 文件
    
    用户可以上传已有的 Excel 文件进行评估
    
    Args:
        file: 上传的 Excel 文件字节流
        enable_llm: 是否启用 LLM 盲评
    
    Returns:
        评估结果的 JSON 对象
    """
    try:
        print(f"📊 开始评估上传的文件...")
        print(f"  文件大小: {len(file)} 字节")
        print(f"  LLM 盲评: {'启用' if enable_llm else '禁用'}")
        
        # 执行评估
        evaluation_result = evaluate_excel(file, enable_llm=enable_llm)
        
        print(f"✅ 评估完成")
        
        return evaluation_result.to_dict()
        
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        print(f"❌ 评估失败:")
        print(error_detail)
        raise HTTPException(status_code=500, detail=f"评估失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # 开发模式热重载
        log_level="info"
    )
