from __future__ import annotations

from pathlib import Path
from typing import Optional

from llama_index.core import VectorStoreIndex, SimpleDirectoryReader
from llama_index.core.node_parser import SentenceWindowNodeParser, SentenceSplitter
from llama_index.core.postprocessor import MetadataReplacementPostProcessor
from llama_index.core.storage import StorageContext
from llama_index.core import Settings
from llama_index.core.vector_stores import ExactMatchFilter, MetadataFilters
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from .settings import AppPaths, ModelSettings


def configure_llamaindex(paths: AppPaths, ms: ModelSettings) -> None:
    """配置 LlamaIndex 全局 Settings（embedding）。
    注意：不再设置全局 node_parser，因为需要针对不同文档类型使用不同策略。
    """
    paths.storage_dir.mkdir(parents=True, exist_ok=True)
    paths.qdrant_dir.mkdir(parents=True, exist_ok=True)

    # 如果 embed_device 为 None，HuggingFaceEmbedding 会自动检测 GPU
    # 如果设置为 "cuda"，会显式使用 GPU
    Settings.embed_model = HuggingFaceEmbedding(
        model_name=ms.embed_model_name,
        device=ms.embed_device
    )


def _qdrant(paths: AppPaths) -> QdrantClient:
    """使用本地持久化 Qdrant（无需单独起服务）。
    如果遇到锁文件问题，会尝试自动清理。
    """
    qdrant_path = str(paths.qdrant_dir)
    lock_file = paths.qdrant_dir / ".lock"
    
    try:
        return QdrantClient(path=qdrant_path)
    except RuntimeError as e:
        if "already accessed" in str(e):
            print(f"⚠️ 检测到 Qdrant 锁文件冲突")
            print(f"  尝试清理锁文件: {lock_file}")
            
            # 尝试删除锁文件
            try:
                if lock_file.exists():
                    lock_file.unlink()
                    print(f"  ✓ 已删除锁文件，重试连接...")
                    return QdrantClient(path=qdrant_path)
            except Exception as cleanup_error:
                print(f"  ✗ 清理失败: {cleanup_error}")
            
            # 如果还是失败，给出明确提示
            print("\n" + "=" * 70)
            print("解决方案：")
            print("  1. 关闭所有 Python 进程（包括其他 Streamlit 或测试脚本）")
            print("  2. 手动删除锁文件：storage/qdrant/.lock")
            print("  3. 或运行：fix_qdrant_lock.bat")
            print("=" * 70 + "\n")
        raise


def build_or_load_index(
    *,
    paths: AppPaths,
    ms: ModelSettings,
    collection_name: str = "avionics_kb",
    rebuild: bool = False,
) -> VectorStoreIndex:
    """构建或加载向量索引（双分块策略）。
    - 标准文档（Avionics_standards）：句子窗口检索
    - SRD 文档（Avionics_srd）：固定大小分块
    - 使用 Qdrant 本地持久化向量库
    """
    configure_llamaindex(paths, ms)

    qdrant_client = _qdrant(paths)
    vector_store = QdrantVectorStore(client=qdrant_client, collection_name=collection_name)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    if rebuild:
        try:
            qdrant_client.delete_collection(collection_name=collection_name)
            print(f"✓ 已删除旧的向量库: {collection_name}")
        except Exception:
            pass

    # 如果 collection 已存在并且不要求 rebuild，直接从已有向量库"重建"索引对象
    if not rebuild:
        try:
            info = qdrant_client.get_collection(collection_name=collection_name)
            if info is not None:
                print(f"✓ 加载已有向量库: {collection_name}")
                return VectorStoreIndex.from_vector_store(
                    vector_store=vector_store, storage_context=storage_context
                )
        except Exception:
            # collection 不存在或连接异常，走构建流程
            pass

    # === 构建新索引：双分块策略 ===
    print("\n" + "=" * 70)
    print("开始构建向量索引（双分块策略）")
    print("=" * 70)
    
    all_nodes = []
    
    # 1. 处理标准文档（句子窗口检索）
    if paths.kb_dir.exists():
        print(f"\n[1/2] 处理标准文档: {paths.kb_dir}")
        print(f"  策略: 句子窗口检索（窗口大小={ms.sentence_window_size}）")
        
        standard_docs = SimpleDirectoryReader(
            input_dir=str(paths.kb_dir), 
            recursive=True
        ).load_data()
        
        if standard_docs:
            # 添加 category 标签
            for doc in standard_docs:
                doc.metadata["category"] = "Standards"
            
            # 使用句子窗口分块器
            standard_parser = SentenceWindowNodeParser.from_defaults(
                window_size=ms.sentence_window_size,
                window_metadata_key="window",
                original_text_metadata_key="original_sentence",
            )
            standard_nodes = standard_parser.get_nodes_from_documents(standard_docs)
            all_nodes.extend(standard_nodes)
            print(f"  ✓ 生成 {len(standard_nodes)} 个节点")
        else:
            print(f"  ⚠️ 目录为空")
    else:
        print(f"\n[1/2] ⚠️ 标准文档目录不存在: {paths.kb_dir}")
    
    # 2. 处理 SRD 文档（固定大小分块）
    if paths.srd_dir.exists():
        print(f"\n[2/2] 处理 SRD 文档: {paths.srd_dir}")
        print(f"  策略: 固定大小分块（chunk_size={ms.srd_chunk_size}, overlap={ms.srd_chunk_overlap}）")
        
        srd_docs = SimpleDirectoryReader(
            input_dir=str(paths.srd_dir), 
            recursive=True
        ).load_data()
        
        if srd_docs:
            # 添加 category 标签
            for doc in srd_docs:
                doc.metadata["category"] = "SRD_Context"
            
            # 使用固定大小分块器（优先按段落切分）
            srd_parser = SentenceSplitter(
                chunk_size=ms.srd_chunk_size,
                chunk_overlap=ms.srd_chunk_overlap,
                separator="\n\n"  # 优先按段落切分
            )
            srd_nodes = srd_parser.get_nodes_from_documents(srd_docs)
            all_nodes.extend(srd_nodes)
            print(f"  ✓ 生成 {len(srd_nodes)} 个节点")
        else:
            print(f"  ⚠️ 目录为空")
    else:
        print(f"\n[2/2] ⚠️ SRD 文档目录不存在: {paths.srd_dir}")
    
    if not all_nodes:
        raise FileNotFoundError(
            f"未找到任何文档！\n"
            f"  标准文档目录: {paths.kb_dir} (必须)\n"
            f"  SRD 文档目录: {paths.srd_dir} (可选)"
        )
    
    print(f"\n{'=' * 70}")
    print(f"总计: {len(all_nodes)} 个节点")
    print(f"{'=' * 70}\n")
    
    # 构建索引
    print("正在构建向量索引...")
    index = VectorStoreIndex(
        nodes=all_nodes,
        storage_context=storage_context,
        show_progress=True
    )
    print("✓ 向量索引构建完成\n")
    
    return index


