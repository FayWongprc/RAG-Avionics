# 前端集成指南

本文档说明如何在前端调用评估 API 并展示结果。

## API 端点

### 1. 评估分析结果

**端点**: `POST /api/evaluate`

**请求参数**:
```typescript
interface EvaluateRequest {
  result: any;              // 分析结果（与 export-excel-direct 相同格式）
  enable_llm: boolean;      // 是否启用 LLM 盲评
  llm_provider?: string;    // LLM 提供商（qwen/deepseek/zhipu）
  llm_model?: string;       // 具体模型名称
}
```

**响应格式**:
```typescript
interface EvaluationResult {
  coverage: {
    total_requirements: number;
    covered_requirements: number;
    coverage_rate: number;              // 0-1
    uncovered_requirements: string[];   // 未覆盖的需求 ID 列表
  };
  
  structure: {
    total_test_cases: number;
    valid_test_cases: number;
    structure_compliance_rate: number;  // 0-1
    invalid_test_cases: Array<{
      tc_id: string;
      missing_fields: string[];
    }>;
  };
  
  logic: {
    total_requirements: number;
    requirements_with_normal_test: number;
    requirements_with_robustness_test: number;
    requirements_with_both: number;
    method_coverage_rate: number;       // 0-1
    requirements_missing_robustness: string[];
    llm_scores: Array<{
      tc_id: string;
      score: number;                    // 1-5
      reasoning: string;
      issues: string[];                 // 具体问题列表
    }>;
    average_llm_score: number;          // 1-5
  };
  
  traceability: {
    total_traceability_links: number;
    valid_links: number;
    broken_links: number;
    link_validity_rate: number;         // 0-1
    broken_link_details: Array<{
      row_index: number;
      atomic_req_id: string;
      tc_id: string;
      issues: string[];
    }>;
    total_test_cases: number;
    test_cases_with_evidence: number;
    evidence_rate: number;              // 0-1
  };
}
```

## 前端调用示例

### React/TypeScript 示例

```typescript
import { useState } from 'react';

interface EvaluationState {
  loading: boolean;
  result: EvaluationResult | null;
  error: string | null;
}

function EvaluationPanel({ analysisResult }: { analysisResult: any }) {
  const [evaluation, setEvaluation] = useState<EvaluationState>({
    loading: false,
    result: null,
    error: null,
  });
  
  const [enableLLM, setEnableLLM] = useState(false);
  const [llmProvider, setLLMProvider] = useState('qwen');
  const [llmModel, setLLMModel] = useState('qwen3-max');

  const handleEvaluate = async () => {
    setEvaluation({ loading: true, result: null, error: null });
    
    try {
      const response = await fetch('http://localhost:8000/api/evaluate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          result: analysisResult,
          enable_llm: enableLLM,
          llm_provider: llmProvider,
          llm_model: llmModel,
        }),
      });
      
      if (!response.ok) {
        throw new Error(`评估失败: ${response.statusText}`);
      }
      
      const data = await response.json();
      setEvaluation({ loading: false, result: data, error: null });
    } catch (error) {
      setEvaluation({
        loading: false,
        result: null,
        error: error.message,
      });
    }
  };

  return (
    <div className="evaluation-panel">
      <h2>质量评估</h2>
      
      {/* 配置选项 */}
      <div className="config">
        <label>
          <input
            type="checkbox"
            checked={enableLLM}
            onChange={(e) => setEnableLLM(e.target.checked)}
          />
          启用 LLM 盲评（评估维度3）
        </label>
        
        {enableLLM && (
          <>
            <select
              value={llmProvider}
              onChange={(e) => setLLMProvider(e.target.value)}
            >
              <option value="qwen">千问</option>
              <option value="deepseek">DeepSeek</option>
              <option value="zhipu">智谱</option>
            </select>
            
            <input
              type="text"
              value={llmModel}
              onChange={(e) => setLLMModel(e.target.value)}
              placeholder="模型名称"
            />
          </>
        )}
      </div>
      
      <button onClick={handleEvaluate} disabled={evaluation.loading}>
        {evaluation.loading ? '评估中...' : '开始评估'}
      </button>
      
      {/* 显示结果 */}
      {evaluation.result && (
        <EvaluationResults result={evaluation.result} />
      )}
      
      {evaluation.error && (
        <div className="error">{evaluation.error}</div>
      )}
    </div>
  );
}
```

### 结果展示组件

