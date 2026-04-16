# PyTorch 升级到 2.6+ 指南

## 当前状态
- **当前版本**: PyTorch 2.5.1+cu121
- **目标版本**: PyTorch 2.6.0+ (GPU 版本)
- **系统 CUDA**: 12.7（向下兼容）

## ⚠️ 升级原因
transformers 库要求 PyTorch >= 2.6 才能安全加载模型权重。

## 📋 升级步骤

### 方法 1：使用批处理脚本（推荐）
直接运行 `upgrade_pytorch.bat`，脚本会自动完成所有步骤。

### 方法 2：手动执行命令

**步骤 1：激活虚拟环境并卸载旧版本**
```bash
.\rag_venv\Scripts\Activate.ps1
pip uninstall torch torchvision torchaudio -y
```

**步骤 2：升级 pip**
```bash
python -m pip install --upgrade pip
```

**步骤 3：安装 PyTorch 2.6.0 (CUDA 12.6)**
```bash
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126
```

**如果 cu126 不可用，尝试 cu124：**
```bash
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```

**步骤 4：验证安装**
```bash
python check_gpu.py
```

应该看到：
- PyTorch 版本：`2.6.0+cu126` 或 `2.6.0+cu124`（不是 `+cpu`）
- CUDA 可用：`True`

## 🔍 版本选择说明

### CUDA 版本选择
- **cu126**：CUDA 12.6（推荐，支持 CUDA 12.7）
- **cu124**：CUDA 12.4（备选）
- **cu121**：PyTorch 2.6 不支持 cu121，需要升级到 cu124/126

### 为什么选择 cu126？
- 您的系统 CUDA 12.7 向下兼容 CUDA 12.6
- PyTorch 2.6 官方支持 cu126
- 性能更好，兼容性更广

## ⚠️ 注意事项

1. **备份虚拟环境**：升级前建议备份 `rag_venv` 目录
2. **依赖兼容性**：升级后确保其他依赖包与 PyTorch 2.6 兼容
3. **模型兼容性**：PyTorch 2.6 的模型权重与 2.5.1 兼容

## 🐛 常见问题

**Q: cu126 安装失败怎么办？**
A: 尝试 cu124，或检查网络连接。

**Q: 升级后其他包报错？**
A: 可能需要升级相关依赖包，如 `sentence-transformers`、`transformers` 等。

**Q: 如何回退到旧版本？**
A: 卸载 2.6，重新安装 2.5.1+cu121。

## ✅ 验证清单

- [ ] PyTorch 版本 >= 2.6.0
- [ ] CUDA 可用：True
- [ ] 版本号显示 `+cu126` 或 `+cu124`（不是 `+cpu`）
- [ ] GPU 名称正确显示
- [ ] 项目可以正常运行