def retrieve_context(
    index: VectorStoreIndex,
    query: str,
    *,
    top_k: int,
) -> list[dict]:
    """检索证据片段（用于 UI 展示与可追溯性）。
    使用句子窗口检索：检索时匹配单句，返回时包含扩展的上下文窗口。
    
    关键：使用 MetadataReplacementPostProcessor 将 node 内容替换为窗口文本，
    避免"原始短句 + window"的重复叠加问题。
    """
    retriever = index.as_retriever(similarity_top_k=top_k)
    
    # 后处理器：将 node.get_content() 替换为 metadata["window"]
    postprocessor = MetadataReplacementPostProcessor(target_metadata_key="window")
    
    # 先检索，再应用后处理器
    nodes = retriever.retrieve(query)
    nodes = postprocessor.postprocess_nodes(nodes)
    
    results: list[dict] = []
    for n in nodes:
        meta = dict(n.node.metadata or {})
        ref = _build_evidence_ref(meta)
        # 此时 n.node.get_content() 已经是窗口扩展后的文本
        text = n.node.get_content()
        original_sentence = meta.get("original_sentence", "")
        results.append(
            {
                "score": float(getattr(n, "score", 0.0) or 0.0),
                "text": text,
                "original_sentence": original_sentence,
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



def retrieve_context_dual(
    index: VectorStoreIndex,
    query: str,
    *,
    standards_top_k: int = 3,
    srd_top_k: int = 3,
) -> list[dict]:
    """双路检索：分别从标准文档和 SRD 文档中检索，确保两类证据都被获取。
    
    Args:
        index: 向量索引
        query: 查询文本
        standards_top_k: 从标准文档中检索的数量
        srd_top_k: 从 SRD 文档中检索的数量
    
    Returns:
        合并后的检索结果列表
    """
    print(f"🔍 正在双路检索: {query[:50]}...")
    
    all_results = []
    
    # 1. 标准文档专线（强制抓取标准证据）
    try:
        std_filters = MetadataFilters(
            filters=[ExactMatchFilter(key="category", value="Standards")]
        )
        standard_retriever = VectorIndexRetriever(
            index=index,
            filters=std_filters,
            similarity_top_k=standards_top_k
        )
        
        # 后处理器：替换为窗口文本（仅对标准文档有效）
        postprocessor = MetadataReplacementPostProcessor(target_metadata_key="window")
        
        std_nodes = standard_retriever.retrieve(query)
        std_nodes = postprocessor.postprocess_nodes(std_nodes)
        
        for n in std_nodes:
            meta = dict(n.node.metadata or {})
            ref = _build_evidence_ref(meta)
            text = n.node.get_content()
            original_sentence = meta.get("original_sentence", "")
            all_results.append({
                "score": float(getattr(n, "score", 0.0) or 0.0),
                "text": text,
                "original_sentence": original_sentence,
                "metadata": meta,
                "ref": ref,
                "category": "Standards"
            })
        
        print(f"  ✓ 标准文档: {len(std_nodes)} 条证据")
    except Exception as e:
        print(f"  ⚠️ 标准文档检索失败: {e}")
    
    # 2. SRD 文档专线（强制抓取 SRD 证据）
    try:
        srd_filters = MetadataFilters(
            filters=[ExactMatchFilter(key="category", value="SRD_Context")]
        )
        srd_retriever = VectorIndexRetriever(
            index=index,
            filters=srd_filters,
            similarity_top_k=srd_top_k
        )
        
        srd_nodes = srd_retriever.retrieve(query)
        
        for n in srd_nodes:
            meta = dict(n.node.metadata or {})
            ref = _build_evidence_ref(meta)
            text = n.node.get_content()
            all_results.append({
                "score": float(getattr(n, "score", 0.0) or 0.0),
                "text": text,
                "original_sentence": "",
                "metadata": meta,
                "ref": ref,
                "category": "SRD_Context"
            })
        
        print(f"  ✓ SRD 文档: {len(srd_nodes)} 条证据")
    except Exception as e:
        print(f"  ⚠️ SRD 文档检索失败: {e}")
    
    print(f"✅ 双路检索完成！总计: {len(all_results)} 条证据\n")
    
    return all_results
