import { FileText, Lightbulb, TestTube2, BarChart3, Download } from 'lucide-react'

const tabs = [
  { id: 'input', label: '需求输入', icon: FileText, color: 'blue' },
  { id: 'atomic', label: '原子需求', icon: Lightbulb, color: 'yellow' },
  { id: 'testcases', label: '测试用例', icon: TestTube2, color: 'green' },
  { id: 'evaluation', label: '质量评估', icon: BarChart3, color: 'purple' },
  { id: 'export', label: '导出报告', icon: Download, color: 'indigo' },
]

export default function TabNavigation({ activeTab, onTabChange, hasResult }) {
  return (
    <div className="bg-white shadow-md border-b border-gray-200 sticky top-20 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav className="flex space-x-2 overflow-x-auto py-2" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon
            const isActive = activeTab === tab.id
            const isDisabled = !hasResult && tab.id !== 'input'
            
            const colorClasses = {
              blue: 'from-blue-500 to-blue-600 shadow-blue-200',
              yellow: 'from-yellow-500 to-amber-600 shadow-yellow-200',
              green: 'from-green-500 to-emerald-600 shadow-green-200',
              purple: 'from-purple-500 to-purple-600 shadow-purple-200',
              indigo: 'from-indigo-500 to-indigo-600 shadow-indigo-200',
            }
            
            return (
              <button
                key={tab.id}
                onClick={() => !isDisabled && onTabChange(tab.id)}
                disabled={isDisabled}
                className={`
                  flex items-center gap-2.5 px-5 py-3 rounded-lg font-medium text-sm whitespace-nowrap
                  transition-all duration-300 transform
                  ${isActive
                    ? `bg-gradient-to-r ${colorClasses[tab.color]} text-white shadow-lg ${colorClasses[tab.color]} scale-105`
                    : isDisabled
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-gray-50 text-gray-600 hover:bg-gray-100 hover:text-gray-900 hover:shadow-md hover:scale-102'
                  }
                `}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'animate-pulse' : ''}`} />
                <span>{tab.label}</span>
                {isActive && (
                  <div className="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
                )}
              </button>
            )
          })}
        </nav>
      </div>
    </div>
  )
}
