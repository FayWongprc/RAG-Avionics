import { BookOpen, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

export default function AtomicRequirementsTab({ result }) {
  const [expandedIds, setExpandedIds] = useState(new Set())

  const toggleExpand = (id) => {
    const newExpanded = new Set(expandedIds)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedIds(newExpanded)
  }

  const expandAll = () => {
    setExpandedIds(new Set(result.atomic_requirements.map(ar => ar.req_id)))
  }

  const collapseAll = () => {
    setExpandedIds(new Set())
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* 统计信息 */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 统计信息</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">{result.atomic_requirements?.length || 0}</div>
            <div className="text-sm text-gray-600 mt-1">原子需求</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-green-600">
              {new Set(result.atomic_requirements?.map(ar => ar.category)).size}
            </div>
            <div className="text-sm text-gray-600 mt-1">需求类别</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">
              {Object.values(result.evidences || {}).flat().length}
            </div>
            <div className="text-sm text-gray-600 mt-1">证据片段</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-orange-600">
              {result.domain_context?.length || 0}
            </div>
            <div className="text-sm text-gray-600 mt-1">领域术语</div>
          </div>
        </div>
      </div>

      {/* 领域术语 */}
      {result.domain_context && result.domain_context.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="w-5 h-5 text-blue-600" />
            <h2 className="text-xl font-bold text-gray-900">
              领域术语解释 ({result.domain_context.length})
            </h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {result.domain_context.map((term, idx) => (
              <div key={idx} className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                <div className="font-semibold text-blue-900 mb-2">{term.matched_term}</div>
                <div className="text-sm text-gray-700">{term.text}</div>
                <div className="text-xs text-gray-500 mt-2">来源: {term.ref}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 原子需求 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900">
            原子需求 ({result.atomic_requirements?.length || 0})
          </h2>
          <div className="flex gap-2">
            <button
              onClick={expandAll}
              className="px-3 py-1.5 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition"
            >
              全部展开
            </button>
            <button
              onClick={collapseAll}
              className="px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition"
            >
              全部折叠
            </button>
          </div>
        </div>

        <div className="space-y-3">
          {result.atomic_requirements?.map((ar, idx) => {
            const isExpanded = expandedIds.has(ar.req_id)
            const evidences = result.evidences?.[ar.req_id] || []

            return (
              <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden hover:border-blue-300 transition">
                <button
                  onClick={() => toggleExpand(ar.req_id)}
                  className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 flex items-center justify-between transition"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-semibold text-blue-600">{ar.req_id}</span>
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">
                      {ar.category || '未分类'}
                    </span>
                  </div>
                  {isExpanded ? (
                    <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                  )}
                </button>

                {isExpanded && (
                  <div className="px-4 py-4 bg-white border-t border-gray-200 space-y-4">
                    {/* 需求详情 */}
                    <div>
                      <h4 className="font-semibold text-gray-700 mb-2">需求陈述</h4>
                      <p className="text-gray-600 bg-gray-50 p-3 rounded">{ar.statement}</p>
                    </div>

                    {ar.source_text && (
                      <div>
                        <h4 className="font-semibold text-gray-700 mb-2">来源文本</h4>
                        <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded">{ar.source_text}</p>
                      </div>
                    )}

                    {/* 证据片段 */}
                    {evidences.length > 0 && (
                      <div>
                        <h4 className="font-semibold text-gray-700 mb-2">
                          检索到的证据片段 ({evidences.length})
                        </h4>
                        <div className="space-y-2">
                          {evidences.map((ev, evIdx) => (
                            <div key={evIdx} className="bg-gray-50 rounded-lg p-3 border border-gray-200">
                              <div className="flex items-center gap-2 mb-2">
                                <span className={`px-2 py-1 rounded text-xs font-medium ${
                                  ev.category === 'Standards' 
                                    ? 'bg-blue-100 text-blue-700' 
                                    : 'bg-green-100 text-green-700'
                                }`}>
                                  {ev.category === 'Standards' ? '📘 标准文档' : '📄 SRD文档'}
                                </span>
                                <span className="text-xs text-gray-600">{ev.ref}</span>
                                <span className="text-xs text-gray-500">相似度: {(ev.score * 100).toFixed(1)}%</span>
                              </div>
                              <pre className="text-xs text-gray-700 whitespace-pre-wrap font-mono bg-white p-2 rounded border border-gray-200">
                                {ev.text?.substring(0, 400)}{ev.text?.length > 400 ? '...' : ''}
                              </pre>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

    </div>
  )
}
