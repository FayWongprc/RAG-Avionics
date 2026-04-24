from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv


@dataclass(frozen=True)
class AppPaths:
    root: Path
    kb_dir: Path
    srd_dir: Path  # 新增：软件需求文档目录
    storage_dir: Path
    qdrant_dir: Path


@dataclass(frozen=True)
class ModelSettings:
    # Embeddings
    #embed_model_name: str = "BAAI/bge-small-zh" #中文优化
    #embed_model_name: str = "BAAI/bge-small-en-v1.5"  # 英文优化
    embed_model_name: str = "BAAI/bge-m3"  # 推荐：多语言
    
    # Device for embeddings (None = auto-detect, "cuda" = GPU, "cpu" = CPU)
    # 如果设置为 None，会自动检测是否有 GPU 可用
    embed_device: str | None = None  # None = auto-detect, "cuda" = GPU, "cpu" = CPU

    # LLM Provider Selection
    llm_provider: str = "deepseek"  # 可选: "deepseek", "zhipu", "qwen"
    
    # DeepSeek 模型配置
    deepseek_model: str = "deepseek-v4-flash"  # DeepSeek 模型名称
    deepseek_api_key_env: str = "DEEPSEEK_API_KEY"
    
    # 智谱 模型配置
    zhipu_model: str = "glm-5"  # 智谱模型: "glm-5", "glm-4-plus", "glm-4-flash", "glm-4.7" 等
    zhipu_api_key_env: str = "ZHIPU_API_KEY"
    
    # 千问 模型配置
    qwen_model: str = "qwen3-max"  # 千问模型: "qwen3-max", "qwen3.5-plus", "qwen-plus" 等
    qwen_api_key_env: str = "DASHSCOPE_API_KEY"

    # Sentence Window Retrieval (用于标准文档)
    sentence_window_size: int = 4  # 前后各扩展 6 句，保证上下文完整性
    
    # Fixed Chunking (用于 SRD 软件需求文档)
    srd_chunk_size: int = 512      # SRD 大块策略，确保逻辑段落完整
    srd_chunk_overlap: int = 100   # 重叠度，防止因果链在边缘处丢失
    
    # Retrieval
    top_k: int = 3


def _detect_device() -> str | None:
    """检测可用的设备，优先使用 GPU。"""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return None  # None 会让 HuggingFaceEmbedding 自动检测，回退到 CPU


def load_settings() -> tuple[AppPaths, ModelSettings]:
    """加载环境变量并返回路径与模型配置。"""
    load_dotenv(override=False)

    root = Path(__file__).resolve().parents[1]
    kb_dir = root / "data" / "Avionics_standards"
    srd_dir = root / "data" / "Avionics_srd"  # 新增：SRD 目录
    storage_dir = root / "storage"
    qdrant_dir = storage_dir / "qdrant"

    paths = AppPaths(
        root=root,
        kb_dir=kb_dir,
        srd_dir=srd_dir,
        storage_dir=storage_dir,
        qdrant_dir=qdrant_dir,
    )
    
    # 自动检测并优先使用 GPU
    detected_device = _detect_device()
    ms = ModelSettings(embed_device=detected_device)
    return paths, ms


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"缺少环境变量 {name}。请在 .env 中配置，或在系统环境变量里设置。"
        )
    return value

