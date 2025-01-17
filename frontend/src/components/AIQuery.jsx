import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { solarizedlight } from 'react-syntax-highlighter/dist/esm/styles/prism';

function AIQuery({ project, settings }) {
  const [query, setQuery] = useState(() => localStorage.getItem('query') || '');
  const [answer, setAnswer] = useState(() => localStorage.getItem('answer') || '');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  const answerRef = useRef(null);

  const logEvent = (message, data = null) => {
    if (data) {
      console.log(`[AIQuery] ${message}`, data);
    } else {
      console.log(`[AIQuery] ${message}`);
    }
  };

  useEffect(() => {
    localStorage.setItem('query', query);
  }, [query]);

  useEffect(() => {
    localStorage.setItem('answer', answer);
    if (answer && answerRef.current) {
      answerRef.current.scrollIntoView({ behavior: 'smooth' });
    }
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
      logEvent('Sending API request', { query, settings });

      const response = await axios.post(`${process.env.REACT_APP_API_BASE_URL}/query`, { 
        project,
        query,
        settings,
      });

      logEvent('Received API response', { response: response.data });
      setAnswer(response.data.answer);
      setNotification({ 
        type: 'success', 
        message: `Query successful! Tokens submitted: ${response.data.tokens_submitted}, Tokens returned: ${response.data.tokens_returned}` 
      });
    } catch (err) {
      logEvent('Error during API request', { error: err });
      console.error('[AIQuery] Error querying AI:', err);
      setAnswer('Error querying AI.');
      setNotification({ type: 'error', message: 'Error querying AI. Please try again.' });
    } finally {
      setLoading(false);
      setQuery('');
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
    <div className="p-4 bg-white rounded shadow-md max-w-3xl mx-auto">
      <h2 className="text-xl font-bold mb-4">AI Query</h2>

      {renderNotification()}

      <div className="mb-4">
        <label className="block mb-2 text-gray-700">Enter your question</label>
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="border rounded p-2 w-full h-48 resize"
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
        <div ref={answerRef} className="mt-6 p-6 border rounded bg-gray-50 shadow relative">
          <h3 className="font-semibold text-xl mb-4 border-b pb-2">Answer:</h3>
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
            {answer}
          </ReactMarkdown>
        </div>
      )}
    </div>
  );
}

export default AIQuery;
