from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os
from dotenv import load_dotenv


@dataclass(frozen=True)
class AppPaths:
    root: Path
    kb_dir: Path
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

    # LLM (DeepSeek)
    llm_model: str = "deepseek-chat"
    deepseek_api_key_env: str = "DEEPSEEK_API_KEY"

    # Chunking / Retrieval
    chunk_size: int = 900
    chunk_overlap: int = 120
    top_k: int = 6


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
    kb_dir = root / "data" / "Avionics_files"
    storage_dir = root / "storage"
    qdrant_dir = storage_dir / "qdrant"

    paths = AppPaths(
        root=root,
        kb_dir=kb_dir,
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

