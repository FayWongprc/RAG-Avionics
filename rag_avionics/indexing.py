from __future__ import annotations

from pathlib import Path
from typing import Optional

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.storage import StorageContext
from llama_index.core import Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from .settings import AppPaths, ModelSettings


def configure_llamaindex(paths: AppPaths, ms: ModelSettings) -> None:
    """配置 LlamaIndex 全局 Settings（embedding + 分块）。"""
    paths.storage_dir.mkdir(parents=True, exist_ok=True)
    paths.qdrant_dir.mkdir(parents=True, exist_ok=True)

    # 如果 embed_device 为 None，HuggingFaceEmbedding 会自动检测 GPU
    # 如果设置为 "cuda"，会显式使用 GPU
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=ms.embed_model_name,
        device=ms.embed_device
    )
    Settings.node_parser = SentenceSplitter(
        chunk_size=ms.chunk_size, chunk_overlap=ms.chunk_overlap
    )


def _qdrant(paths: AppPaths) -> QdrantClient:
    # 使用本地持久化 Qdrant（无需单独起服务）
    return QdrantClient(path=str(paths.qdrant_dir))


def build_or_load_index(
    *,
    paths: AppPaths,
    ms: ModelSettings,
    collection_name: str = "avionics_kb",
    rebuild: bool = False,
) -> VectorStoreIndex:
    """构建或加载向量索引。

    - 使用 Qdrant 本地持久化向量库
    - 使用 LlamaIndex 负责读取 PDF、分块、入库
    """
    configure_llamaindex(paths, ms)

    qdrant_client = _qdrant(paths)
    vector_store = QdrantVectorStore(client=qdrant_client, collection_name=collection_name)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    if rebuild:
        try:
            qdrant_client.delete_collection(collection_name=collection_name)
        except Exception:
            pass

    # 如果 collection 已存在并且不要求 rebuild，直接从已有向量库“重建”索引对象
    if not rebuild:
        try:
            info = qdrant_client.get_collection(collection_name=collection_name)
            if info is not None:
                return VectorStoreIndex.from_vector_store(
                    vector_store=vector_store, storage_context=storage_context
                )
        except Exception:
            # collection 不存在或连接异常，走构建流程
            pass

    if not paths.kb_dir.exists():
        raise FileNotFoundError(f"知识库目录不存在: {paths.kb_dir}")

    documents = SimpleDirectoryReader(input_dir=str(paths.kb_dir), recursive=True).load_data()
    return VectorStoreIndex.from_documents(documents, storage_context=storage_context)


def retrieve_context(
    index: VectorStoreIndex,
    query: str,
    *,
    top_k: int,
) -> list[dict]:
    """检索证据片段（用于 UI 展示与可追溯性）。"""
    retriever = index.as_retriever(similarity_top_k=top_k)
    nodes = retriever.retrieve(query)
    results: list[dict] = []
    for n in nodes:
        meta = dict(n.node.metadata or {})
        ref = _build_evidence_ref(meta)
        results.append(
            {
                "score": float(getattr(n, "score", 0.0) or 0.0),
                "text": n.node.get_content(),
                "metadata": meta,
                "ref": ref,
            }
        )
    return results


def _build_evidence_ref(meta: dict) -> str:
    """将 LlamaIndex 的 node.metadata 尽量归一成可读的证据引用（文件名/页码等）。"""
    file_path = meta.get("file_path") or meta.get("source") or meta.get("filename")
    file_name = None
    if isinstance(file_path, str) and file_path:
        try:
            file_name = Path(file_path).name
        except Exception:
            file_name = file_path

    # 不同 reader 可能使用不同字段
    page = (
        meta.get("page_label")
        or meta.get("page_number")
        or meta.get("page")
        or meta.get("pagenum")
    )
    section = meta.get("section") or meta.get("heading") or meta.get("chapter")

    parts: list[str] = []
    if file_name:
        parts.append(str(file_name))
    if page is not None and str(page).strip() != "":
        parts.append(f"p.{page}")
    if section:
        parts.append(str(section))

    if parts:
        return " | ".join(parts)
    return "KB"
