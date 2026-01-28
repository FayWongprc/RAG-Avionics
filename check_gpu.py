import torch

print("=" * 50)
print("PyTorch 版本信息")
print("=" * 50)
print(f"PyTorch 版本: {torch.__version__}")
print(f"CUDA 可用: {torch.cuda.is_available()}")
print(f"CUDA 版本: {torch.version.cuda if torch.cuda.is_available() else 'N/A'}")

if torch.cuda.is_available():
    print(f"GPU 数量: {torch.cuda.device_count()}")
    print(f"当前 GPU: {torch.cuda.get_device_name(0)}")
    print(f"GPU 设备: {torch.cuda.current_device()}")
    print("\n[成功] 已安装 GPU 版本的 PyTorch！")
    
    # 简单测试 GPU 计算
    x = torch.randn(3, 3).cuda()
    print(f"[成功] GPU 张量测试成功: {x.device}")
else:
    print("\n[错误] 未检测到 CUDA")
    print("当前安装的是 CPU 版本（版本号显示为 +cpu）")
    print("需要卸载后重新安装 GPU 版本")
print("=" * 50)
