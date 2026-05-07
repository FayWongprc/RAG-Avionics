# 🚀 基于RAG的机载软件需求自动解析与测试用例生成系统

> **FastAPI + React** | 前后端分离 | 智能质量评估

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg)](https://react.dev/)

基于航空标准（DO-178C、ARP4754A、IEEE 829）的智能需求分析与测试用例生成系统。

## ✨ 核心功能

- 🔍 **需求原子化分解** - 将复杂需求拆解为可验证的原子需求
- 📚 **RAG 证据检索** - 双路检索：标准文档 + SRD
- 📝 **测试用例生成** - 自动生成符合 IEEE 829 标准的测试用例
- 📊 **四维质量评估** - LLM-as-a-Judge 深度评估（需求覆盖、结构规范、逻辑合理性、追溯完整性）
- 📄 **Excel 导出** - 一键导出完整追溯矩阵

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+
- 至少一个 LLM API Key（千问/DeepSeek/智谱）

### 安装步骤

```bash
# 1. 克隆项目
git clone https://github.com/FayWongprc/RAG-Avionics.git
cd RAG-Avionics

# 2. 创建并激活虚拟环境
python -m venv rag_venv
rag_venv\Scripts\activate  # Windows
# source rag_venv/bin/activate  # Linux/Mac

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 安装前端依赖
cd frontend
npm install
cd ..

# 5. 配置 API Key
 .env  # 在该文件填写你的 API Key
```

### 启动服务

```bash
# 启动后端
python backend/main.py

# 在另一个终端启动前端
cd frontend
npm run dev
```

### 访问系统

- **前端界面**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs

### 首次使用

1. 打开 http://localhost:5173
2. 点击"重建向量索引"（首次必须，约 1-2 分钟）
3. 输入需求文本，点击"开始分析"
4. 查看原子需求、测试用例、质量评估
5. 导出 Excel 报告

---

## ⚠️ 重要提示

### 首次启动会自动下载嵌入模型

- **模型**: BAAI/bge-m3（约 2.3GB）
- **下载时间**: 5-10 分钟
- **存储位置**: `~/.cache/huggingface/hub/`
- **只需下载一次**，后续启动直接使用缓存

### 两个命令行窗口必须同时运行

- 后端窗口：运行 FastAPI 服务
- 前端窗口：运行 React 开发服务器
- **不要关闭这两个窗口**

---

## 📁 项目结构

```
RAG-Avionics/
├── backend/                    # FastAPI 后端
│   └── main.py                # API 入口
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── components/        # 标签页组件
│   │   └── App.jsx            # 主应用
│   └── package.json
├── rag_avionics/              # 核心业务逻辑
│   ├── evaluation/            # 质量评估模块
│   ├── pipeline.py            # RAG 流程
│   └── indexing.py            # 向量索引
├── data/                      # 知识库
│   ├── Avionics_standards/    # 标准文档
│   ├── Avionics_srd/          # SRD 文档
│   └── avionics_terms.json    # 术语词典
└── storage/                   # 向量数据库
```

---

## 🔧 技术栈

**后端**: FastAPI + LlamaIndex + LangGraph + Qdrant + HuggingFace  
**前端**: React 18 + Vite + Tailwind CSS + Axios  
**LLM**: 阿里千问 / DeepSeek / 智谱AI

---

## 🎯 使用流程

```
① 需求输入 → ② 原子需求 → ③ 测试用例 → ④ 质量评估 → ⑤ 导出报告
```

1. **需求输入**: 配置 LLM 参数，输入需求文本
2. **原子需求**: 查看分解结果、术语解释、检索证据
3. **测试用例**: 查看生成的测试用例（支持过滤）
4. **质量评估**: 四维度评估，LLM 深度打分
5. **导出报告**: 下载 Excel 追溯矩阵

---

## 🐛 常见问题

### Q1: 后端启动失败，提示 Qdrant 锁文件冲突
```bash
# 删除锁文件
del storage\qdrant\.lock  # Windows
# rm storage/qdrant/.lock  # Linux/Mac
```

### Q2: 虚拟环境激活失败
```bash
# Windows 可能需要执行
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q3: pip install 失败
```bash
# 使用国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q4: npm install 失败
```bash
# 使用国内镜像
npm install --registry=https://registry.npmmirror.com
```

### Q5: 嵌入模型下载失败
- 检查网络连接
- 重新启动后端会继续下载
- 手动下载：https://huggingface.co/BAAI/bge-m3

### Q6: 前端无法连接后端
- 确保后端已启动（http://localhost:8000）
- 检查防火墙设置
- 查看浏览器控制台错误信息

---

## 📚 详细文档

- [前端详细文档](frontend/FRONTEND_V2_README.md)
- [评估模块文档](rag_avionics/evaluation/README.md)
- [双分块策略说明](双分块策略说明.md)
- [双路检索说明](双路检索说明.md)

---

## 📊 核心特性

### 1. 四维质量评估（LLM-as-a-Judge）

- **维度1**: 需求覆盖完整度
- **维度2**: 用例结构规范性
- **维度3**: 测试方法与逻辑合理性（LLM 评分 1-5 分）
- **维度4**: 追溯链路与证据完整性

### 2. 双路检索策略

- **标准文档专线**: 强制检索 DO-178C、ARP4754A 等标准
- **SRD 文档专线**: 强制检索软件需求文档
- 确保两类证据都被获取

### 3. 状态持久化

- LocalStorage 自动保存
- 刷新页面不丢失数据
- 支持断点续传

---


---

## 🙏 致谢

[LlamaIndex](https://www.llamaindex.ai/) | [FastAPI](https://fastapi.tiangolo.com/) | [React](https://react.dev/) | [Qdrant](https://qdrant.tech/) | [Tailwind CSS](https://tailwindcss.com/)

---

**项目地址**: https://github.com/FayWongprc/RAG-Avionics  
**有问题？** 查看 [详细文档](frontend/FRONTEND_V2_README.md) 或提交 Issue
