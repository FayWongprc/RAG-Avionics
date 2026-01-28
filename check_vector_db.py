"""
检查向量库信息的脚本
用于验证向量库是否使用了正确的embedding模型
"""
import sys
import io
# 修复Windows控制台编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from pathlib import Path
from qdrant_client import QdrantClient
from rag_avionics.settings import load_settings

def get_embedding_dimension(model_name: str) -> int:
    """获取不同模型的向量维度"""
    dimension_map = {
        "BAAI/bge-small-zh": 512,
        "BAAI/bge-small-en-v1.5": 384,
        "BAAI/bge-m3": 1024,
    }
    return dimension_map.get(model_name, -1)

def check_vector_db():
    """检查向量库的配置和维度信息"""
    paths, ms = load_settings()
    
    print("=" * 60)
    print("向量库检查报告")
    print("=" * 60)
    
    # 显示当前配置
    print(f"\n[当前配置]")
    print(f"  Embedding模型: {ms.embed_model_name}")
    expected_dim = get_embedding_dimension(ms.embed_model_name)
    if expected_dim > 0:
        print(f"  预期向量维度: {expected_dim}")
    else:
        print(f"  预期向量维度: 未知（请手动检查）")
    
    # 检查Qdrant集合
    collection_name = "avionics_kb"
    qdrant_dir = paths.qdrant_dir
    
    print(f"\n[向量库路径]")
    print(f"  Qdrant目录: {qdrant_dir}")
    print(f"  集合名称: {collection_name}")
    
    if not qdrant_dir.exists():
        print(f"\n[!] 警告: Qdrant目录不存在，向量库尚未构建")
        print(f"   建议: 首次运行时请在Streamlit界面勾选'重建向量库'")
        return
    
    try:
        client = QdrantClient(path=str(qdrant_dir))
        
        # 检查集合是否存在
        collections = client.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if collection_name not in collection_names:
            print(f"\n[!] 警告: 集合 '{collection_name}' 不存在")
            if collection_names:
                print(f"   现有集合: {', '.join(collection_names)}")
            else:
                print(f"   向量库为空，需要构建")
            return
        
        # 获取集合信息
        info = client.get_collection(collection_name=collection_name)
        actual_dim = None
        
        # 从集合配置中获取向量维度
        if info.config and info.config.params and info.config.params.vectors:
            vectors_config = info.config.params.vectors
            if hasattr(vectors_config, 'size'):
                actual_dim = vectors_config.size
            elif hasattr(vectors_config, 'dense'):
                actual_dim = vectors_config.dense.size
        
        print(f"\n[向量库信息]")
        print(f"  集合状态: {info.status}")
        print(f"  向量数量: {info.points_count or 0}")
        
        if actual_dim is not None:
            print(f"  实际向量维度: {actual_dim}")
            
            # 对比预期维度
            if expected_dim > 0:
                if actual_dim == expected_dim:
                    print(f"\n[V] 匹配成功!")
                    print(f"   向量库维度 ({actual_dim}) 与配置的模型 ({ms.embed_model_name}) 匹配")
                    print(f"   向量库应该是用 {ms.embed_model_name} 构建的")
                else:
                    print(f"\n[X] 维度不匹配!")
                    print(f"   向量库维度: {actual_dim}")
                    print(f"   配置模型维度: {expected_dim}")
                    print(f"   配置模型: {ms.embed_model_name}")
                    print(f"\n   可能的原因:")
                    print(f"   1. 向量库是用其他模型构建的")
                    print(f"   2. 配置文件已更改，但向量库未重建")
                    print(f"\n   建议操作:")
                    print(f"   - 在Streamlit界面勾选'重建向量库'，重新构建向量库")
                    print(f"   - 或者检查之前的配置，确认使用了哪个模型")
            else:
                print(f"\n[!] 无法判断: 无法确定配置模型的预期维度")
        else:
            print(f"\n[!] 无法获取向量维度信息")
        
    except RuntimeError as e:
        if "already accessed by another instance" in str(e):
            print(f"\n[!] 注意: 向量库正在被其他进程使用（可能是Streamlit应用正在运行）")
            print(f"   请先关闭Streamlit应用，然后重新运行此脚本")
            print(f"   或者直接在Streamlit应用中查看配置（当前配置的模型是: {ms.embed_model_name}）")
        else:
            print(f"\n[X] 错误: 无法读取向量库信息")
            print(f"   错误详情: {e}")
    except Exception as e:
        print(f"\n[X] 错误: 无法读取向量库信息")
        print(f"   错误详情: {e}")

if __name__ == "__main__":
    check_vector_db()