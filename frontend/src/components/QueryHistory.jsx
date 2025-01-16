import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';

function QueryHistory({ project }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const logEvent = (message, data = null) => {
    if (data) {
      console.log(`[QueryHistory] ${message}`, data);
    } else {
      console.log(`[QueryHistory] ${message}`);
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

  // Memoized fetchHistory function to prevent recreation
  const fetchHistory = useCallback(async () => {
    if (!project) {
      setNotification({ type: 'error', message: 'No project loaded.' });
      return;
    }

    logEvent('fetchHistory invoked');
    setLoading(true);
    setNotification({ type: 'info', message: 'Fetching query history. Please wait...' });

    try {
      const response = await axios.get(`${process.env.REACT_APP_API_BASE_URL}/history`, {
        params: { project },
      });
      logEvent('Received history data', { response: response.data });
      setHistory(response.data || []);
      setNotification({ type: 'success', message: 'Query history loaded successfully.' });
    } catch (err) {
      logEvent('Error fetching query history', { error: err });
      console.error('[QueryHistory] Error fetching history:', err);
      setNotification({ type: 'error', message: 'Failed to load query history. Please try again.' });
    } finally {
      setLoading(false);
      logEvent('fetchHistory completed', { loading: false });
    }
  }, [project]); // Memoized with project as dependency

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]); // No project needed, as it's already a dependency of fetchHistory

  return (
    <div className="max-w-3xl mx-auto">
      <h2 className="text-xl font-bold mb-4">Query History</h2>

      {renderNotification()}

      <div className="mb-4 flex justify-between items-center">
        <button
          onClick={fetchHistory}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors duration-200"
          disabled={loading}
        >
          {loading ? 'Refreshing...' : 'Refresh History'}
        </button>
      </div>

      {loading && !history.length ? (
        <p>Loading query history...</p>
      ) : history.length === 0 ? (
        <p className="text-gray-500">No queries found.</p>
      ) : (
        <div className="space-y-4">
          {history.map((entry, index) => (
            <div
              key={index}
              className="border rounded p-4 bg-gray-100 shadow-sm hover:shadow-md transition-shadow"
            >
              <p>
                <span className="font-semibold">Query:</span> {entry.query}
              </p>
              <div>
                <span className="font-semibold">Answer:</span>
                <ReactMarkdown className="mt-2 prose prose-sm">{entry.answer}</ReactMarkdown>
              </div>
              <p className="text-sm text-gray-500">
                <span className="font-semibold">Timestamp:</span>{' '}
                {new Date(entry.timestamp).toLocaleString()}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default QueryHistory;

