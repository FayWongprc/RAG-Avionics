import { useState, useEffect } from 'react'
import { BarChart3, Loader2, AlertCircle, CheckCircle2, XCircle, TrendingUp } from 'lucide-react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

export default function EvaluationTab({ result, llmProvider, llmModel }) {
  const [evaluation, setEvaluation] = useState(() => {
    const saved = localStorage.getItem('evaluationResult')
    return saved ? JSON.parse(saved) : null
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // 保存评估结果到 localStorage
  useEffect(() => {
    if (evaluation) {
      localStorage.setItem('evaluationResult', JSON.stringify(evaluation))
    } else {
      localStorage.removeItem('evaluationResult')
    }
  }, [evaluation])

  const runEvaluation = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // 确保数据格式正确：将 req_id 映射为 atomic_req_id（如果需要）
      const formattedResult = {
        ...result,
        atomic_requirements: result.atomic_requirements?.map(ar => ({
          ...ar,
          atomic_req_id: ar.req_id || ar.atomic_req_id,  // 兼容两种格式
        })) || []
      }
      
      console.log('发送评估请求，数据:', {
        atomic_requirements_count: formattedResult.atomic_requirements.length,
        test_cases_count: formattedResult.test_cases?.length || 0,
        sample_atomic_req: formattedResult.atomic_requirements[0]
      })
      
      const res = await axios.post(`${API_BASE}/api/evaluate`, {
        result: formattedResult,
        enable_llm: true,  // 默认启用 LLM 评估
        llm_provider: llmProvider,
        llm_model: llmModel
      })
      setEvaluation(res.data)
    } catch (err) {
      console.error('评估失败:', err)
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (rate) => {
    if (rate >= 0.9) return 'text-green-600'
    if (rate >= 0.7) return 'text-blue-600'
    if (rate >= 0.5) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getScoreBgColor = (rate) => {
    if (rate >= 0.9) return 'bg-green-50 border-green-200'
    if (rate >= 0.7) return 'bg-blue-50 border-blue-200'
    if (rate >= 0.5) return 'bg-yellow-50 border-yellow-200'
    return 'bg-red-50 border-red-200'
  }

  const getLLMScoreColor = (score) => {
    if (score >= 4.5) return 'bg-green-100 text-green-800'
    if (score >= 3.5) return 'bg-blue-100 text-blue-800'
    if (score >= 2.5) return 'bg-yellow-100 text-yellow-800'
    return 'bg-red-100 text-red-800'
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* 评估控制面板 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">质量评估</h2>
        
        <div className="space-y-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm">
            <div className="font-medium text-blue-900 mb-2">📊 评估维度</div>
            <ul className="text-blue-800 space-y-1 ml-4">
              <li>• <strong>维度1</strong>：需求覆盖完整度 - 检查所有原子需求是否都被测试用例覆盖</li>
              <li>• <strong>维度2</strong>：用例结构规范性 - 检查测试用例的核心字段是否完整</li>
              <li>• <strong>维度3</strong>：测试方法与逻辑合理性 - 检查每个测试用例的质量并给出优化建议（引入大模型裁判-LLM-as-a-Judge）</li>
              <li>• <strong>维度4</strong>：追溯链路与证据完整性 - 检查追溯矩阵和证据引用的完整性</li>
            </ul>
          </div>

          <button
            onClick={runEvaluation}
            disabled={loading}
            className="w-full px-6 py-3 bg-gradient-to-r from-purple-500 to-indigo-600 text-white rounded-lg hover:from-purple-600 hover:to-indigo-700 transition disabled:opacity-50 flex items-center justify-center gap-2 font-medium shadow-lg"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                评估中...
              </>
            ) : (
              <>
                <BarChart3 className="w-5 h-5" />
                开始质量评估
              </>
            )}
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div>
            <h3 className="font-medium text-red-800">评估失败</h3>
            <p className="text-red-600 text-sm mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* 评估结果 */}
      {evaluation && (
        <div className="space-y-6">
          {/* 总览卡片 */}
          <div className="bg-gradient-to-r from-purple-50 to-indigo-50 rounded-xl border border-purple-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 评估总览</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className={`bg-white rounded-lg p-4 text-center border-2 ${getScoreBgColor(evaluation.coverage.coverage_rate)}`}>
                <div className={`text-3xl font-bold ${getScoreColor(evaluation.coverage.coverage_rate)}`}>
                  {(evaluation.coverage.coverage_rate * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600 mt-1">需求覆盖率</div>
                <div className="text-xs text-gray-500 mt-1">维度1</div>
              </div>
              <div className={`bg-white rounded-lg p-4 text-center border-2 ${getScoreBgColor(evaluation.structure.structure_compliance_rate)}`}>
                <div className={`text-3xl font-bold ${getScoreColor(evaluation.structure.structure_compliance_rate)}`}>
                  {(evaluation.structure.structure_compliance_rate * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600 mt-1">结构合格率</div>
                <div className="text-xs text-gray-500 mt-1">维度2</div>
              </div>
              <div className={`bg-white rounded-lg p-4 text-center border-2 ${
                evaluation.logic.average_llm_score >= 4.5 ? 'bg-green-50 border-green-200' :
                evaluation.logic.average_llm_score >= 3.5 ? 'bg-blue-50 border-blue-200' :
                evaluation.logic.average_llm_score >= 2.5 ? 'bg-yellow-50 border-yellow-200' :
                'bg-red-50 border-red-200'
              }`}>
                <div className={`text-3xl font-bold ${
                  evaluation.logic.average_llm_score >= 4.5 ? 'text-green-600' :
                  evaluation.logic.average_llm_score >= 3.5 ? 'text-blue-600' :
                  evaluation.logic.average_llm_score >= 2.5 ? 'text-yellow-600' :
                  'text-red-600'
                }`}>
                  {evaluation.logic.average_llm_score.toFixed(2)}/5
                </div>
                <div className="text-sm text-gray-600 mt-1">逻辑合理性</div>
                <div className="text-xs text-gray-500 mt-1">维度3</div>
              </div>
              <div className={`bg-white rounded-lg p-4 text-center border-2 ${getScoreBgColor(evaluation.traceability.link_validity_rate)}`}>
                <div className={`text-3xl font-bold ${getScoreColor(evaluation.traceability.link_validity_rate)}`}>
                  {(evaluation.traceability.link_validity_rate * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600 mt-1">链路有效率</div>
                <div className="text-xs text-gray-500 mt-1">维度4</div>
              </div>
            </div>
          </div>

          {/* 维度1：需求覆盖完整度 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">📋 维度1：需求覆盖完整度</h3>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-600">总需求数</div>
                <div className="text-2xl font-bold text-gray-900">{evaluation.coverage.total_requirements}</div>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <div className="text-sm text-gray-600">已覆盖</div>
                <div className="text-2xl font-bold text-green-600">{evaluation.coverage.covered_requirements}</div>
              </div>
              <div className="bg-red-50 rounded-lg p-3">
                <div className="text-sm text-gray-600">未覆盖</div>
                <div className="text-2xl font-bold text-red-600">
                  {evaluation.coverage.uncovered_requirements.length}
                </div>
              </div>
            </div>

            {evaluation.coverage.uncovered_requirements.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="font-medium text-red-900 mb-2 flex items-center gap-2">
                  <XCircle className="w-4 h-4" />
                  未覆盖的需求
                </div>
                <div className="flex flex-wrap gap-2">
                  {evaluation.coverage.uncovered_requirements.map((reqId, idx) => (
                    <span key={idx} className="px-2 py-1 bg-red-100 text-red-800 text-sm rounded font-mono">
                      {reqId}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {evaluation.coverage.uncovered_requirements.length === 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-green-800 font-medium">✅ 所有需求都已被测试用例覆盖</span>
              </div>
            )}
          </div>

          {/* 维度2：用例结构规范性 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">📝 维度2：用例结构规范性</h3>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-600">总用例数</div>
                <div className="text-2xl font-bold text-gray-900">{evaluation.structure.total_test_cases}</div>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <div className="text-sm text-gray-600">结构完整</div>
                <div className="text-2xl font-bold text-green-600">{evaluation.structure.valid_test_cases}</div>
              </div>
              <div className="bg-red-50 rounded-lg p-3">
                <div className="text-sm text-gray-600">结构不完整</div>
                <div className="text-2xl font-bold text-red-600">
                  {evaluation.structure.invalid_test_cases.length}
                </div>
              </div>
            </div>

            {evaluation.structure.invalid_test_cases.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="font-medium text-red-900 mb-3 flex items-center gap-2">
                  <XCircle className="w-4 h-4" />
                  结构不完整的用例
                </div>
                <div className="space-y-2">
                  {evaluation.structure.invalid_test_cases.map((tc, idx) => (
                    <div key={idx} className="bg-white rounded p-3 border border-red-200">
                      <div className="font-mono font-semibold text-red-800 mb-1">{tc.tc_id}</div>
                      <div className="text-sm text-red-700">
                        缺失字段: {tc.missing_fields.join(', ')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {evaluation.structure.invalid_test_cases.length === 0 && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-2">
                <CheckCircle2 className="w-5 h-5 text-green-600" />
                <span className="text-green-800 font-medium">✅ 所有测试用例结构完整</span>
              </div>
            )}
          </div>

          {/* 维度3：测试方法与逻辑合理性 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">🧪 维度3：测试方法与逻辑合理性</h3>
            
            {/* 测试方法覆盖分析 */}
            <div>
              <h4 className="font-semibold text-gray-700 mb-3">测试方法覆盖统计</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm text-gray-600">总需求数</div>
                  <div className="text-2xl font-bold text-gray-900">{evaluation.logic.total_requirements}</div>
                </div>
                <div className="bg-blue-50 rounded-lg p-3">
                  <div className="text-sm text-gray-600">含正常测试</div>
                  <div className="text-2xl font-bold text-blue-600">{evaluation.logic.requirements_with_normal_test}</div>
                </div>
                <div className="bg-purple-50 rounded-lg p-3">
                  <div className="text-sm text-gray-600">含健壮性测试</div>
                  <div className="text-2xl font-bold text-purple-600">{evaluation.logic.requirements_with_robustness_test}</div>
                </div>
                <div className="bg-green-50 rounded-lg p-3">
                  <div className="text-sm text-gray-600">同时包含两者</div>
                  <div className="text-2xl font-bold text-green-600">{evaluation.logic.requirements_with_both}</div>
                </div>
              </div>

              {/* 缺少健壮性测试的需求 */}
              {evaluation.logic.requirements_missing_robustness.length > 0 ? (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <div className="font-medium text-yellow-900 mb-2 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    缺少健壮性测试的需求 ({evaluation.logic.requirements_missing_robustness.length})
                  </div>
                  <div className="text-sm text-yellow-800 mb-3">
                    以下需求只有正常测试，建议补充边界值、异常情况等健壮性测试用例：
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {evaluation.logic.requirements_missing_robustness.map((reqId, idx) => (
                      <span key={idx} className="px-2 py-1 bg-yellow-100 text-yellow-800 text-sm rounded font-mono">
                        {reqId}
                      </span>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                  <span className="text-green-800 font-medium">✅ 所有需求都包含正常测试和健壮性测试</span>
                </div>
              )}

              {/* LLM 逻辑合理性评分 */}
              {evaluation.logic.llm_scores && evaluation.logic.llm_scores.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    测试用例逻辑合理性评分（LLM-as-a-Judge）
                  </h4>
                  <div className="bg-blue-50 rounded-lg p-4 mb-4">
                    <div className="text-center">
                      <div className="text-4xl font-bold text-blue-600">{evaluation.logic.average_llm_score.toFixed(2)}</div>
                      <div className="text-sm text-gray-600 mt-1">平均分 / 5.0</div>
                    </div>
                  </div>

                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {evaluation.logic.llm_scores
                      .sort((a, b) => a.score - b.score)
                      .map((score, idx) => (
                      <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-mono font-semibold text-gray-900">{score.tc_id}</span>
                          <span className={`px-3 py-1 rounded-full text-sm font-bold ${getLLMScoreColor(score.score)}`}>
                            {score.score}/5
                          </span>
                        </div>
                        <div className="text-sm text-gray-700 mb-2">{score.reasoning}</div>
                        {score.issues && score.issues.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-gray-200">
                            <div className="text-xs font-medium text-gray-600 mb-1">具体问题:</div>
                            <ul className="space-y-1">
                              {score.issues.map((issue, issueIdx) => (
                                <li key={issueIdx} className="text-xs text-red-600 flex items-start gap-1">
                                  <span>•</span>
                                  <span>{issue}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 测试方法完整性分析 */}
              {evaluation.logic.requirement_coverage_analysis && evaluation.logic.requirement_coverage_analysis.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5" />
                    测试方法完整性分析
                  </h4>
                  <div className="text-sm text-gray-600 mb-4">
                    针对每个原子需求，检查是否需要从五种测试方法中补充缺失的方法
                  </div>

                  <div className="space-y-3">
                    {evaluation.logic.requirement_coverage_analysis.map((analysis, idx) => {
                      const isComplete = analysis.is_complete
                      const hasMissing = (analysis.missing_required_methods?.length > 0) || 
                                        (analysis.missing_conditional_methods?.length > 0)
                      
                      return (
                        <div key={idx} className={`rounded-lg p-4 border-2 ${
                          isComplete ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'
                        }`}>
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                              <span className="font-mono font-semibold text-gray-900">{analysis.atomic_req_id}</span>
                              {isComplete ? (
                                <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                                  ✓ 完整覆盖
                                </span>
                              ) : (
                                <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">
                                  ⚠ 需补充
                                </span>
                              )}
                            </div>
                            <span className={`text-lg font-bold ${
                              analysis.completeness_score >= 80 ? 'text-green-600' :
                              analysis.completeness_score >= 60 ? 'text-blue-600' :
                              analysis.completeness_score >= 40 ? 'text-yellow-600' :
                              'text-red-600'
                            }`}>
                              {analysis.completeness_score}%
                            </span>
                          </div>

                          {/* 已覆盖的方法 */}
                          {analysis.covered_methods && analysis.covered_methods.length > 0 && (
                            <div className="mb-3">
                              <div className="text-xs font-medium text-gray-600 mb-1">✓ 已覆盖的测试方法:</div>
                              <div className="flex flex-wrap gap-1">
                                {analysis.covered_methods.map((method, mIdx) => (
                                  <span key={mIdx} className="px-2 py-0.5 bg-green-100 text-green-800 text-xs rounded">
                                    {method}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* 缺失的必选方法 */}
                          {analysis.missing_required_methods && analysis.missing_required_methods.length > 0 && (
                            <div className="mb-3">
                              <div className="text-xs font-medium text-red-600 mb-1">✗ 缺失的必选方法:</div>
                              <div className="flex flex-wrap gap-1">
                                {analysis.missing_required_methods.map((method, mIdx) => (
                                  <span key={mIdx} className="px-2 py-0.5 bg-red-100 text-red-800 text-xs rounded">
                                    {method}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* 缺失的条件方法 */}
                          {analysis.missing_conditional_methods && analysis.missing_conditional_methods.length > 0 && (
                            <div className="mb-3">
                              <div className="text-xs font-medium text-orange-600 mb-1">⚠ 建议补充的条件方法:</div>
                              <div className="flex flex-wrap gap-1">
                                {analysis.missing_conditional_methods.map((method, mIdx) => (
                                  <span key={mIdx} className="px-2 py-0.5 bg-orange-100 text-orange-800 text-xs rounded">
                                    {method}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* 补充建议 */}
                          {analysis.suggestions && analysis.suggestions.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-gray-200">
                              <div className="text-xs font-medium text-gray-600 mb-2">💡 补充建议:</div>
                              <div className="space-y-2">
                                {analysis.suggestions.map((suggestion, sIdx) => (
                                  <div key={sIdx} className="bg-white rounded p-2 text-xs">
                                    <div className="font-semibold text-gray-800 mb-1">
                                      {suggestion.method}
                                    </div>
                                    <div className="text-gray-600 mb-1">
                                      <strong>原因:</strong> {suggestion.reason}
                                    </div>
                                    <div className="text-gray-600">
                                      <strong>建议:</strong> {suggestion.test_case_suggestion}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}

              {/* 测试方法说明 */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
                <div className="font-medium text-blue-900 mb-2">📖 测试方法说明</div>
                <div className="text-sm text-blue-800 space-y-1">
                  <div>• <strong>正常测试</strong>：验证系统在正常条件下的功能是否符合预期</div>
                  <div>• <strong>健壮性测试</strong>：验证系统在边界条件、异常输入、故障情况下的行为</div>
                  <div>• <strong>完整覆盖</strong>：每个需求应同时包含正常测试和健壮性测试，确保全面验证</div>
                </div>
              </div>
            </div>
          </div>

          {/* 维度4：追溯链路与证据完整性 */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-bold text-gray-900 mb-4">🔗 维度4：追溯链路与证据完整性</h3>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <div className="bg-gray-50 rounded-lg p-3">
                <div className="text-sm text-gray-600">总链路数</div>
                <div className="text-2xl font-bold text-gray-900">{evaluation.traceability.total_traceability_links}</div>
              </div>
              <div className="bg-green-50 rounded-lg p-3">
                <div className="text-sm text-gray-600">有效链路</div>
                <div className="text-2xl font-bold text-green-600">{evaluation.traceability.valid_links}</div>
              </div>
              <div className="bg-red-50 rounded-lg p-3">
                <div className="text-sm text-gray-600">断链数</div>
                <div className="text-2xl font-bold text-red-600">{evaluation.traceability.broken_links}</div>
              </div>
              <div className="bg-purple-50 rounded-lg p-3">
                <div className="text-sm text-gray-600">证据引用率</div>
                <div className="text-2xl font-bold text-purple-600">
                  {(evaluation.traceability.evidence_rate * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {evaluation.traceability.broken_link_details.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <div className="font-medium text-red-900 mb-3 flex items-center gap-2">
                  <XCircle className="w-4 h-4" />
                  断链详情
                </div>
                <div className="space-y-2">
                  {evaluation.traceability.broken_link_details.map((link, idx) => (
                    <div key={idx} className="bg-white rounded p-3 border border-red-200">
                      <div className="text-sm text-red-800 mb-1">行 {link.row_index}</div>
                      <div className="text-xs text-red-600">
                        {link.issues.join(', ')}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <div className="font-medium text-purple-900 mb-2">📄 证据引用统计</div>
              <div className="text-sm text-purple-800">
                {evaluation.traceability.test_cases_with_evidence} / {evaluation.traceability.total_test_cases} 个测试用例包含证据引用
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