```typescript
function EvaluationResults({ result }: { result: EvaluationResult }) {
  return (
    <div className="evaluation-results">
      {/* 总览卡片 */}
      <div className="overview">
        <MetricCard
          title="需求覆盖率"
          value={result.coverage.coverage_rate}
          format="percentage"
        />
        <MetricCard
          title="结构合格率"
          value={result.structure.structure_compliance_rate}
          format="percentage"
        />
        <MetricCard
          title="方法覆盖率"
          value={result.logic.method_coverage_rate}
          format="percentage"
        />
        <MetricCard
          title="链路有效率"
          value={result.traceability.link_validity_rate}
          format="percentage"
        />
      </div>
      
      {/* 详细问题列表 */}
      <div className="details">
        {/* 维度1：需求覆盖 */}
        {result.coverage.uncovered_requirements.length > 0 && (
          <IssueSection
            title="未覆盖的需求"
            items={result.coverage.uncovered_requirements}
          />
        )}
        
        {/* 维度2：结构规范 */}
        {result.structure.invalid_test_cases.length > 0 && (
          <IssueSection
            title="结构不完整的用例"
            items={result.structure.invalid_test_cases.map(tc => ({
              id: tc.tc_id,
              description: `缺失字段: ${tc.missing_fields.join(', ')}`,
            }))}
          />
        )}
        
        {/* 维度3：LLM 评分 */}
        {result.logic.llm_scores.length > 0 && (
          <LLMScoresSection scores={result.logic.llm_scores} />
        )}
        
        {/* 维度4：追溯链路 */}
        {result.traceability.broken_link_details.length > 0 && (
          <IssueSection
            title="断链详情"
            items={result.traceability.broken_link_details.map(link => ({
              id: `行 ${link.row_index}`,
              description: link.issues.join(', '),
            }))}
          />
        )}
      </div>
    </div>
  );
}

function LLMScoresSection({ scores }: { scores: Array<any> }) {
  // 按分数排序，低分在前
  const sortedScores = [...scores].sort((a, b) => a.score - b.score);
  
  return (
    <div className="llm-scores">
      <h3>🤖 LLM 逻辑合理性评分</h3>
      <p>平均分: {(scores.reduce((sum, s) => sum + s.score, 0) / scores.length).toFixed(2)} / 5.0</p>
      
      <table>
        <thead>
          <tr>
            <th>用例ID</th>
            <th>评分</th>
            <th>评分理由</th>
            <th>具体问题</th>
          </tr>
        </thead>
        <tbody>
          {sortedScores.map(score => (
            <tr key={score.tc_id} className={`score-${score.score}`}>
              <td>{score.tc_id}</td>
              <td>
                <span className="score-badge">{score.score}/5</span>
              </td>
              <td>{score.reasoning}</td>
              <td>
                {score.issues.length > 0 ? (
                  <ul>
                    {score.issues.map((issue, idx) => (
                      <li key={idx}>{issue}</li>
                    ))}
                  </ul>
                ) : (
                  <span className="no-issues">无问题</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
```

### CSS 样式建议

```css
/* 评分徽章 */
.score-badge {
  display: inline-block;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
}

.score-5 .score-badge {
  background-color: #10b981;
  color: white;
}

.score-4 .score-badge {
  background-color: #3b82f6;
  color: white;
}

.score-3 .score-badge {
  background-color: #f59e0b;
  color: white;
}

.score-2 .score-badge {
  background-color: #ef4444;
  color: white;
}

.score-1 .score-badge {
  background-color: #991b1b;
  color: white;
}

/* 问题列表 */
.llm-scores ul {
  margin: 0;
  padding-left: 20px;
}

.llm-scores li {
  color: #dc2626;
  margin: 4px 0;
}

.no-issues {
  color: #10b981;
  font-style: italic;
}
```

## 性能优化建议

### 1. 异步评估

LLM 盲评可能需要较长时间（每个用例 1-3 秒），建议：

```typescript
// 先显示静态评估结果
const quickEvaluation = await fetch('/api/evaluate', {
  method: 'POST',
  body: JSON.stringify({ result, enable_llm: false }),
});

// 如果用户选择启用 LLM，再进行深度评估
if (userWantsLLMEvaluation) {
  const deepEvaluation = await fetch('/api/evaluate', {
    method: 'POST',
    body: JSON.stringify({ result, enable_llm: true }),
  });
}
```

### 2. 进度提示

```typescript
// 使用 Server-Sent Events 或 WebSocket 实时显示进度
const eventSource = new EventSource('/api/evaluate-stream');
eventSource.onmessage = (event) => {
  const progress = JSON.parse(event.data);
  setProgress(`正在评估: ${progress.current}/${progress.total}`);
};
```

### 3. 缓存结果

```typescript
// 缓存评估结果，避免重复评估
const cacheKey = `eval_${analysisResult.requirement_id}`;
const cached = localStorage.getItem(cacheKey);
if (cached) {
  return JSON.parse(cached);
}
```

## 错误处理

```typescript
try {
  const response = await fetch('/api/evaluate', { ... });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || '评估失败');
  }
  
  const result = await response.json();
  return result;
} catch (error) {
  if (error.message.includes('timeout')) {
    // 超时处理
    showNotification('评估超时，请稍后重试');
  } else if (error.message.includes('LLM')) {
    // LLM 相关错误
    showNotification('LLM 调用失败，请检查配置');
  } else {
    // 其他错误
    showNotification(`评估失败: ${error.message}`);
  }
}
```

## 完整的前端流程

```
1. 用户输入需求 → 调用 /api/analyze
2. 显示分析结果（原子需求、测试用例）
3. 用户点击"导出 Excel" → 调用 /api/export-excel-direct
4. 用户点击"质量评估" → 调用 /api/evaluate
   - 选择是否启用 LLM 盲评
   - 选择 LLM 提供商和模型
5. 显示评估结果
   - 四个维度的评分卡片
   - 详细问题列表
   - LLM 评分详情（如果启用）
6. 用户可以根据评估结果优化需求或测试用例
```
