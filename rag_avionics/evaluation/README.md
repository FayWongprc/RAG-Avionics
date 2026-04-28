# 评估与验证模块

本模块提供对 RAG 系统生成的测试用例 Excel 文件进行四个维度的自动化评估。

## 📋 评估维度

### 1. 需求覆盖完整度评估 (纯逻辑计算)

**目标**: 确保所有需求都被测试用例覆盖

**评估方法**:
- 提取 `AtomicRequirements` 表中的所有需求 ID
- 提取 `TestCases` 表中关联的需求 ID
- 进行集合比对，计算覆盖率
- 输出未被任何测试用例覆盖的孤立需求列表

**输出指标**:
- `total_requirements`: 总需求数
- `covered_requirements`: 已覆盖需求数
- `coverage_rate`: 覆盖率 (0-1)
- `uncovered_requirements`: 未覆盖需求 ID 列表

### 2. 用例结构规范性评估 (纯逻辑计算)

**目标**: 检查测试用例的结构完整性

**评估方法**:
- 遍历 `TestCases` 表
- 检查核心字段是否存在空值 (NaN/空字符串)
  - `tc_id`: 测试用例 ID
  - `title`: 标题
  - `objective`: 测试目的
  - `test_method`: 测试方法
  - `preconditions`: 前提条件
  - `inputs`: 输入
  - `steps`: 测试步骤
  - `expected_results`: 预期结果
  - `trace_to_atomic_req`: 追溯到的原子需求
- 计算结构合格率

**输出指标**:
- `total_test_cases`: 总测试用例数
- `valid_test_cases`: 结构完整的用例数
- `structure_compliance_rate`: 结构合格率 (0-1)
- `invalid_test_cases`: 结构不完整的用例详情列表

### 3. 测试方法与逻辑合理性评估 (静态分组 + 大模型盲评)

**目标**: 评估测试方法的完整性和合理性

**评估方法**:

**第一步 - 静态基线检查**:
- 按 `trace_to_atomic_req` 对测试用例分组
- 检查每个需求组是否至少包含:
  - 一个"正常范围"测试 (关键词: 正常、正常范围、nominal)
  - 一个"健壮性测试"或"异常测试" (关键词: 健壮、异常、边界、robustness、boundary、exception)
- 找出未覆盖异常工况的需求

**第二步 - 大模型盲评** (可选):
- 遍历每个测试用例
- 将测试方法标签、测试步骤、预期结果拼装成 Prompt
- 调用 `call_llm_judge()` 函数
- 要求大模型评估"该用例的步骤是否真正符合它声明的测试方法"
- 返回 1-5 分的评分

**输出指标**:
- `total_requirements`: 总需求数
- `requirements_with_normal_test`: 包含正常测试的需求数
- `requirements_with_robustness_test`: 包含健壮性测试的需求数
- `requirements_with_both`: 同时包含两者的需求数
- `method_coverage_rate`: 方法覆盖率 (0-1)
- `requirements_missing_robustness`: 缺少健壮性测试的需求列表
- `llm_scores`: LLM 评分详情列表 (如果启用)
- `average_llm_score`: LLM 平均分 (1-5)

### 4. 追溯链路与证据完整性评估 (图校验与统计)

**目标**: 验证追溯关系的完整性和证据的有效性

**评估方法**:

**连通性与合法性校验**:
- 检查 `TraceabilityMatrix` 表中的上下游引用 ID
- 验证 `atomic_req_id` 是否存在于 `AtomicRequirements` 表
- 验证 `tc_id` 是否存在于 `TestCases` 表
- 找出"断链"或"凭空捏造、不存在的 ID"

**证据率统计**:
- 统计 `TestCases` 表中 `evidence_refs` 列非空的比例
- 证明 RAG 检索的有效性

**输出指标**:
- `total_traceability_links`: 总追溯链路数
- `valid_links`: 有效链路数
- `broken_links`: 断链数
- `link_validity_rate`: 链路有效率 (0-1)
- `broken_link_details`: 断链详情列表
- `total_test_cases`: 总测试用例数
- `test_cases_with_evidence`: 包含证据引用的用例数
- `evidence_rate`: 证据引用率 (0-1)

## 🚀 使用方法

### 基本用法

