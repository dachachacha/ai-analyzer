import React, { useState, useEffect } from 'react';
import axios from 'axios';

function AIQuery({ project }) {
  // Initialize states with values from localStorage
  const [query, setQuery] = useState(() => localStorage.getItem('query') || '');
  const [answer, setAnswer] = useState(() => localStorage.getItem('answer') || '');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const logEvent = (message, data = null) => {
    if (data) {
      console.log(`[AIQuery] ${message}`, data);
    } else {
      console.log(`[AIQuery] ${message}`);
    }
  };

  // Save query and answer to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem('query', query);
  }, [query]);

  useEffect(() => {
    localStorage.setItem('answer', answer);
  }, [answer]);

  const handleQuery = async () => {
    logEvent('handleQuery invoked');
    if (!project) {
      setNotification({ type: 'error', message: 'No project loaded.' });
      return;
    }

    if (!query.trim()) {
      logEvent('Empty query submitted');
      setNotification({ type: 'error', message: 'Please enter a valid query.' });
      return;
    }

    try {
      setLoading(true);
      setAnswer('Querying AI. Please wait...');
      setNotification({ type: 'info', message: 'Querying AI. Please wait...' });
      logEvent('Sending API request', { query });

      const response = await axios.post(`${process.env.REACT_APP_API_BASE_URL}/query`, { 
        project,
        query,
      });

      logEvent('Received API response', { response: response.data });
      setAnswer(response.data.answer);
      setNotification({ type: 'success', message: 'Query successful!' });
    } catch (err) {
      logEvent('Error during API request', { error: err });
      console.error('[AIQuery] Error querying AI:', err);
      setAnswer('Error querying AI.');
      setNotification({ type: 'error', message: 'Error querying AI. Please try again.' });
    } finally {
      setLoading(false);
      setQuery(''); // Flush the textbox after the query is done
      logEvent('handleQuery completed', { loading: false });
    }
  };

  const renderNotification = () => {
    if (!notification) return null;

    const notificationStyles = {
      info: 'bg-blue-100 text-blue-700 border-blue-500',
      success: 'bg-green-100 text-green-700 border-green-500',
      error: 'bg-red-100 text-red-700 border-red-500',
    };

    const style = notificationStyles[notification.type] || 'bg-gray-100 text-gray-700 border-gray-500';

    return (
      <div className={`p-3 border-l-4 rounded mb-4 ${style}`}>
        {notification.message}
      </div>
    );
  };

  return (
    <div className="p-4 bg-white rounded shadow-md max-w-3xl mx-auto">
      <h2 className="text-xl font-bold mb-4">AI Query</h2>

      {renderNotification()}

      <div className="mb-4">
        <label className="block mb-2 text-gray-700">Enter your question</label>
        <textarea
          value={query}
          onChange={(e) => {
            setQuery(e.target.value); // Removed logEvent for input change
          }}
          className="border rounded p-2 w-full h-48 resize" // Larger text area with full width and adjustable height
          placeholder="Ask something about your code..."
        />
      </div>
      <button
        onClick={handleQuery}
        className={`bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
        disabled={loading}
      >
        {loading ? 'Querying...' : 'Query AI'}
      </button>

      {answer && (
        <div className="mt-4 p-4 border rounded bg-gray-100 relative">
          <h3 className="font-semibold text-lg mb-2">Answer:</h3>
          <div className="whitespace-pre-wrap text-gray-800 text-sm max-h-64 overflow-y-auto">
            {answer}
          </div>
          <button
            onClick={() => navigator.clipboard.writeText(answer)}
            className="absolute top-4 right-4 bg-blue-500 text-white px-2 py-1 text-sm rounded hover:bg-blue-600"
            title="Copy to Clipboard"
          >
            Copy
          </button>
        </div>
      )}
    </div>
  );
}

export default AIQuery;
