"""测试项目是否自动使用 GPU"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from rag_avionics.settings import load_settings, _detect_device
from rag_avionics.indexing import configure_llamaindex

print("=" * 60)
print("GPU 自动检测与使用测试")
print("=" * 60)

# 1. 测试设备检测
print("\n[1] 检测可用设备...")
detected_device = _detect_device()
print(f"    检测到的设备: {detected_device}")

if detected_device == "cuda":
    try:
        import torch
        print(f"    GPU 名称: {torch.cuda.get_device_name(0)}")
        print(f"    CUDA 版本: {torch.version.cuda}")
    except Exception as e:
        print(f"    获取 GPU 信息失败: {e}")
else:
    print("    将使用 CPU（GPU 不可用）")

# 2. 测试配置加载
print("\n[2] 加载项目配置...")
try:
    paths, ms = load_settings()
    print(f"    Embedding 模型: {ms.embed_model_name}")
    print(f"    配置的设备: {ms.embed_device}")
    if ms.embed_device == "cuda":
        print("    [成功] 已配置为使用 GPU")
    elif ms.embed_device is None:
        print("    [警告] 设备设置为 None（将自动检测）")
    else:
        print(f"    设备配置: {ms.embed_device}")
except Exception as e:
    print(f"    [错误] 配置加载失败: {e}")
    sys.exit(1)

# 3. 测试模型初始化（只初始化，不加载完整模型以节省时间）
print("\n[3] 测试模型初始化（使用 GPU 检测）...")
print("    注意：这一步会下载模型（如果是第一次），可能需要一些时间...")
try:
    configure_llamaindex(paths, ms)
    from llama_index.core import Settings
    embed_model = Settings.embed_model
    
    # 尝试获取设备信息
    if hasattr(embed_model, '_device'):
        device = embed_model._device
        print(f"    [成功] Embedding 模型设备: {device}")
        if device == "cuda":
            print("    [成功] 成功使用 GPU！")
        else:
            print(f"    使用设备: {device}")
    else:
        print("    [警告] 无法获取设备信息（但模型已初始化）")
except Exception as e:
    print(f"    [错误] 模型初始化失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
