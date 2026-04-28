import { useState } from 'react'
import axios from 'axios'
import { 
  Loader2, Send, Download, RefreshCw, CheckCircle2, AlertCircle,
  BookOpen, FileText, TestTube2, Lightbulb, Settings, Menu, X
} from 'lucide-react'

const API_BASE = 'http://localhost:8000'

function App() {
  const [requirementText, setRequirementText] = useState(
    `需求编号：REQ-LG-001
功能描述：起落架控制逻辑。
具体规约：当且仅当起落架控制手柄（Gear Handle）处于"DOWN"位置，且飞行速度（Airspeed）低于 250 节时，
起落架执行机构应在 3 秒内接收到"放下（Deploy）"指令。
若速度超过 250 节，即使手柄在"DOWN"位，也不允许执行放下动作，并需触发告警。`
  )
  
  const [llmProvider, setLlmProvider] = useState('qwen')
  const [llmModel, setLlmModel] = useState('qwen3-max')
  const [topK, setTopK] = useState(3)
  const [windowSize, setWindowSize] = useState(4)
  
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [indexStatus, setIndexStatus] = useState(null)

  const modelOptions = {
    qwen: ['qwen3-max', 'qwen3.6-plus', 'qwen3.5-plus', 'qwen3.6-flash'],
    deepseek: ['deepseek-v4-flash', 'deepseek-v4-pro'],
    zhipu: ['glm-5.1', 'glm-5', 'glm-4.7', 'glm-4.7-FlashX']
  }

  const checkHealth = async () => {
    try {
      const res = await axios.get(`${API_BASE}/api/health`)
      setIndexStatus(res.data)
    } catch (err) {
      setIndexStatus({ status: 'error', message: err.message })
    }
  }

  const rebuildIndex = async () => {
    if (!confirm('确定要重建向量索引吗？这可能需要几分钟时间。')) return
    setLoading(true)
    setError(null)
    try {
      await axios.post(`${API_BASE}/api/rebuild-index`)
      alert('✅ 索引重建完成！')
      await checkHealth()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const analyzeRequirement = async () => {
    if (!requirementText.trim()) {
      alert('请输入需求文本')
      return
    }
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await axios.post(`${API_BASE}/api/analyze`, {
        requirement_text: requirementText,
        llm_provider: llmProvider,
        llm_model: llmModel,
        top_k: topK,
        window_size: windowSize
      })
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const exportExcel = async () => {
    if (!result) {
      alert('请先生成分析结果')
      return
    }
    setLoading(true)
    try {
      // 添加 requirement_text 到导出数据中
      const exportData = {
        ...result,
        requirement_text: requirementText  // 从输入框获取原始需求文本
      }
      
      const res = await axios.post(`${API_BASE}/api/export-excel-direct`, exportData, {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `traceability_${result?.requirement_id || 'export'}.xlsx`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleProviderChange = (provider) => {
    setLlmProvider(provider)
    setLlmModel(modelOptions[provider][0])
  }

  const formatFieldValue = (value) => {
    if (Array.isArray(value)) {
      return value.map((item, idx) => (
        <div key={idx} className="mb-1">• {item}</div>
      ))
    }
    return value
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 导航栏 */}
      <nav className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            <div className="flex items-center">
              <div>
                <h1 className="text-2xl font-bold text-gray-900">RAG 机载软件需求解析与测试用例生成系统</h1>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {indexStatus && (
                <div className={`flex items-center space-x-2 px-4 py-2 rounded-full text-sm font-medium ${
                  indexStatus.status === 'healthy' 
                    ? 'bg-green-50 text-green-700 border border-green-200' 
                    : 'bg-red-50 text-red-700 border border-red-200'
                }`}>
                  <div className={`w-2 h-2 rounded-full animate-pulse ${
                    indexStatus.status === 'healthy' ? 'bg-green-500' : 'bg-red-500'
                  }`}></div>
                  <span>{indexStatus.status === 'healthy' ? '系统正常' : '系统异常'}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容区 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* 设置侧边栏 - 始终显示 */}
          <div className="lg:col-span-3">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6 sticky top-28">
              <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                <Settings className="w-5 h-5 text-blue-600" />
                系统设置
              </h2>

                <div className="space-y-3">
                  <button
                    onClick={checkHealth}
                    className="w-full px-4 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition flex items-center justify-center gap-2 font-medium shadow-sm"
                  >
                    <CheckCircle2 className="w-4 h-4" />
                    检查状态
                  </button>

                  <button
                    onClick={rebuildIndex}
                    disabled={loading}
                    className="w-full px-4 py-2.5 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition disabled:opacity-50 flex items-center justify-center gap-2 font-medium shadow-sm"
                  >
                    <RefreshCw className="w-4 h-4" />
                    重建向量库
                  </button>
                </div>

                <hr className="border-gray-200" />

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    🤖 LLM 提供商
                  </label>
                  <select
                    value={llmProvider}
                    onChange={(e) => handleProviderChange(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="qwen">阿里千问</option>
                    <option value="deepseek">DeepSeek</option>
                    <option value="zhipu">智谱AI</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    模型选择
                  </label>
                  <select
                    value={llmModel}
                    onChange={(e) => setLlmModel(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {modelOptions[llmProvider].map(model => (
                      <option key={model} value={model}>{model}</option>
                    ))}
                  </select>
                </div>

                <hr className="border-gray-200" />

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Top-K: {topK}
                  </label>
                  <input
                    type="range"
                    min="2"
                    max="8"
                    value={topK}
                    onChange={(e) => setTopK(Number(e.target.value))}
                    className="w-full accent-blue-600"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Window: {windowSize}
                  </label>
                  <input
                    type="range"
                    min="2"
                    max="8"
                    value={windowSize}
                    onChange={(e) => setWindowSize(Number(e.target.value))}
                    className="w-full accent-blue-600"
                  />
                </div>
              </div>
            </div>

          {/* 主内容 */}
          <div className="lg:col-span-9">
            <div className="space-y-6">
              {/* 输入区 */}
              <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-600" />
                  需求输入
                </h2>
                <textarea
                  value={requirementText}
                  onChange={(e) => setRequirementText(e.target.value)}
                  className="w-full h-40 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm"
                  placeholder="输入需求文本..."
                />
                <div className="flex gap-3 mt-4">
                  <button
                    onClick={analyzeRequirement}
                    disabled={loading}
                    className="flex-1 px-6 py-3 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg hover:from-blue-600 hover:to-indigo-700 transition disabled:opacity-50 flex items-center justify-center gap-2 font-medium shadow-md"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        分析中...
                      </>
                    ) : (
                      <>
                        <Send className="w-5 h-5" />
                        生成原子需求 + 测试用例
                      </>
                    )}
                  </button>
                  {result && (
                    <button
                      onClick={exportExcel}
                      disabled={loading}
                      className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition disabled:opacity-50 flex items-center gap-2 font-medium shadow-md"
                    >
                      <Download className="w-5 h-5" />
                      导出 Excel
                    </button>
                  )}
                </div>
              </div>

              {/* 错误提示 */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-red-800">错误</h3>
                    <p className="text-red-600 text-sm mt-1">{error}</p>
                  </div>
                </div>
              )}

              {/* 结果展示 */}
              {result && (
                <div className="space-y-6">
                  {/* 领域术语 */}
                  {result.domain_context && result.domain_context.length > 0 && (
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                      <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <BookOpen className="w-5 h-5 text-blue-600" />
                        领域术语解释
                      </h2>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        {result.domain_context.map((term, idx) => (
                          <div key={idx} className="bg-blue-50 rounded-lg p-4 border border-blue-100">
                            <div className="font-medium text-blue-900 mb-1">{term.matched_term}</div>
                            <div className="text-sm text-gray-700">{term.text}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* 原子需求 */}
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                      <Lightbulb className="w-5 h-5 text-yellow-600" />
                      原子需求 ({result.atomic_requirements?.length || 0})
                    </h2>
                    <div className="space-y-3">
                      {result.atomic_requirements?.map((ar, idx) => (
                        <details key={idx} className="bg-gray-50 rounded-lg border border-gray-200 overflow-hidden">
                          <summary className="px-4 py-3 cursor-pointer hover:bg-gray-100 font-medium flex items-center justify-between">
                            <span>{ar.req_id} | {ar.category || '未分类'}</span>
                            <span className="text-gray-400">▼</span>
                          </summary>
                          <div className="px-4 pb-4 space-y-3 border-t border-gray-200 pt-3">
                            <p className="text-gray-700">{ar.statement}</p>
                            {result.evidences?.[ar.req_id]?.length > 0 && (
                              <div className="mt-3">
                                <h4 className="font-medium text-gray-700 mb-2 text-sm">证据片段:</h4>
                                <div className="space-y-2">
                                  {result.evidences[ar.req_id].map((ev, evIdx) => (
                                    <div key={evIdx} className="bg-white rounded p-3 border border-gray-200 text-sm">
                                      <div className="flex items-center gap-2 mb-2">
                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                                          ev.category === 'Standards' 
                                            ? 'bg-blue-100 text-blue-700' 
                                            : 'bg-green-100 text-green-700'
                                        }`}>
                                          {ev.category === 'Standards' ? '📘 标准' : '📄 SRD'}
                                        </span>
                                        <span className="text-gray-600 text-xs">{ev.ref}</span>
                                      </div>
                                      <pre className="text-xs text-gray-600 whitespace-pre-wrap font-mono bg-gray-50 p-2 rounded">
                                        {ev.text?.substring(0, 300)}...
                                      </pre>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </details>
                      ))}
                    </div>
                  </div>

                  {/* 测试用例 */}
                  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                    <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                      <TestTube2 className="w-5 h-5 text-green-600" />
                      IEEE 829 测试用例 ({result.test_cases?.length || 0})
                    </h2>
                    <div className="space-y-3">
                      {result.test_cases?.map((tc, idx) => (
                        <details key={idx} className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg border border-green-200 overflow-hidden">
                          <summary className="px-4 py-3 cursor-pointer hover:bg-green-100 font-medium flex items-center justify-between">
                            <span>{tc.tc_id} | {tc.title}</span>
                            <span className="text-gray-400">▼</span>
                          </summary>
                          <div className="px-4 pb-4 space-y-3 border-t border-green-200 pt-3">
                            {tc.design_rationale && (
                              <div className="bg-blue-50 border-l-4 border-blue-400 p-3 rounded">
                                <div className="font-medium text-blue-900 mb-1 text-sm">💡 推导逻辑</div>
                                <p className="text-sm text-blue-800">{tc.design_rationale}</p>
                              </div>
                            )}
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                              <div>
                                <span className="font-medium text-gray-700">目的: </span>
                                <span className="text-gray-600">{tc.objective}</span>
                              </div>
                              {tc.test_method && (
                                <div>
                                  <span className="font-medium text-gray-700">测试方法: </span>
                                  <span className="text-gray-600">{tc.test_method}</span>
                                </div>
                              )}
                            </div>
                            
                            {tc.preconditions && (
                              <div>
                                <div className="font-medium text-gray-700 mb-1 text-sm">前置条件:</div>
                                <div className="text-sm text-gray-600 bg-white p-3 rounded border">
                                  {formatFieldValue(tc.preconditions)}
                                </div>
                              </div>
                            )}
                            
                            {tc.inputs && (
                              <div>
                                <div className="font-medium text-gray-700 mb-1 text-sm">输入/刺激:</div>
                                <div className="text-sm text-gray-600 bg-white p-3 rounded border">
                                  {formatFieldValue(tc.inputs)}
                                </div>
                              </div>
                            )}
                            
                            {tc.steps && (
                              <div>
                                <div className="font-medium text-gray-700 mb-1 text-sm">步骤:</div>
                                <div className="text-sm text-gray-600 bg-white p-3 rounded border">
                                  {formatFieldValue(tc.steps)}
                                </div>
                              </div>
                            )}
                            
                            {tc.expected_results && (
                              <div>
                                <div className="font-medium text-gray-700 mb-1 text-sm">期望结果:</div>
                                <div className="text-sm text-gray-600 bg-white p-3 rounded border">
                                  {formatFieldValue(tc.expected_results)}
                                </div>
                              </div>
                            )}
                          </div>
                        </details>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
