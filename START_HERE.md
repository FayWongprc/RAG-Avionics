# 🎯 从这里开始！

## 欢迎使用 RAG 需求解析与测试用例生成系统 v2.0

**全新架构**: FastAPI + React | 已解决 Qdrant 锁文件问题 ✅

---

## 📋 快速检查清单

在开始之前，请确认以下事项：

- [ ] Python 3.10+ 已安装
- [ ] Node.js 16+ 已安装
- [ ] 已有至少一个 LLM API Key（千问/DeepSeek/智谱）

---

## 🚀 三步启动

### 第一步：验证安装

```bash
python check_installation.py
```

这个脚本会检查：
- ✅ Python 版本
- ✅ Python 包
- ✅ 前端文件
- ✅ 后端文件
- ✅ 数据目录
- ✅ 环境变量

如果有任何 ❌，请根据提示修复。

### 第二步：启动服务

**打开两个终端窗口：**

**终端 1（后端）**：
```bash
start_backend.bat
```
等待看到：`✅ 索引加载完成！`

**终端 2（前端）**：
```bash
start_frontend.bat
```
等待看到：`Local: http://localhost:5173/`

### 第三步：使用应用

1. 打开浏览器：http://localhost:5173
2. 点击左侧"检查状态"按钮
3. 如果是首次运行，点击"重建向量库"
4. 输入需求文本，点击"生成原子需求 + 测试用例"

---

## 📚 文档导航

### 新手必读
- [快速启动指南](QUICKSTART.md) - 5 分钟上手
- [迁移指南](MIGRATION_GUIDE.md) - 从 Streamlit 迁移

### 深入了解
- [完整 README](README.md) - 项目概览
- [变更日志](CHANGES.md) - 版本变更
- [项目总结](SUMMARY.md) - 改造详情

### API 文档
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 🐛 常见问题速查

### 问题 1: 后端启动失败
```
RuntimeError: Storage folder ... is already accessed
```

**解决方案**：
```bash
# 关闭所有 Python 进程
taskkill /F /IM python.exe

# 删除锁文件
del storage\qdrant\.lock

# 重新启动
start_backend.bat
```

### 问题 2: 前端无法连接后端
```
Network Error
```

**检查**：
1. 后端是否在运行？访问 http://localhost:8000/api/health
2. 防火墙是否阻止了端口 8000？

### 问题 3: 索引未加载
```
向量索引未加载，请先重建索引
```

**解决方案**：
在前端界面点击"重建向量库"按钮，等待 1-2 分钟。

### 问题 4: LLM 调用失败
```
API Key 错误或余额不足
```

**检查**：
1. `.env` 文件中的 API Key 是否正确
2. API Key 是否有余额
3. 网络是否能访问 LLM 服务

---

## 🎨 界面预览

### 主界面布局
```
┌─────────────────────────────────────────────────────┐
│  🚀 RAG 需求解析与测试用例生成系统                          │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│  系统设置  │  需求输入区                               │
│          │  ┌────────────────────────────────────┐ │
│  ✓ 健康检查│  │ 输入需求文本...                    │ │
│  ✓ 重建索引│  └────────────────────────────────────┘ │
│          │  [生成原子需求 + 测试用例] [导出 Excel]   │
│  LLM 配置 │                                          │
│  ├ 提供商  │  结果展示区                               │
│  ├ 模型    │  ┌────────────────────────────────────┐ │
│  └ 参数    │  │ 📘 领域术语解释                    │ │
│          │  │ 💡 原子需求                        │ │
│          │  │ 🧪 测试用例                        │ │
│          │  └────────────────────────────────────┘ │
└──────────┴──────────────────────────────────────────┘
```

---

## 🎯 使用示例

### 示例需求
```
需求编号：REQ-LG-001
功能描述：起落架控制逻辑。
具体规约：当且仅当起落架控制手柄（Gear Handle）处于"DOWN"位置，
且飞行速度（Airspeed）低于 250 节时，起落架执行机构应在 3 秒内
接收到"放下（Deploy）"指令。若速度超过 250 节，即使手柄在"DOWN"位，
也不允许执行放下动作，并需触发告警。
```

### 预期输出
1. **领域术语**：Gear Handle、Airspeed 等术语定义
2. **原子需求**：3-5 个可验证的原子需求
3. **测试用例**：每个原子需求对应 1-2 个 IEEE 829 测试用例

---

## 📊 性能指标

| 操作 | 预期时间 |
|------|---------|
| 后端启动 | ~5 秒 |
| 前端启动 | ~3 秒 |
| 索引构建 | 1-2 分钟 |
| 需求分析 | 10-30 秒 |
| Excel 导出 | 2-5 秒 |

---

## 🔧 高级配置

### 自定义端口

**后端**（修改 `backend/main.py`）：
```python
uvicorn.run("main:app", host="0.0.0.0", port=9000)
```

**前端**（修改 `frontend/vite.config.js`）：
```javascript
server: {
  port: 3000,
  proxy: {
    '/api': 'http://localhost:9000'
  }
}
```

### 调整检索参数

在前端界面左侧面板：
- **Top-K**: 2-8（推荐 3-5）
- **Window**: 2-8（推荐 4-6）

---

## 📞 获取帮助

### 文档
- [QUICKSTART.md](QUICKSTART.md) - 快速上手
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 迁移指南
- [README.md](README.md) - 完整文档

### API 文档
- http://localhost:8000/docs - Swagger UI
- http://localhost:8000/redoc - ReDoc

### 问题反馈
如果遇到问题，请提供：
1. 错误信息截图
2. 浏览器控制台日志
3. 后端终端输出
4. 操作步骤

---

## 🎉 准备好了吗？

运行验证脚本开始：

```bash
python check_installation.py
```

如果所有检查通过，执行：

```bash
start_backend.bat   # 终端 1
start_frontend.bat  # 终端 2
```

然后访问：http://localhost:5173

**祝使用愉快！** 🚀
