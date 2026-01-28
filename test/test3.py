import torch
# 1. 查看PyTorch版本
print("PyTorch版本：", torch.__version__)
# 2. 核心验证：是否能调用CUDA（返回True=成功，False=失败）
print("CUDA是否可用：", torch.cuda.is_available())
# 3. 查看显卡名称（可选）
if torch.cuda.is_available():
    print("显卡型号：", torch.cuda.get_device_name(0))
    print("GPU显存：", torch.cuda.get_device_properties(0).total_memory / 1024 / 1024, "MB")
import torch
print(torch.__version__)  # 看PyTorch版本
print(torch.version.cuda) # 看PyTorch绑定的CUDA版本