```python
from rag_avionics.evaluation import evaluate_excel

# 从字节流评估
with open("output/traceability_report.xlsx", "rb") as f:
    excel_bytes = f.read()

result = evaluate_excel(excel_bytes, enable_llm=False)

# 访问评估结果
print(f"需求覆盖率: {result.coverage.coverage_rate * 100:.2f}%")
print(f"结构合格率: {result.structure.structure_compliance_rate * 100:.2f}%")
print(f"方法覆盖率: {result.logic.method_coverage_rate * 100:.2f}%")
print(f"链路有效率: {result.traceability.link_validity_rate * 100:.2f}%")
```

### 从文件路径评估

```python
from rag_avionics.evaluation import evaluate_from_file

result = evaluate_from_file("output/traceability_report.xlsx", enable_llm=False)
```

### 启用 LLM 盲评

```python
result = evaluate_excel(excel_bytes, enable_llm=True)

# 查看 LLM 评分
for score_info in result.logic.llm_scores:
    print(f"{score_info['tc_id']}: {score_info['score']}/5 - {score_info['reasoning']}")
```

### 导出为 JSON

```python
import json

result_dict = result.to_dict()

with open("evaluation_result.json", "w", encoding="utf-8") as f:
    json.dump(result_dict, f, ensure_ascii=False, indent=2)
```

### 运行示例脚本

```bash
python -m rag_avionics.evaluation.example_usage
```

## 🔧 集成到后端 API

在 `backend/main.py` 中添加评估端点:

```python
from rag_avionics.evaluation import evaluate_excel

@app.post("/api/evaluate")
async def evaluate_report(file: UploadFile = File(...)):
    """评估上传的 Excel 文件"""
    excel_bytes = await file.read()
    result = evaluate_excel(excel_bytes, enable_llm=False)
    return result.to_dict()
```

## 📊 前端展示建议

### 仪表盘布局

```
┌─────────────────────────────────────────────────────┐
│  评估总览                                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐│
│  │需求覆盖率│ │结构合格率│ │方法覆盖率│ │链路有效率││
│  │  95.2%   │ │  98.5%   │ │  87.3%   │ │  100%    ││
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘│
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  详细问题列表                                        │
│  ⚠️  未覆盖的需求 (3个)                              │
│    - AR-001: 系统启动时序要求                        │
│    - AR-015: 故障检测逻辑                            │
│    - AR-023: 数据完整性校验                          │
│                                                      │
│  ⚠️  结构不完整的用例 (2个)                          │
│    - TC-001: 缺失字段 [steps, expected_results]     │
│    - TC-007: 缺失字段 [preconditions]               │
└─────────────────────────────────────────────────────┘
```

### 可视化组件

1. **环形进度图**: 显示四个维度的评分
2. **柱状图**: 对比正常测试 vs 健壮性测试的覆盖情况
3. **表格**: 展示详细的问题列表，支持筛选和排序
4. **趋势图**: 如果有历史数据，显示评估指标的变化趋势

## 🔌 自定义 LLM 评分函数

默认的 `call_llm_judge()` 是一个模拟实现。要集成真实的 LLM:

```python
from rag_avionics.llm import make_llm
from langchain_core.messages import HumanMessage

def call_llm_judge(prompt: str) -> dict:
    """使用真实 LLM 进行评分"""
    llm = make_llm(temperature=0.3)
    
    # 添加评分指令
    full_prompt = f"""{prompt}

请以 JSON 格式返回评分结果:
{{
  "score": 1-5的整数,
  "reasoning": "简短的评分理由"
}}
"""
    
    response = llm.invoke([HumanMessage(content=full_prompt)])
    result_text = getattr(response, "content", str(response))
    
    # 解析 JSON
    import json
    result = json.loads(result_text)
    
    return result
```

然后在 `evaluator.py` 中替换默认实现。

## 📝 注意事项

1. **性能考虑**: LLM 盲评会显著增加评估时间，建议在后台异步执行
2. **阈值调整**: 可以根据项目需求调整各维度的合格标准
3. **扩展性**: 可以轻松添加新的评估维度，只需实现新的评估函数
4. **数据质量**: 评估结果的准确性依赖于 Excel 文件的数据质量

## 🧪 测试

```bash
# 运行单元测试
pytest rag_avionics/evaluation/tests/

# 运行示例评估
python -m rag_avionics.evaluation.example_usage
```

## 📚 相关文档

- [RAG Pipeline 说明](../README.md)
- [Excel 导出格式](../export_excel.py)
- [数据模型定义](../schemas.py)
