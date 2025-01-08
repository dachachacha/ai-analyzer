import React, { useState } from 'react';
import CodeAnalyze from './components/CodeAnalyze';
import AIQuery from './components/AIQuery';
import QueryHistory from './components/QueryHistory';
import Projects from './components/Projects';

function App() {
  const [activeTab, setActiveTab] = useState('projects');
  const [currentProject, setCurrentProject] = useState(null); // Track active project

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-blue-800 text-white p-4">
        <h1 className="text-2xl font-semibold">Code + AI Demo</h1>
      </header>

      <div className="flex justify-center bg-gray-200 p-2">
        <button
          className={`mx-2 px-4 py-2 rounded ${
            activeTab === 'projects' ? 'bg-blue-600 text-white' : 'bg-white text-black'
          }`}
          onClick={() => setActiveTab('projects')}
        >
          Projects
        </button>
        <button
          className={`mx-2 px-4 py-2 rounded ${
            activeTab === 'analyze' ? 'bg-blue-600 text-white' : 'bg-white text-black'
          }`}
          onClick={() => setActiveTab('analyze')}
          disabled={!currentProject}
        >
          Code Analyze
        </button>
        <button
          className={`mx-2 px-4 py-2 rounded ${
            activeTab === 'query' ? 'bg-blue-600 text-white' : 'bg-white text-black'
          }`}
          onClick={() => setActiveTab('query')}
          disabled={!currentProject}
        >
          AI Query
        </button>
        <button
          className={`mx-2 px-4 py-2 rounded ${
            activeTab === 'history' ? 'bg-blue-600 text-white' : 'bg-white text-black'
          }`}
          onClick={() => setActiveTab('history')}
          disabled={!currentProject}
        >
          Query History
        </button>
      </div>

      {/* Display current project info */}
      <div className="text-center bg-gray-100 p-2">
        {currentProject ? (
          <p className="text-sm text-gray-700">Current Project: <strong>{currentProject}</strong></p>
        ) : (
          <p className="text-red-500">No project loaded</p>
        )}
      </div>

      <main className="flex-grow p-4">
        {activeTab === 'projects' && <Projects setCurrentProject={setCurrentProject} />}
        {activeTab === 'analyze' && currentProject && <CodeAnalyze project={currentProject} />}
        {activeTab === 'query' && currentProject && <AIQuery project={currentProject} />}
        {activeTab === 'history' && currentProject && <QueryHistory project={currentProject} />}
      </main>

      <footer className="bg-gray-300 text-center py-2">
        <p className="text-sm">© 2025 AI Caller Demo</p>
      </footer>
    </div>
  );
}

export default App;

