// src/App.jsx
import React, { useState } from 'react';
import CodeAnalyze from './components/CodeAnalyze';
import AIQuery from './components/AIQuery';
import QueryHistory from './components/QueryHistory';
import Projects from './components/Projects';
import ChunkedFiles from './components/ChunkedFiles';
import Settings from './components/Settings';

function App() {
  const [activeTab, setActiveTab] = useState('projects');
  const [currentProject, setCurrentProject] = useState(null); // Track active project
  const [settings, setSettings] = useState({
    // Provide default values for your settings here:
    querySettings: { nbChunksUsedForQuery: 10 },
    historySummarizerSettings: {
      nbLiteralItems: 2,
      maxTotalHistoryItems: 10,
    },
  });

  // This function updates the settings state with the values provided by Settings.jsx
  const handleSettingsSave = (newSettings) => {
    setSettings(newSettings);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-blue-800 text-white p-4">
        <h1 className="text-2xl font-semibold">Code + AI Demo</h1>
      </header>

      <div className="flex justify-center bg-gray-200 p-2">
        <button
          className={`mx-2 px-4 py-2 rounded ${
            activeTab === 'settings' ? 'bg-blue-600 text-white' : 'bg-white text-black'
          }`}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
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
        <button
          className={`mx-2 px-4 py-2 rounded ${
            activeTab === 'chunked_files' ? 'bg-blue-600 text-white' : 'bg-white text-black'
          }`}
          onClick={() => setActiveTab('chunked_files')}
          disabled={!currentProject}
        >
          Chunked Files
        </button>
      </div>

      {/* Enhanced current project display */}
      <div className="bg-gray-100 p-4 my-4 mx-auto max-w-3xl rounded shadow flex items-center justify-center">
        {currentProject ? (
          <div className="flex items-center space-x-2">
            <span className="text-base font-bold text-blue-800">Current Project:</span>
            <span className="text-base font-extrabold text-blue-900 bg-blue-200 px-3 py-1 rounded">
              {currentProject}
            </span>
          </div>
        ) : (
          <p className="text-lg font-semibold text-red-500">No project loaded</p>
        )}
      </div>

      <main className="flex-grow p-4">
        {activeTab === 'settings' && <Settings onSave={handleSettingsSave} />}
        {activeTab === 'projects' && <Projects setCurrentProject={setCurrentProject} />}
        {activeTab === 'analyze' && currentProject && <CodeAnalyze project={currentProject} />}
        {activeTab === 'query' && currentProject && (
          <AIQuery project={currentProject} settings={settings} />
        )}
        {activeTab === 'history' && currentProject && <QueryHistory project={currentProject} />}
        {activeTab === 'chunked_files' && currentProject && <ChunkedFiles project={currentProject} />}
      </main>

      <footer className="bg-gray-300 text-center py-2">
        <p className="text-sm">© 2025 AI Caller Demo</p>
      </footer>
    </div>
  );
}

export default App;

