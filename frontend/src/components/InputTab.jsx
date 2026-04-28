import { useState } from 'react'
import { Loader2, Send, Settings, HelpCircle, ChevronDown, ChevronUp, CheckCircle2, RefreshCw } from 'lucide-react'

export default function InputTab({ 
  requirementText, 
  setRequirementText,
  llmProvider,
  setLlmProvider,
  llmModel,
  setLlmModel,
  topK,
  setTopK,
  windowSize,
  setWindowSize,
  onAnalyze,
  loading,
  onCheckHealth,
  onRebuildIndex,
  indexStatus,
  hasResult,
  onReset
}) {
  const [showHelp, setShowHelp] = useState(false)

  const modelOptions = {
    qwen: ['qwen3-max', 'qwen3.6-plus', 'qwen3.5-plus', 'qwen3.6-flash'],
    deepseek: ['deepseek-v4-flash', 'deepseek-v4-pro'],
    zhipu: ['glm-5.1', 'glm-5', 'glm-4.7', 'glm-4.7-FlashX']
  }

  const handleProviderChange = (provider) => {
    setLlmProvider(provider)
    setLlmModel(modelOptions[provider][0])
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* 左侧：系统设置 */}
      <div className="lg:col-span-4">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sticky top-32">
          <div className="flex items-center gap-2 mb-6">
            <Settings className="w-5 h-5 text-blue-600" />
            <h3 className="text-lg font-bold text-gray-900">系统设置</h3>
          </div>
          
          <div className="space-y-5">
            {/* 系统操作按钮 */}
            <div className="space-y-2">
              <button
                onClick={onCheckHealth}
                className="w-full px-4 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition flex items-center justify-center gap-2 font-medium text-sm"
              >
                <CheckCircle2 className="w-4 h-4" />
                检查系统状态
              </button>

              <button
                onClick={onRebuildIndex}
                disabled={loading}
                className="w-full px-4 py-2.5 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition disabled:opacity-50 flex items-center justify-center gap-2 font-medium text-sm"
              >
                <RefreshCw className="w-4 h-4" />
                重建向量索引
              </button>
              
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-2 text-xs text-yellow-800">
                <div className="font-medium mb-0.5">⚠️ 注意</div>
                <div>修改知识库文件后需要重建向量索引才能生效</div>
              </div>
            </div>

            <hr className="border-gray-200" />

            {/* LLM 设置 */}
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
                模型选择（用于检索、生成、评估）
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                检索证据数量 (Top-K): {topK}
              </label>
              <input
                type="range"
                min="2"
                max="8"
                value={topK}
                onChange={(e) => setTopK(Number(e.target.value))}
                className="w-full accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>少 (2)</span>
                <span>多 (8)</span>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                句子窗口大小 (Window): {windowSize}
              </label>
              <input
                type="range"
                min="2"
                max="8"
                value={windowSize}
                onChange={(e) => setWindowSize(Number(e.target.value))}
                className="w-full accent-blue-600"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>小 (2)</span>
                <span>大 (8)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 右侧：需求输入区 */}
      <div className="lg:col-span-8 space-y-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-gray-900">输入需求文本</h2>
            <button
              onClick={() => setShowHelp(!showHelp)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition"
            >
              <HelpCircle className="w-4 h-4" />
              使用说明
              {showHelp ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>
          </div>

          {/* 使用说明（可折叠） */}
          {showHelp && (
            <div className="mb-4 bg-blue-50 rounded-lg border border-blue-200 p-4">
              <div className="space-y-3 text-sm text-blue-800">
                {/* 系统设置说明 */}
                <div>
                  <div className="font-semibold mb-1.5">⚙️ 系统设置（左侧）</div>
                  <ul className="space-y-1 ml-4 text-xs">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600">•</span>
                      <span><strong>LLM 提供商</strong>：选择使用的大模型服务（千问/DeepSeek/智谱）</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600">•</span>
                      <span><strong>模型选择</strong>：选择具体的模型版本，不同模型性能和成本不同</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600">•</span>
                      <span><strong>Top-K</strong>：每个原子需求检索的证据数量，越大越全面但速度越慢</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600">•</span>
                      <span><strong>Window</strong>：句子窗口大小，越大上下文越完整但可能引入噪声</span>
                    </li>
                  </ul>
                </div>

                {/* 使用步骤 */}
                <div>
                  <div className="font-semibold mb-1.5">📝 使用步骤</div>
                  <ul className="space-y-1 ml-4 text-xs">
                    <li className="flex items-start gap-2">
                      <span className="font-bold text-blue-600">1.</span>
                      <span>在下方文本框中输入需求文本（支持多段需求）</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold text-blue-600">2.</span>
                      <span>点击"开始分析"按钮，系统将自动提取术语、分解需求、检索证据、生成测试用例</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="font-bold text-blue-600">3.</span>
                      <span>分析完成后，切换到其他标签页查看详细结果和质量评估</span>
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          <textarea
            value={requirementText}
            onChange={(e) => setRequirementText(e.target.value)}
            disabled={hasResult}
            className={`w-full h-80 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none font-mono text-sm ${
              hasResult ? 'bg-gray-50 cursor-not-allowed' : ''
            }`}
            placeholder={`请输入需求文本，例如：

需求编号：REQ-LG-001
功能描述：起落架控制逻辑
具体规约：当且仅当起落架控制手柄（Gear Handle）处于 DOWN 位置，且飞行速度（Airspeed）低于 250 节时，起落架执行机构应在 3 秒内接收到放下（Deploy）指令。若速度超过 250 节，即使手柄在 DOWN 位，也不允许执行放下动作，并需触发告警。`}
          />

          {hasResult ? (
            <button
              onClick={onReset}
              disabled={loading}
              className="w-full mt-4 px-6 py-4 bg-gradient-to-r from-orange-500 to-red-600 text-white rounded-lg hover:from-orange-600 hover:to-red-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium shadow-lg text-lg"
            >
              <RefreshCw className="w-6 h-6" />
              重新输入与分析
            </button>
          ) : (
            <button
              onClick={onAnalyze}
              disabled={loading || !requirementText.trim()}
              className="w-full mt-4 px-6 py-4 bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-lg hover:from-blue-600 hover:to-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-medium shadow-lg text-lg"
            >
              {loading ? (
                <>
                  <Loader2 className="w-6 h-6 animate-spin" />
                  正在分析需求...
                </>
              ) : (
                <>
                  <Send className="w-6 h-6" />
                  开始分析 - 生成原子需求和测试用例
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
