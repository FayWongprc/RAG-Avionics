import { useState, useEffect } from 'react'
import axios from 'axios'
import { CheckCircle2, RefreshCw, AlertCircle } from 'lucide-react'

import TabNavigation from './components/TabNavigation'
import InputTab from './components/InputTab'
import AtomicRequirementsTab from './components/AtomicRequirementsTab'
import TestCasesTab from './components/TestCasesTab'
import EvaluationTab from './components/EvaluationTab'
import ExportTab from './components/ExportTab'

const API_BASE = 'http://localhost:8000'

function App() {
  const [activeTab, setActiveTab] = useState('input')
  const [requirementText, setRequirementText] = useState(
    localStorage.getItem('requirementText') || 
    `需求编号：REQ-LG-001
功能描述：起落架控制逻辑。
具体规约：当且仅当起落架控制手柄（Gear Handle）处于"DOWN"位置，且飞行速度（Airspeed）低于 250 节时，
起落架执行机构应在 3 秒内接收到"放下（Deploy）"指令。
若速度超过 250 节，即使手柄在"DOWN"位，也不允许执行放下动作，并需触发告警。`
  )
  
  const [llmProvider, setLlmProvider] = useState(localStorage.getItem('llmProvider') || 'qwen')
  const [llmModel, setLlmModel] = useState(localStorage.getItem('llmModel') || 'qwen3-max')
  const [topK, setTopK] = useState(Number(localStorage.getItem('topK')) || 3)
  const [windowSize, setWindowSize] = useState(Number(localStorage.getItem('windowSize')) || 4)
  
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(() => {
    const saved = localStorage.getItem('analysisResult')
    return saved ? JSON.parse(saved) : null
  })
  const [error, setError] = useState(null)
  const [indexStatus, setIndexStatus] = useState(null)

  // 保存数据到 localStorage
  useEffect(() => {
    localStorage.setItem('requirementText', requirementText)
  }, [requirementText])

  useEffect(() => {
    localStorage.setItem('llmProvider', llmProvider)
  }, [llmProvider])

  useEffect(() => {
    localStorage.setItem('llmModel', llmModel)
  }, [llmModel])

  useEffect(() => {
    localStorage.setItem('topK', topK.toString())
  }, [topK])

  useEffect(() => {
    localStorage.setItem('windowSize', windowSize.toString())
  }, [windowSize])

  useEffect(() => {
    if (result) {
      localStorage.setItem('analysisResult', JSON.stringify(result))
    } else {
      localStorage.removeItem('analysisResult')
    }
  }, [result])

  useEffect(() => {
    checkHealth()
  }, [])

  const checkHealth = async (showAlert = false) => {
    try {
      const res = await axios.get(`${API_BASE}/api/health`)
      setIndexStatus(res.data)
      // 只在手动检查时显示提示
      if (showAlert) {
        if (res.data.status === 'healthy') {
          alert('✅ 系统状态正常\n索引: ' + (res.data.index_loaded ? '已加载' : '未加载'))
        } else {
          alert('❌ 系统状态异常\n' + (res.data.message || '未知错误'))
        }
      }
    } catch (err) {
      setIndexStatus({ status: 'error', message: err.message })
      if (showAlert) {
        alert('❌ 无法连接到后端服务\n' + err.message)
      }
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
      setActiveTab('atomic') // 自动切换到结果标签页
    } catch (err) {
      setError(err.response?.data?.detail || err.message)
    } finally {
      setLoading(false)
    }
  }

  const resetAnalysis = () => {
    if (confirm('确定要清空当前分析结果并重新开始吗？记得导出报告进行保存！')) {
      setResult(null)
      setRequirementText('')
      setError(null)
      setActiveTab('input')
      localStorage.removeItem('analysisResult')
      localStorage.removeItem('requirementText')
      localStorage.removeItem('evaluationResult')  // 同时清除评估结果
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* 顶部导航栏 */}
      <nav className="bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 shadow-lg sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-20">
            {/* 标题 */}
            <div>
              <h1 className="text-2xl font-bold text-white tracking-tight">
                RAG 机载软件需求解析与测试用例生成系统
              </h1>
              <p className="text-blue-100 text-sm font-medium mt-0.5">
                Avionics Requirements Analysis & Test Generation
              </p>
            </div>

            <div className="flex items-center space-x-4">
              {indexStatus && (
                <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium backdrop-blur-sm ${
                  indexStatus.status === 'healthy' 
                    ? 'bg-green-500/20 text-white border border-green-300/30' 
                    : 'bg-red-500/20 text-white border border-red-300/30'
                }`}>
                  <div className={`w-2.5 h-2.5 rounded-full animate-pulse ${
                    indexStatus.status === 'healthy' ? 'bg-green-300' : 'bg-red-300'
                  }`}></div>
                  <span>{indexStatus.status === 'healthy' ? '系统正常' : '系统异常'}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* 标签页导航 */}
      <TabNavigation 
        activeTab={activeTab} 
        onTabChange={setActiveTab}
        hasResult={!!result}
      />

      {/* 主内容区 */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 错误提示 */}
        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-medium text-red-800">错误</h3>
              <p className="text-red-600 text-sm mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* 标签页内容 */}
        {activeTab === 'input' && (
          <InputTab
            requirementText={requirementText}
            setRequirementText={setRequirementText}
            llmProvider={llmProvider}
            setLlmProvider={setLlmProvider}
            llmModel={llmModel}
            setLlmModel={setLlmModel}
            topK={topK}
            setTopK={setTopK}
            windowSize={windowSize}
            setWindowSize={setWindowSize}
            onAnalyze={analyzeRequirement}
            loading={loading}
            onCheckHealth={checkHealth}
            onRebuildIndex={rebuildIndex}
            indexStatus={indexStatus}
            hasResult={!!result}
            onReset={resetAnalysis}
          />
        )}

        {activeTab === 'atomic' && result && (
          <AtomicRequirementsTab result={result} />
        )}

        {activeTab === 'testcases' && result && (
          <TestCasesTab result={result} />
        )}

        {activeTab === 'evaluation' && result && (
          <EvaluationTab 
            result={result}
            llmProvider={llmProvider}
            llmModel={llmModel}
          />
        )}

        {activeTab === 'export' && result && (
          <ExportTab 
            result={result}
            requirementText={requirementText}
          />
        )}
      </div>
    </div>
  )
}

export default App
