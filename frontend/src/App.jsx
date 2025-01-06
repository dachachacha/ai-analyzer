 import React, { useState } from 'react'
import CodeAnalyze from './components/CodeAnalyze'
import AIQuery from './components/AIQuery'
import QueryHistory from './components/QueryHistory'

function App() {
  const [activeTab, setActiveTab] = useState('analyze')

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-blue-800 text-white p-4">
        <h1 className="text-2xl font-semibold">Code + AI Demo</h1>
      </header>

      <div className="flex justify-center bg-gray-200 p-2">
        <button
          className={`mx-2 px-4 py-2 rounded ${
            activeTab === 'analyze' ? 'bg-blue-600 text-white' : 'bg-white text-black'
          }`}
          onClick={() => setActiveTab('analyze')}
        >
          Code Analyze
        </button>
        <button
          className={`mx-2 px-4 py-2 rounded ${
            activeTab === 'query' ? 'bg-blue-600 text-white' : 'bg-white text-black'
          }`}
          onClick={() => setActiveTab('query')}
        >
          AI Query
        </button>
        <button
          className={`mx-2 px-4 py-2 rounded ${
            activeTab === 'history' ? 'bg-blue-600 text-white' : 'bg-white text-black'
          }`}
          onClick={() => setActiveTab('history')}
        >
          Query History
        </button>
      </div>

      <main className="flex-grow p-4">
        {activeTab === 'analyze' && <CodeAnalyze />}
        {activeTab === 'query' && <AIQuery />}
        {activeTab === 'history' && <QueryHistory />}
      </main>
      
      <footer className="bg-gray-300 text-center py-2">
        <p className="text-sm">© 2025 AI Caller demo</p>
      </footer>
    </div>
  )
}

export default App

