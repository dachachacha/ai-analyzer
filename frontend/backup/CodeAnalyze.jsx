import React, { useState } from 'react';
import axios from 'axios';
import { ClipLoader } from 'react-spinners'; // Import spinner

function CodeAnalyze({ project }) {
  //const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [chunkedFiles, setChunkedFiles] = useState([]);
  const [ignoredFiles, setIgnoredFiles] = useState([]);
  const [notification, setNotification] = useState(null); // Notification state

  // Function to handle logging (centralized logging)
  const logEvent = (message, data = null) => {
    if (data) {
      console.log(`[CodeAnalyze] ${message}`, data);
    } else {
      console.log(`[CodeAnalyze] ${message}`);
    }
  };

  const handleAnalyze = async () => {
    logEvent('handleAnalyze invoked');
    if (!project) {
      setNotification({ type: 'error', message: 'No project loaded.' });
      return;
    }

    try {
      setLoading(true);
      setError('');
      setNotification({ type: 'info', message: 'Analyzing code. Please wait...' });
      logEvent('Sending analyze API request');

      const response = await axios.post(`${process.env.REACT_APP_API_BASE_URL}/analyze`, {
        project,
        folderPath: null, // Explicitly send null or an empty string
      });

      logEvent('Received analyze API response', { response: response.data });
      setChunkedFiles(response.data.chunked);
      setIgnoredFiles(response.data.ignored);
      setNotification({ type: 'success', message: 'Analysis completed successfully.' });
    } catch (err) {
      logEvent('Error during analyze API request', { error: err });
      console.error('[CodeAnalyze] Error analyzing code:', err);

      const errorMessage =
        err.response?.data?.message || err.response?.statusText || 'An unknown error occurred.';
      setNotification({ type: 'error', message: errorMessage });
    } finally {
      setLoading(false);
      logEvent('handleAnalyze completed', { loading: false });
    }
  };

  const handleFlush = async () => {
    logEvent('handleFlush invoked');

    try {
      setLoading(true);
      setError('');
      setNotification({ type: 'info', message: 'Flushing the database...' });
      logEvent('Sending flush API request');

      const response = await axios.post(`${process.env.REACT_APP_API_BASE_URL}/flush`);

      logEvent('Received flush API response', { response: response.data });
      setNotification({ type: 'success', message: `Flushed: ${response.data.message}` });
    } catch (err) {
      logEvent('Error during flush API request', { error: err });
      console.error('[CodeAnalyze] Error flushing database:', err);

      const errorMessage =
        err.response?.data?.message || err.response?.statusText || 'An unknown error occurred.';
      setNotification({ type: 'error', message: errorMessage });
    } finally {
      setLoading(false);
      logEvent('handleFlush completed', { loading: false });
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
    <div className="p-6 bg-white rounded-lg shadow-md max-w-xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Code Analyze for {project}</h2>

      {/* Notification Display */}
      {renderNotification()}

      {/* Action Buttons */}
      <div className="flex space-x-4 mb-4">
        <button
          onClick={handleAnalyze}
          className={`bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition-colors duration-200 flex items-center ${
            loading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          disabled={loading}
        >
          {loading ? (
            <>
              <ClipLoader size={20} color="#ffffff" />
              <span className="ml-2">Analyzing...</span>
            </>
          ) : (
            'Analyze & Store'
          )}
        </button>

        <button
          onClick={handleFlush}
          className={`bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors duration-200 flex items-center ${
            loading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          disabled={loading}
        >
          {loading ? (
            <>
              <ClipLoader size={20} color="#ffffff" />
              <span className="ml-2">Flushing...</span>
            </>
          ) : (
            'Flush hashes and embeddings'
          )}
        </button>
      </div>

      {/* Chunked Files Display */}
      <div className="mt-4">
        <h3 className="text-lg font-semibold mb-2">Chunked Files</h3>
        <textarea
          readOnly
          value={chunkedFiles.join('\n')}
          className="w-full p-2 border rounded h-32 bg-gray-100"
        />
      </div>

      {/* Ignored Files Display */}
      <div className="mt-4">
        <h3 className="text-lg font-semibold mb-2">Ignored Files</h3>
        <textarea
          readOnly
          value={ignoredFiles.join('\n')}
          className="w-full p-2 border rounded h-32 bg-gray-100"
        />
      </div>
    </div>
  );
}

export default CodeAnalyze;

