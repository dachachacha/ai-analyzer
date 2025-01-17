import React, { useEffect, useState, useCallback } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { solarizedlight } from 'react-syntax-highlighter/dist/esm/styles/prism';

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
  }, [project]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const renderCodeBlock = ({ language, value }) => (
    <div className="relative">
      <SyntaxHighlighter language={language} style={solarizedlight}>
        {value}
      </SyntaxHighlighter>
      <button
        onClick={() => navigator.clipboard.writeText(value)}
        className="absolute top-2 right-2 bg-blue-500 text-white px-2 py-1 text-sm rounded hover:bg-blue-600"
        title="Copy to Clipboard"
      >
        Copy
      </button>
    </div>
  );

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
              <div className="bg-gray-200 p-2 rounded mb-2">
                <span className="font-semibold">Query:</span>
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        renderCodeBlock({ language: match[1], value: String(children).replace(/\n$/, '') })
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {entry.query}
                </ReactMarkdown>
              </div>
              <div className="bg-white p-2 rounded">
                <span className="font-semibold">Answer:</span>
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      return !inline && match ? (
                        renderCodeBlock({ language: match[1], value: String(children).replace(/\n$/, '') })
                      ) : (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {entry.answer}
                </ReactMarkdown>
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
