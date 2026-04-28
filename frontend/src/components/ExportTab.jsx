import { Download, FileSpreadsheet, Loader2 } from 'lucide-react'
import { useState } from 'react'
import axios from 'axios'

const API_BASE = 'http://localhost:8000'

export default function ExportTab({ result, requirementText }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const exportExcel = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const exportData = {
        ...result,
        requirement_text: requirementText
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

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* 统计信息 - 移到顶部 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 导出数据统计</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div className="bg-yellow-50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-yellow-600">
              {result.atomic_requirements?.length || 0}
            </div>
            <div className="text-sm text-gray-600 mt-1">原子需求</div>
          </div>
          <div className="bg-green-50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-green-600">
              {result.test_cases?.length || 0}
            </div>
            <div className="text-sm text-gray-600 mt-1">测试用例</div>
          </div>
          <div className="bg-purple-50 rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">
              {Object.values(result.evidences || {}).flat().length}
            </div>
            <div className="text-sm text-gray-600 mt-1">证据片段</div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
        <div className="text-center mb-8">
          <FileSpreadsheet className="w-16 h-16 text-green-600 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-900 mb-2">导出追溯矩阵</h2>
          <p className="text-gray-600">
            将生成的原子需求、测试用例和追溯关系导出为 Excel 文件
          </p>
        </div>

        <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-6 mb-6">
          <h3 className="font-semibold text-gray-900 mb-3">📋 导出内容包括：</h3>
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span><strong>Requirements</strong> - 原始需求信息</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span><strong>AtomicRequirements</strong> - 分解后的原子需求</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span><strong>TestCases</strong> - IEEE 829 标准测试用例</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span><strong>TraceabilityMatrix</strong> - 需求-用例追溯矩阵</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-green-600 font-bold">✓</span>
              <span><strong>Evidence</strong> - 检索到的证据片段</span>
            </li>
          </ul>
        </div>

        <button
          onClick={exportExcel}
          disabled={loading}
          className="w-full px-6 py-4 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-lg hover:from-green-600 hover:to-emerald-700 transition disabled:opacity-50 flex items-center justify-center gap-2 font-medium shadow-lg text-lg"
        >
          {loading ? (
            <>
              <Loader2 className="w-6 h-6 animate-spin" />
              正在生成 Excel...
            </>
          ) : (
            <>
              <Download className="w-6 h-6" />
              下载 Excel 文件
            </>
          )}
        </button>

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-600">
            导出失败: {error}
          </div>
        )}
      </div>

      {/* 使用提示 */}
      <div className="bg-blue-50 rounded-xl border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">💡 使用提示</h3>
        <ul className="space-y-2 text-sm text-blue-800">
          <li className="flex items-start gap-2">
            <span className="font-bold mt-0.5">•</span>
            <span>Excel 文件可以直接用于需求管理和测试管理工具</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="font-bold mt-0.5">•</span>
            <span>追溯矩阵符合 DO-178C 和 ARP4754A 标准要求</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="font-bold mt-0.5">•</span>
            <span>建议在质量评估后再导出，确保数据质量</span>
          </li>
        </ul>
      </div>
    </div>
  )
}
