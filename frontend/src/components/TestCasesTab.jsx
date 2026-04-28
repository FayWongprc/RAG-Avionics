import { TestTube2, ChevronDown, ChevronUp, Filter, FileText } from 'lucide-react'
import { useState, useMemo } from 'react'

export default function TestCasesTab({ result }) {
  const [expandedTestCases, setExpandedTestCases] = useState(new Set())
  const [expandedRequirements, setExpandedRequirements] = useState(new Set())
  const [filterMethod, setFilterMethod] = useState('all')

  const toggleTestCase = (id) => {
    const newExpanded = new Set(expandedTestCases)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedTestCases(newExpanded)
  }

  const toggleRequirement = (id) => {
    const newExpanded = new Set(expandedRequirements)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedRequirements(newExpanded)
  }

  const expandAll = () => {
    const allReqIds = Object.keys(groupedTestCases)
    const allTcIds = Object.values(groupedTestCases).flat().map(tc => tc.tc_id)
    setExpandedRequirements(new Set(allReqIds))
    setExpandedTestCases(new Set(allTcIds))
  }

  const collapseAll = () => {
    setExpandedRequirements(new Set())
    setExpandedTestCases(new Set())
  }

  const formatFieldValue = (value) => {
    if (Array.isArray(value)) {
      return value.map((item, idx) => (
        <div key={idx} className="mb-1">• {item}</div>
      ))
    }
    return value
  }

  // 获取所有测试方法
  const allMethods = [...new Set(result.test_cases?.map(tc => tc.test_method).filter(Boolean))]

  // 按原子需求分组测试用例
  const groupedTestCases = useMemo(() => {
    const filtered = filterMethod === 'all' 
      ? result.test_cases 
      : result.test_cases?.filter(tc => tc.test_method === filterMethod)
    
    const grouped = {}
    filtered?.forEach(tc => {
      const reqId = tc.trace_to_atomic_req || 'UNKNOWN'
      if (!grouped[reqId]) {
        grouped[reqId] = []
      }
      grouped[reqId].push(tc)
    })
    return grouped
  }, [result.test_cases, filterMethod])

  // 获取原子需求信息
  const getAtomicReqInfo = (reqId) => {
    return result.atomic_requirements?.find(ar => ar.req_id === reqId)
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* 统计信息 */}
      <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-xl border border-green-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">📊 测试用例统计</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-green-600">{result.test_cases?.length || 0}</div>
            <div className="text-sm text-gray-600 mt-1">总用例数</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-blue-600">{allMethods.length}</div>
            <div className="text-sm text-gray-600 mt-1">测试方法</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-purple-600">
              {new Set(result.test_cases?.map(tc => tc.trace_to_atomic_req)).size}
            </div>
            <div className="text-sm text-gray-600 mt-1">覆盖需求</div>
          </div>
          <div className="bg-white rounded-lg p-4 text-center">
            <div className="text-3xl font-bold text-orange-600">
              {result.test_cases?.filter(tc => tc.evidence_refs && tc.evidence_refs.length > 0).length}
            </div>
            <div className="text-sm text-gray-600 mt-1">含证据引用</div>
          </div>
        </div>
      </div>

      {/* 控制栏 */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <Filter className="w-5 h-5 text-gray-600" />
            <select
              value={filterMethod}
              onChange={(e) => setFilterMethod(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">全部方法 ({result.test_cases?.length || 0})</option>
              {allMethods.map(method => (
                <option key={method} value={method}>
                  {method} ({result.test_cases?.filter(tc => tc.test_method === method).length})
                </option>
              ))}
            </select>
          </div>

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
      </div>

      {/* 按原子需求分组的测试用例 */}
      <div className="space-y-4">
        {Object.entries(groupedTestCases).map(([reqId, testCases]) => {
          const atomicReq = getAtomicReqInfo(reqId)
          const isReqExpanded = expandedRequirements.has(reqId)

          return (
            <div key={reqId} className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
              {/* 原子需求标题栏 */}
              <button
                onClick={() => toggleRequirement(reqId)}
                className="w-full px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 flex items-center justify-between transition border-b border-gray-200"
              >
                <div className="flex items-center gap-4 flex-1">
                  <FileText className="w-5 h-5 text-blue-600 flex-shrink-0" />
                  <div className="text-left">
                    <div className="flex items-center gap-3 mb-1">
                      <span className="font-mono font-bold text-blue-600">{reqId}</span>
                      {atomicReq?.category && (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-800 text-xs font-medium rounded">
                          {atomicReq.category}
                        </span>
                      )}
                      <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded">
                        {testCases.length} 个测试用例
                      </span>
                    </div>
                    {atomicReq?.statement && (
                      <p className="text-sm text-gray-600 line-clamp-2">{atomicReq.statement}</p>
                    )}
                  </div>
                </div>
                {isReqExpanded ? (
                  <ChevronUp className="w-6 h-6 text-gray-400 flex-shrink-0" />
                ) : (
                  <ChevronDown className="w-6 h-6 text-gray-400 flex-shrink-0" />
                )}
              </button>

              {/* 测试用例列表 */}
              {isReqExpanded && (
                <div className="p-4 space-y-3 bg-gray-50">
                  {testCases.map((tc, idx) => {
                    const isTcExpanded = expandedTestCases.has(tc.tc_id)

                    return (
                      <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden bg-white hover:border-green-300 transition">
                        <button
                          onClick={() => toggleTestCase(tc.tc_id)}
                          className="w-full px-4 py-3 bg-gradient-to-r from-green-50 to-blue-50 hover:from-green-100 hover:to-blue-100 flex items-center justify-between transition"
                        >
                          <div className="flex items-center gap-3 flex-1">
                            <span className="font-mono font-semibold text-green-600">{tc.tc_id}</span>
                            {tc.test_method && (
                              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded">
                                {tc.test_method}
                              </span>
                            )}
                            <span className="text-gray-700 text-left">{tc.title}</span>
                          </div>
                          {isTcExpanded ? (
                            <ChevronUp className="w-5 h-5 text-gray-400 flex-shrink-0" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400 flex-shrink-0" />
                          )}
                        </button>

                        {isTcExpanded && (
                          <div className="px-4 py-4 bg-white border-t border-gray-200 space-y-4">
                            {/* 设计理由（高亮显示） */}
                            {tc.design_rationale && (
                              <div className="bg-blue-50 border-l-4 border-blue-400 p-4 rounded">
                                <div className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
                                  💡 设计理由
                                </div>
                                <p className="text-sm text-blue-800">{tc.design_rationale}</p>
                              </div>
                            )}

                            {/* 基本信息 */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                              <div>
                                <h4 className="font-semibold text-gray-700 mb-1 text-sm">测试目的</h4>
                                <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded">{tc.objective}</p>
                              </div>
                              <div>
                                <h4 className="font-semibold text-gray-700 mb-1 text-sm">追溯需求</h4>
                                <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded font-mono">
                                  {tc.trace_to_atomic_req}
                                </p>
                              </div>
                            </div>

                            {/* 测试详情 */}
                            {tc.preconditions && (
                              <div>
                                <h4 className="font-semibold text-gray-700 mb-2 text-sm">前置条件</h4>
                                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded border border-gray-200">
                                  {formatFieldValue(tc.preconditions)}
                                </div>
                              </div>
                            )}

                            {tc.inputs && (
                              <div>
                                <h4 className="font-semibold text-gray-700 mb-2 text-sm">输入/刺激</h4>
                                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded border border-gray-200">
                                  {formatFieldValue(tc.inputs)}
                                </div>
                              </div>
                            )}

                            {tc.steps && (
                              <div>
                                <h4 className="font-semibold text-gray-700 mb-2 text-sm">测试步骤</h4>
                                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded border border-gray-200">
                                  {formatFieldValue(tc.steps)}
                                </div>
                              </div>
                            )}

                            {tc.expected_results && (
                              <div>
                                <h4 className="font-semibold text-gray-700 mb-2 text-sm">预期结果</h4>
                                <div className="text-sm text-gray-600 bg-green-50 p-3 rounded border border-green-200">
                                  {formatFieldValue(tc.expected_results)}
                                </div>
                              </div>
                            )}

                            {tc.postconditions && (
                              <div>
                                <h4 className="font-semibold text-gray-700 mb-2 text-sm">后置条件</h4>
                                <div className="text-sm text-gray-600 bg-gray-50 p-3 rounded border border-gray-200">
                                  {formatFieldValue(tc.postconditions)}
                                </div>
                              </div>
                            )}

                            {/* 证据引用 */}
                            {tc.evidence_refs && tc.evidence_refs.length > 0 && (
                              <div>
                                <h4 className="font-semibold text-gray-700 mb-2 text-sm">证据引用</h4>
                                <div className="flex flex-wrap gap-2">
                                  {tc.evidence_refs.map((ref, refIdx) => (
                                    <span key={refIdx} className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                                      {ref}
                                    </span>
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
              )}
            </div>
          )
        })}
      </div>

    </div>
  )
}
