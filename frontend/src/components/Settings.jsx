// src/components/Settings.jsx

import React, { useState, useEffect } from 'react';

function Settings({ onSave }) {
  const [querySettings, setQuerySettings] = useState({
    nbChunksUsedForQuery: 10, // Default value
  });

  const [historySummarizerSettings, setHistorySummarizerSettings] = useState({
    nbLiteralItems: 2, // Default value
    maxTotalHistoryItems: 10, // Default value
  });

  useEffect(() => {
    // Load settings from localStorage or use defaults
    const savedQuerySettings = JSON.parse(localStorage.getItem('querySettings'));
    const savedHistorySettings = JSON.parse(localStorage.getItem('historySummarizerSettings'));

    if (savedQuerySettings) setQuerySettings(savedQuerySettings);
    if (savedHistorySettings) setHistorySummarizerSettings(savedHistorySettings);
  }, []);

  const handleSave = () => {
    localStorage.setItem('querySettings', JSON.stringify(querySettings));
    localStorage.setItem('historySummarizerSettings', JSON.stringify(historySummarizerSettings));
    onSave({ querySettings, historySummarizerSettings });
  };

  return (
    <div className="p-4 bg-white rounded shadow-md max-w-3xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Settings</h2>

      <div className="mb-4">
        <label className="block mb-2 text-gray-700">Number of Chunks Used for Query</label>
        <input
          type="number"
          value={querySettings.nbChunksUsedForQuery}
          onChange={(e) => setQuerySettings({ ...querySettings, nbChunksUsedForQuery: e.target.value })}
          className="border rounded p-2 w-full"
        />
      </div>

      <div className="mb-4">
        <label className="block mb-2 text-gray-700">Number of Literal History Items</label>
        <input
          type="number"
          value={historySummarizerSettings.nbLiteralItems}
          onChange={(e) => setHistorySummarizerSettings({ ...historySummarizerSettings, nbLiteralItems: e.target.value })}
          className="border rounded p-2 w-full"
        />
      </div>

      <div className="mb-4">
        <label className="block mb-2 text-gray-700">Max total of History Items to Summarize</label>
        <input
          type="number"
          value={historySummarizerSettings.maxTotalHistoryItems}
          onChange={(e) => setHistorySummarizerSettings({ ...historySummarizerSettings, maxTotalHistoryItems: e.target.value })}
          className="border rounded p-2 w-full"
        />
      </div>

      <button
        onClick={handleSave}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Save Settings
      </button>
    </div>
  );
}
export default Settings;
